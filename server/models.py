from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    prompt: str
    image: str
    previous_actions: List[dict] = Field(
        default_factory=list,
        alias="previousActions",
        description="List of previous actions taken in this task",
    )
    current_url: str = Field(default_factory=str, alias="currentUrl")
    current_page_html: str = Field(default_factory=str, alias="currentPageHtml")


class Action(BaseModel):
    type: Optional[str] = Field(
        None, description="Text to type (only if input focused)", max_length=30
    )
    click: Optional[str] = Field(
        None,
        description="1-2 letter Vimium code (priority over type)",
    )
    done: Optional[bool] = Field(None, description="True only if task is 100% complete")
    reason: str = Field(
        None,
        description="Detailed reasoning including element text/position",
        min_length=20,
    )


class LinkedInAgentResponse(BaseModel):
    """
    Defines the expected JSON response structure from the Gemini model.
    """

    javascript_code: str = Field(
        description="The generated JavaScript code to execute in the browser console for the next action. Should be concise and target a single step. Wrap in an IIFE: (() => { ... })();"
    )
    agent_reasoning: str = Field(
        description="A brief explanation of why this specific JavaScript code was generated, based on the goal, URL, HTML context, and history."
    )
    estimated_completion: Optional[bool] = Field(
        default=None,
        description="Does the agent estimate that executing this JavaScript code will fully complete the original user goal?",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="If unable to generate valid JS or if an obvious issue is detected, provide an error message here.",
    )
