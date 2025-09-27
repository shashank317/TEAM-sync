from collections import defaultdict
from typing import List, Dict


class HistoryManager:
    """Simple in-memory per-user conversation history manager.

    Each message is stored in the Gemini-compatible format:
    {"role": <"user"|"model"|"system">, "parts": [{"text": <str>}]}

    Note: This is process-local and not persistent. Consider replacing with
    a DB/Redis-backed implementation for production or multiple workers.
    """

    def __init__(self) -> None:
        self.histories: Dict[str, List[dict]] = defaultdict(list)

    def add_message(self, user_id: str, role: str, text: str) -> None:
        """Store a message for the given user in Gemini format."""
        self.histories[user_id].append({"role": role, "parts": [{"text": text}]})

    def get_history(self, user_id: str) -> List[dict]:
        """Return the conversation history for a user (empty list if none)."""
        return self.histories[user_id]

    def clear_history(self, user_id: str) -> None:
        """Clear a user's conversation history."""
        self.histories[user_id] = []
