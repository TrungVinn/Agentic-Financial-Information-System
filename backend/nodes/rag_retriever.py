"""
RAG Retriever Node - Xử lý câu hỏi kiến thức tổng quát với PDF retrieval.

Module này xử lý các câu hỏi KHÔNG cần SQL:
1. Load và index PDF documents vào ChromaDB
2. Retrieve relevant chunks bằng semantic search
3. Trả lời bằng LLM với context từ documents

Dependencies:
- chromadb: Vector database
- sentence-transformers: Embedding model
- pypdf: PDF parsing
- langchain-text-splitters: Text chunking
"""

import os
import re
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as google_genai

# Load environment
load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# ========== CONFIGURATION ==========
# Đường dẫn tới thư mục chứa PDF documents
DOCUMENTS_DIR = Path(__file__).parent.parent / "data" / "documents"
# Đường dẫn lưu ChromaDB
CHROMA_PERSIST_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
# Collection name trong ChromaDB
COLLECTION_NAME = "djia_documents"
# Chunk size và overlap cho text splitting
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_chroma_client():
    """
    Khởi tạo ChromaDB client với persistent storage.
    """
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Tạo thư mục nếu chưa có
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        return client
    except ImportError:
        print("ChromaDB not installed. Run: pip install chromadb")
        return None


def get_embedding_function():
    """
    Lấy embedding function sử dụng sentence-transformers.
    Model: all-MiniLM-L6-v2 (nhẹ, nhanh, hiệu quả)
    """
    try:
        from chromadb.utils import embedding_functions
        
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    except ImportError:
        print("sentence-transformers not installed. Run: pip install sentence-transformers")
        return None


def load_pdf(file_path: Path) -> str:
    """
    Load và extract text từ PDF file.
    
    Args:
        file_path: Đường dẫn tới file PDF
        
    Returns:
        Text content của PDF
    """
    try:
        from pypdf import PdfReader
        
        reader = PdfReader(str(file_path))
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    except ImportError:
        print("pypdf not installed. Run: pip install pypdf")
        return ""
    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
        return ""


def split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text thành các chunks nhỏ hơn để indexing.
    
    Args:
        text: Text cần split
        chunk_size: Kích thước mỗi chunk (characters)
        chunk_overlap: Độ overlap giữa các chunks
        
    Returns:
        List các text chunks
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        
        chunks = splitter.split_text(text)
        return chunks
    except ImportError:
        # Fallback: simple splitting
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks


