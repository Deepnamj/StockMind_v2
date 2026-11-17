
from src.common import get_llm

llm = get_llm()

response = llm.invoke(
    "Explain what an AI agent is in two simple sentences."
)

print("\nLangChain Gemini Response:")
print(response.content)
