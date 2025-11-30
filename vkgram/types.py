from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    is_admin: bool = False

@dataclass
class Message:
    id: int
    from_id: int
    peer_id: int
    text: str
    date: int
    attachments: List[Any]
    payload: Optional[str] = None
    reply_message: Optional['Message'] = None
    
    @property
    def chat_id(self) -> int:
        return self.peer_id

@dataclass
class Update:
    type: str
    object: Dict[str, Any]
    group_id: int
    event_id: str
