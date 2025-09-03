from config import OWNER_ID

def is_owner(user_id: int) -> bool:
    """
    Check if the given user_id is the bot owner.
    Returns True if yes, otherwise False.
    """
    try:
        return int(user_id) == int(OWNER_ID)
    except Exception:
        return False
