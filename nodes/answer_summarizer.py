from typing import Dict, Any
import pandas as pd

def derive_answer(df: pd.DataFrame) -> str:
    if df.empty:
        return "Không có dữ liệu phù hợp."
    # Lấy ô đầu tiên nếu có cột duy nhất
    if df.shape[1] == 1:
        val = df.iloc[0, 0]
        if isinstance(val, (int, float)):
            return f"{val}"
        return str(val)
    # Nếu có cột close/volume hay max_close...
    for col in ["close", "open", "high", "low", "volume", "max_close", "min_close", "avg_close", "median_close", "a_close", "b_close"]:
        if col in df.columns:
            return str(df[col].iloc[0])
    # Fallback
    return str(df.iloc[0].to_dict())


def summarize_answer(state: Dict[str, Any]) -> Dict[str, Any]:
    df = state.get("df")
    answer = derive_answer(df) if df is not None else "Không có dữ liệu phù hợp."
    return {**state, "answer": answer}


