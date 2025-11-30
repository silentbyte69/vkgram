import json
from enum import Enum
from typing import List, Dict, Any, Optional

class ButtonColor(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary" 
    NEGATIVE = "negative"
    POSITIVE = "positive"

class Button:
    def __init__(
        self,
        text: str,
        color: ButtonColor = ButtonColor.PRIMARY,
        payload: Optional[Dict] = None
    ):
        self.text = text
        self.color = color
        self.payload = payload or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "text",
                "label": self.text,
                "payload": json.dumps(self.payload, ensure_ascii=False)
            },
            "color": self.color.value
        }

class Keyboard:
    def __init__(self, one_time: bool = False, inline: bool = False):
        self.one_time = one_time
        self.inline = inline
        self.rows = []
    
    def add(self, *buttons: Button) -> 'Keyboard':
        """Add buttons to a new row"""
        self.rows.append(list(buttons))
        return self
    
    def row(self, *buttons: Button) -> 'Keyboard':
        """Add buttons to a new row (alias)"""
        return self.add(*buttons)
    
    def to_json(self) -> str:
        keyboard_dict = {
            "one_time": self.one_time,
            "inline": self.inline,
            "buttons": [
                [button.to_dict() for button in row]
                for row in self.rows
            ]
        }
        return json.dumps(keyboard_dict, ensure_ascii=False)
