async def chatai(prompt: str):
    """
    Dummy AI function for bots that don't have Gemini/OpenAI API.
    This ensures chat_lang.py works without any errors.
    
    You can replace this with real AI later if needed.
    """

    # Always return a safe default response so bot never crashes
    return "Lang Name :- English\nLang Code :- en"
