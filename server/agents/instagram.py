from pydantic import BaseModel, Field
from google.genai import Client, types
from json import loads
from os import getenv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InstagramLikePostAgentResponse(BaseModel):
    # xpath: str = Field(..., description="XPath of the element to click")
    css_selector: str = Field(None, description="CSS selector of the element to click")
    # javascript_xpath: str = Field(..., description="JavaScript to click using XPath")
    javascript_css: str = Field(
        None, description="JavaScript to click using CSS selector"
    )
    count: int = Field(None, description="How many repititions do we need?")
    scroll: bool = Field(
        None, description="Boolean to show whether we should scroll or not!"
    )


class InstagramLikePostAgent:
    def __init__(self):
        self.client = Client(
            api_key=getenv("GOOGLE_API_KEY"),
        )
        self.system_prompt = (
            "You are an AI assistant specialized in Instagram browser automation. Your task is to identify a visible, clickable HTML element that matches the user's goal, and return:\n\n"
            "- A CSS selector (`css_selector`) that targets the element(s)\n"
            "- A JavaScript string (`javascript_css`) that performs the action, using Instagram-specific logic\n"
            "- A boolean `scroll` flag to indicate whether scrolling is required to bring the target into view\n"
            "- A `count` indicating how many elements to interact with (e.g., like 10 posts)\n\n"
            "### JavaScript generation rules:\n"
            "- Always use `document.querySelectorAll(...)` or `Array.from(...).filter(...)` to collect matching clickable elements.\n"
            "- When clicking multiple elements (e.g., like 10 posts), use a **recursive function** with a delay between each interaction.\n"
            "- Example pattern:\n"
            "  let l=0, m=10;\n"
            "  function n() {\n"
            "    let b = Array.from(document.querySelectorAll(\"svg[aria-label='Like']\")).filter(e => e.closest(\"div[role='button']\"));\n"
            "    if (l >= m) return;\n"
            "    b[0].closest(\"div[role='button']\").click();\n"
            "    l++;\n"
            "    window.scrollBy(0, 500);\n"
            "    setTimeout(n, 1200);\n"
            "  }\n"
            "  n();\n"
            "- Do NOT use regular for-loops or index-based selectors.\n"
            "- Avoid using :nth-child, :nth-of-type, or other fragile selectors.\n"
            "- Always filter only the visible and clickable elements.\n"
            "- Always use `.closest('div[role=button]')` to ensure clicking on the actual button container, not just the SVG.\n"
            "- Do NOT stop the function when no matching elements are found. Instagram loads content dynamically — if no buttons are found, you must scroll and retry."
            "- Use `setTimeout(n, 1200)` for delays between each click to allow the DOM to update.\n"
            "- After each click, scroll the window slightly using `window.scrollBy(0, 500);` to load new posts.\n"
            "- Output the JavaScript as a **single-line string** with no newlines or formatting.\n\n"
            "### Response format (strict JSON):\n"
            "{\n"
            '  "css_selector": "CSS selector string",\n'
            '  "javascript_css": "One-line JavaScript code to execute",\n'
            '  "scroll": true or false,\n'
            '  "count": integer\n'
            "}\n\n"
            "Important: The HTML snippet contains only a subset of visible Instagram posts. Your selector and logic must be robust and work in a live, dynamic Instagram feed with scrolling. Be specific, avoid fragile matches, and make sure the code can run directly without modifications."
        )

    def perform_action(self, task: str, html: str):
        try:
            prompt = (
                f"User wants to: {task}\n"
                "Here is a list of visible, clickable elements from the Instagram page HTML."
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_text(text=html),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_schema=InstagramLikePostAgentResponse,
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
