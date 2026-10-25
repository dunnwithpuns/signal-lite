from typing import Literal
from pydantic import BaseModel


class Turn(BaseModel):
    turn_id: int
    speaker: Literal["interviewer", "participant"]
    text: str = Field(min_length=1)