def compute_file_hash(file_path: Path) -> str:
    """Tính MD5 hash của file để detect changes."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def index_documents(force_reindex: bool = False) -> bool:
    """
    Index tất cả PDF documents trong thư mục vào ChromaDB.
    
    Args:
        force_reindex: True để reindex toàn bộ, bỏ qua cache
        
    Returns:
        True nếu có documents được index
    """
    client = get_chroma_client()
    if not client:
        return False
    
    embedding_fn = get_embedding_function()
    if not embedding_fn:
        return False
    
    # Get or create collection
    try:
        if force_reindex:
            # Xóa collection cũ nếu force reindex
            try:
                client.delete_collection(COLLECTION_NAME)
            except:
                pass
        
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(f"Error creating collection: {e}")
        return False
    
    # Tìm tất cả PDF files
    if not DOCUMENTS_DIR.exists():
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created documents directory: {DOCUMENTS_DIR}")
        return False
    
    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {DOCUMENTS_DIR}")
        return False
    
    # Index từng file
    indexed_count = 0
    for pdf_path in pdf_files:
        file_hash = compute_file_hash(pdf_path)
        doc_id_prefix = f"{pdf_path.stem}_{file_hash[:8]}"
        
        # Check if already indexed (by checking if any document with this prefix exists)
        existing = collection.get(where={"source": str(pdf_path.name)})
        if existing and existing["ids"] and not force_reindex:
            # Check hash to see if file changed
            existing_hash = existing["metadatas"][0].get("file_hash", "") if existing["metadatas"] else ""
            if existing_hash == file_hash:
                print(f"Skipping {pdf_path.name} (already indexed)")
                continue
            else:
                # File changed, delete old entries
                collection.delete(where={"source": str(pdf_path.name)})
        
        print(f"Indexing {pdf_path.name}...")
        
        # Load và split PDF
        text = load_pdf(pdf_path)
        if not text:
            print(f"  Warning: No text extracted from {pdf_path.name}")
            continue
        
        chunks = split_text(text)
        print(f"  Split into {len(chunks)} chunks")
        
        # Add to collection
        ids = [f"{doc_id_prefix}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": str(pdf_path.name),
                "file_hash": file_hash,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]
        
        # Add in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            collection.add(
                ids=ids[i:batch_end],
                documents=chunks[i:batch_end],
                metadatas=metadatas[i:batch_end],
            )
        
        indexed_count += 1
        print(f"  ✓ Indexed {len(chunks)} chunks from {pdf_path.name}")
    
    print(f"\nTotal: Indexed {indexed_count} documents, Collection size: {collection.count()}")
    return indexed_count > 0 or collection.count() > 0


def retrieve_from_db(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks từ ChromaDB.
    
    Args:
        query: Câu hỏi cần tìm context
        top_k: Số lượng chunks trả về
        
    Returns:
        List các documents với metadata
    """
    client = get_chroma_client()
    if not client:
        return []
    
    embedding_fn = get_embedding_function()
    if not embedding_fn:
        return []
    
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        
        if collection.count() == 0:
            print("Warning: ChromaDB collection is empty. Run index_documents() first.")
            return []
        
        # Query với semantic search
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        documents = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                
                documents.append({
                    "content": doc,
                    "source": metadata.get("source", "unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "distance": distance,  # Lower = more similar (cosine distance)
                    "relevance_score": 1 - distance,  # Convert to similarity score
                })
        
        return documents
    
    except Exception as e:
        print(f"Error retrieving from ChromaDB: {e}")
        return []


def detect_general_question(question: str) -> bool:
    """
    Phát hiện xem câu hỏi có liên quan đến kiến thức trong PDF documents không.
    
    Sử dụng LLM để phân tích câu hỏi và xác định:
    - Nếu câu hỏi liên quan đến kiến thức tổng quát, khái niệm, giải thích có thể tìm trong PDF → True
    - Nếu câu hỏi yêu cầu dữ liệu cụ thể từ database (giá, volume, số liệu) → False
    
    Returns:
        True nếu câu hỏi liên quan đến PDF documents và nên dùng RAG
        False nếu câu hỏi cần truy vấn SQL database
    """
    if not question or not question.strip():
        return False
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Fallback: nếu không có API key, trả về False để dùng SQL pipeline
        print("Warning: No Gemini API key found. Skipping RAG detection.")
        return False
    
    try:
        google_genai.configure(api_key=api_key)
        
        # Prompt để LLM phân tích câu hỏi
        prompt = f"""Bạn là một chuyên gia phân tích câu hỏi cho hệ thống tài chính.

Hệ thống có 2 nguồn thông tin:
1. PDF Documents: Chứa kiến thức tổng quát về thị trường chứng khoán, DJIA, khái niệm, giải thích, định nghĩa
2. SQL Database: Chứa dữ liệu cụ thể về giá cổ phiếu, volume, ngày tháng cụ thể của các công ty

CÂU HỎI: {question}

NHIỆM VỤ: Xác định xem câu hỏi này có liên quan đến kiến thức trong PDF documents không.

QUY TẮC:
- Trả về TRUE nếu câu hỏi hỏi về: khái niệm, định nghĩa, giải thích, kiến thức tổng quát, lý thuyết, cách thức hoạt động
  Ví dụ: "What is DJIA?", "Giải thích về thị trường chứng khoán", "How does stock market work?"
  
- Trả về FALSE nếu câu hỏi yêu cầu: dữ liệu cụ thể, số liệu, giá cả, volume, so sánh số liệu, biểu đồ dữ liệu
  Ví dụ: "What was the price of Apple on 2024-01-15?", "Plot the volume", "Compare prices of AAPL and MSFT"

CHỈ TRẢ LỜI: TRUE hoặc FALSE (không có dấu chấm, không có giải thích thêm)"""

        model = google_genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        result = (response.text or "").strip().upper()
        
        # Parse kết quả
        if "TRUE" in result:
            return True
        elif "FALSE" in result:
            return False
        else:
            # Nếu LLM trả về format không chuẩn, mặc định là False
            print(f"Warning: LLM returned unexpected format: {result}. Defaulting to False.")
            return False
            
    except Exception as e:
        print(f"Error in detect_general_question with LLM: {e}")
        # Fallback: nếu có lỗi, trả về False để dùng SQL pipeline
        return False


def answer_with_context(question: str, context_docs: List[Dict[str, Any]]) -> str:
    """
    Trả lời câu hỏi sử dụng LLM với context từ RAG.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Không thể kết nối với LLM. Vui lòng kiểm tra API key."
    
    google_genai.configure(api_key=api_key)
    
    # Build context string với source attribution
    if context_docs:
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            source = doc.get("source", "unknown")
            content = doc.get("content", "")
            relevance = doc.get("relevance_score", 0)
            context_parts.append(
                f"[Document {i}] (Source: {source}, Relevance: {relevance:.2f})\n{content}"
            )
        context_text = "\n\n---\n\n".join(context_parts)
    else:
        context_text = "Không tìm thấy context phù hợp trong knowledge base."
    
    # Detect language
    vietnamese_chars = re.findall(
        r'[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]', 
        question.lower()
    )
    is_vietnamese = len(vietnamese_chars) > 0
    
    system_prompt = f"""Bạn là trợ lý AI chuyên về thị trường chứng khoán và DJIA (Dow Jones Industrial Average).

RETRIEVED CONTEXT FROM DOCUMENTS:
{context_text}

YÊU CẦU:
- Trả lời dựa trên context được cung cấp từ documents
- Nếu context không đủ thông tin, hãy nói rõ và cung cấp kiến thức chung
- {'Trả lời bằng tiếng Việt' if is_vietnamese else 'Answer in English'}
- Giữ câu trả lời ngắn gọn, rõ ràng, dễ hiểu
- Cite source documents khi có thể (ví dụ: "Theo tài liệu X...")
- Nếu câu hỏi về giá cụ thể của một cổ phiếu tại thời điểm nào đó, hãy hướng dẫn người dùng hỏi lại với format phù hợp"""

    prompt = f"{system_prompt}\n\nCâu hỏi: {question}\n\nTrả lời:"
    
    try:
        model = google_genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        answer = (response.text or "").strip()
        return answer if answer else "Không thể tạo câu trả lời."
    except Exception as e:
        return f"Lỗi khi gọi LLM: {str(e)}"


def rag_retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: RAG Retriever - Tìm kiếm thông tin từ PDF documents.
    
    Node này được gọi khi câu hỏi KHÔNG liên quan SQL (đã được phân loại bởi question_classifier).
    - Tìm kiếm thông tin liên quan từ PDF documents
    - Nếu có thông tin phù hợp: Trả về context để gửi cho answer_summarizer
    - Nếu không có: Trả về flag không có thông tin trong PDF
    
    Args:
        state: Dictionary chứa workflow state, cần có key "question"
        
    Returns:
        State mới với các key:
        - has_rag_context: Boolean - Có thông tin liên quan trong PDF không
        - rag_context: List documents retrieved (nếu có)
    """
    question = state.get("question", "")
    
    # Đảm bảo documents đã được index
    index_documents(force_reindex=False)
    
    # Retrieve context từ ChromaDB
    context_docs = retrieve_from_db(question, top_k=5)
    
    if not context_docs:
        # Không có documents trong knowledge base
        return {
            **state,
            "has_rag_context": False,
            "rag_context": [],
        }
    
    # Kiểm tra relevance score của documents
    # Nếu tất cả documents có relevance score thấp (< 0.3), coi như không phù hợp
    min_relevance = 0.3
    relevant_docs = [doc for doc in context_docs if doc.get("relevance_score", 0) >= min_relevance]
    
    if not relevant_docs:
        # Documents không phù hợp với câu hỏi
        return {
            **state,
            "has_rag_context": False,
            "rag_context": [],
        }
    
    # Có documents phù hợp, trả về context để answer_summarizer xử lý
    return {
        **state,
        "has_rag_context": True,
        "rag_context": relevant_docs,
    }


# ========== UTILITY FUNCTIONS ==========

def reindex_all():
    """
    Force reindex tất cả documents.
    Gọi hàm này khi có PDF mới hoặc cần rebuild index.
    
    Usage:
        from nodes.rag_retriever import reindex_all
        reindex_all()
    """
    print("Force reindexing all documents...")
    index_documents(force_reindex=True)


def get_collection_info() -> Dict[str, Any]:
    """
    Lấy thông tin về ChromaDB collection.
    
    Returns:
        Dictionary chứa thông tin collection
    """
    client = get_chroma_client()
    if not client:
        return {"error": "ChromaDB not available"}
    
    try:
        embedding_fn = get_embedding_function()
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
        
        # Get sample of documents
        sample = collection.peek(limit=3)
        
        return {
            "name": COLLECTION_NAME,
            "count": collection.count(),
            "sample_sources": list(set(
                m.get("source", "unknown") 
                for m in sample.get("metadatas", [])
            )) if sample.get("metadatas") else [],
        }
    except Exception as e:
        return {"error": str(e)}


def test_retrieval(query: str, top_k: int = 3):
    """
    Test retrieval với một query.
    
    Usage:
        from nodes.rag_retriever import test_retrieval
        test_retrieval("What is DJIA?")
    """
    print(f"\n🔍 Query: {query}")
    print("-" * 50)
    
    results = retrieve_from_db(query, top_k)
    
    if not results:
        print("No results found. Make sure documents are indexed.")
        return
    
    for i, doc in enumerate(results, 1):
        print(f"\n📄 Result {i}:")
        print(f"   Source: {doc['source']}")
        print(f"   Relevance: {doc['relevance_score']:.3f}")
        print(f"   Content: {doc['content'][:200]}...")


if __name__ == "__main__":
    # Test script
    print("=" * 60)
    print("RAG Retriever - PDF Document Search")
    print("=" * 60)
    
    # Index documents
    print("\n📚 Indexing documents...")
    index_documents()
    
    # Show collection info
    print("\n📊 Collection info:")
    info = get_collection_info()
    print(f"   Documents: {info.get('count', 0)}")
    print(f"   Sources: {info.get('sample_sources', [])}")
    
    # Test query
    test_retrieval("What is DJIA?")
