from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    prompt: str
    image: str
    previous_actions: List[dict] = Field(
        default_factory=list,
        alias="previousActions",
        description="List of previous actions taken in this task"
    )
    current_url: str



class Action(BaseModel):
    type: Optional[str] = Field(
        None, description="Text to type (only if input focused)", max_length=30
    )
    click: Optional[str] = Field(
        None,
        description="1-2 letter Vimium code (priority over type)",
    )
    done: Optional[bool] = Field(
        None, description="True only if task is 100% complete"
    )
    reason: str = Field(
        None,
        description="Detailed reasoning including element text/position",
        min_length=20,
    )
