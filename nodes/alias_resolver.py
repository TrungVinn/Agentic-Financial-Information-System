from typing import Dict, Any
from nodes.utils import extract_ticker

def resolve_alias(state: Dict[str, Any]) -> Dict[str, Any]:
    ticker = extract_ticker(state.get("question", ""))
    return {**state, "ticker": ticker}


