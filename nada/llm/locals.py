from langchain_openai import ChatOpenAI

def get_openai(url: str) -> ChatOpenAI:
    llm = ChatOpenAI(
        api_key="NOT_A_REAL_KEY",  # Not required for local server
        base_url=url,
    )
    return llm
