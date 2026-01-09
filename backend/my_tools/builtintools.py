from langchain_community.tools import DuckDuckGoSearchRun , WikipediaQueryRun
from langchain_core.tools import tool
from langchain_community.utilities import WikipediaAPIWrapper

def duckduckgo_search(query: str) -> str:
    """
    Perform a web search using DuckDuckGo search engine.
    
    This tool searches the web using DuckDuckGo to find current information
    on various topics. It's useful for getting up-to-date answers to questions
    that require recent information.
    
    Args:
        query (str): The search query or question to look up.
    
    Returns:
        str: Search results containing relevant information from the web.
    
    Example:
        >>> duckduckgo_search("What is the capital of France?")
        "Paris is the capital of France..."
    """
    search = DuckDuckGoSearchRun()
    return search.invoke(query)


def wikipedia_search(query: str, lang: str = "en") -> str:
    """
    Search for information on Wikipedia.
    
    This tool queries Wikipedia for detailed, structured information on
    various topics. It's ideal for factual, historical, or encyclopedia-style
    information.
    
    Args:
        query (str): The topic or query to search for on Wikipedia.
        lang (str): The language code for Wikipedia. Default is "en" (English).
    
    Returns:
        str: Wikipedia article summary or search results.
    
    Example:
        >>> wikipedia_search("Quantum mechanics")
        "Quantum mechanics is a fundamental theory in physics..."
    """
    api_wrapper = WikipediaAPIWrapper(lang=lang , wiki_client=any)
    search = WikipediaQueryRun(api_wrapper=api_wrapper)
    return search.invoke(query)

    

if __name__  == "__main__":
    result = wikipedia_search("Who are founder of OpenAI")
    # next call 
    print(result)
    
    print(f"{"-"*50}next{"-"*50}")
    
    result = duckduckgo_search("who is the founder of OpenAI")
    print(result)

