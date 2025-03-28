from pydantic import BaseModel, Field
from typing import Optional

class GenerateRequest(BaseModel):
    prompt: str
    image: str


class Action(BaseModel):
    """
    Represents the expected JSON response structure.
    """
    type: Optional[str] = Field(None, description="Text to type.")
    click: Optional[str] = Field(None, description="A 1-2 letter sequence to click.")
    done: Optional[bool] = Field(None, description="Indicates task completion.")
