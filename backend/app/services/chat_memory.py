from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage
from app.models.schemas import ChatMessage

class ChatMemory:
    def __init__(self):
        # In-memory store: session_id -> list of messages
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def get_history(self, session_id: str) -> List[ChatMessage]:
        """Retrieve chat history for a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(ChatMessage(role=role, content=content))
        
    def clear_session(self, session_id: str) -> None:
        """Clear history for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

chat_memory = ChatMemory()
