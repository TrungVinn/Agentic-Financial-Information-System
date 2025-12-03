#!/usr/bin/env python3
"""
Script để index PDF documents vào ChromaDB.

Usage:
    cd backend
    python scripts/index_documents.py              # Index documents mới
    python scripts/index_documents.py --force      # Force reindex tất cả
    python scripts/index_documents.py --info       # Hiển thị thông tin collection
    python scripts/index_documents.py --test "What is DJIA?"  # Test retrieval
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path để import nodes
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.rag_retriever import (
    index_documents,
    reindex_all,
    get_collection_info,
    test_retrieval,
    retrieve_from_db,
    DOCUMENTS_DIR,
)


def main():
    parser = argparse.ArgumentParser(
        description="Index PDF documents vào ChromaDB cho RAG"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force reindex tất cả documents (xóa index cũ)"
    )
    parser.add_argument(
        "--info", "-i",
        action="store_true", 
        help="Hiển thị thông tin về collection"
    )
    parser.add_argument(
        "--test", "-t",
        type=str,
        metavar="QUERY",
        help="Test retrieval với một query"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List tất cả PDF files trong thư mục documents"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📚 RAG Document Indexer")
    print("=" * 60)
    print(f"\nDocuments directory: {DOCUMENTS_DIR}")
    
    # List files
    if args.list:
        print("\n📁 PDF files in documents folder:")
        pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))
        if pdf_files:
            for f in pdf_files:
                size_kb = f.stat().st_size / 1024
                print(f"   - {f.name} ({size_kb:.1f} KB)")
        else:
            print("   (No PDF files found)")
        return
    
    # Show info
    if args.info:
        print("\n📊 Collection Info:")
        info = get_collection_info()
        if "error" in info:
            print(f"   Error: {info['error']}")
        else:
            print(f"   Collection: {info['name']}")
            print(f"   Total chunks: {info['count']}")
            print(f"   Sources: {', '.join(info['sample_sources']) if info['sample_sources'] else 'None'}")
        return
    
    # Test retrieval
    if args.test:
        test_retrieval(args.test, top_k=3)
        return
    
    # Index documents
    print("\n🔄 Indexing documents...")
    
    if args.force:
        print("   Mode: Force reindex (deleting old index)")
        reindex_all()
    else:
        print("   Mode: Incremental (only new/changed files)")
        success = index_documents(force_reindex=False)
        
        if not success:
            print("\n⚠️  No documents indexed.")
            print(f"   Please add PDF files to: {DOCUMENTS_DIR}")
            print("\n   Example:")
            print("   1. Copy your PDF files to the documents folder")
            print("   2. Run this script again")
    
    # Show final info
    print("\n📊 Final Collection Info:")
    info = get_collection_info()
    if "error" not in info:
        print(f"   Total chunks: {info['count']}")
        print(f"   Sources: {', '.join(info['sample_sources']) if info['sample_sources'] else 'None'}")


if __name__ == "__main__":
    main()

