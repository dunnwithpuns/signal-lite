from typing import Annotated, Literal
from pydantic import BaseModel, Field


class Turn(BaseModel, frozen=True):
    turn_id: Annotated[int, Field(gt=0)]
    speaker: Literal["interviewer", "participant"]
    text: str = Field(min_length=1)
