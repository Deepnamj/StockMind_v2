from langchain_core.tools import tool
from langgraph.types import interrupt

@tool
def request_simulated_stock_purchase(symbol: str, quantity: int, estimated_price: float) -> str:
    """Request human approval for a simulated stock purchase. This never places a real trade."""
    if not symbol or quantity <= 0 or estimated_price < 0:
        return "Invalid purchase details. Please provide a symbol, positive quantity and non-negative price."

    total = quantity * estimated_price
    decision = interrupt({
        "type": "simulated_stock_purchase",
        "symbol": symbol.upper(),
        "quantity": quantity,
        "estimated_price": estimated_price,
        "estimated_total": round(total, 2),
        "message": "Please approve or reject this simulated purchase."
    })

    if isinstance(decision, dict):
        approved = decision.get("decision") == "approve"
    else:
        approved = decision == "approve"

    if approved:
        return (
            f"Human approval received. SIMULATED purchase approved: "
            f"{quantity} shares of {symbol.upper()} at estimated price {estimated_price:.2f}. "
            f"Estimated total: {total:.2f}. No real trade was placed."
        )

    return f"Simulated purchase request for {symbol.upper()} was rejected. No trade was placed."
