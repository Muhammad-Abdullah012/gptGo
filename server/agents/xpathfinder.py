from pydantic import BaseModel, Field
from google.genai import Client, types
from json import loads
from os import getenv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class XPathFinderResponse(BaseModel):
    # xpath: str = Field(..., description="XPath of the element to click")
    css_selector: str = Field(None, description="CSS selector of the element to click")
    # javascript_xpath: str = Field(..., description="JavaScript to click using XPath")
    javascript_css: str = Field(
        None, description="JavaScript to click using CSS selector"
    )
    # count: int = Field(None, description="How many repititions do we need?")
    scroll: bool = Field(
        None, description="Boolean to show whether we should scroll or not!"
    )


class XPathFinder:
    def __init__(self):
        self.client = Client(
            api_key=getenv("GOOGLE_API_KEY"),
        )
        self.system_prompt = (
            "You are an AI assistant for browser automation. Your job is to identify an HTML element that best matches the user's goal and return:\n"
            "- Javascript Code to click that element (i.e if it's button or [role='button'])"
            "  - If the element is not directly clickable, use element.closest() to find a clickable ancestor (e.g., button, [role='button'])."
            "- CSS selector of the element to click"
            "Rules:\n"
            "- Always return both `css_selector` and `javascript_css`. The `css_selector` must exactly match the one used inside the JavaScript code."
            "- If the element is not visible, then set scroll true in response and javascript_css and css_selector to empty strings."
            "- Provide the code which can be run directly. confirm the code you provide. Don't format code with newlines."
            "- Use the JSON format strictly:\n"
            "{\n"
            '  "javascript_css": "..."\n'
            '  "css_selector": "..."\n'
            '  "scroll": ".."\n'
            "}"
            "Important: The provided HTML snippet only contains a subset of the visible, clickable elements currently in the viewport — not the full HTML of the page. This means other elements may exist before or after this snippet in the actual page. Therefore:"
            "Avoid using position-based selectors such as :nth-child, :nth-of-type, or index-based selectors. They are fragile and may fail when more elements are present on the full page."
            "Instead, prefer attribute-based selectors (e.g., element[role='..'][aria-label='..']) or unique text/content when available."
            "Ensure your selector and JavaScript target only the intended element, and do not match similar or duplicate elements outside the provided HTML snippet."
            "Always prioritize specificity and robustness. Your response must work even when the actual page contains many similar elements."
        )

    def find_x_path(self, task: str, html: str):
        try:
            prompt = (
                f"User wants to: {task}\n"
                "Here is a list of visible, clickable elements from the rendered page HTML."
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_text(text=html),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_schema=XPathFinderResponse,
                    system_instruction=self.system_prompt,
                    response_mime_type="application/json",
                ),
            )

            logger.info("**********************************************")
            logger.info("XPathFinder response => %s", response.text)
            logger.info("**********************************************")

            return loads(response.text)
        except Exception as e:
            logger.exception("Unexpected error occurred %s", e)
            raise
