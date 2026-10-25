from typing import Literal
from pydantic import BaseModel


class Turn(BaseModel):
    turn_id: int
    speaker: Literal["interviewer", "subject"]
    text: str
