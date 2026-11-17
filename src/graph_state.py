from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class StockMindState(TypedDict):
    messages: Annotated[list, add_messages]
