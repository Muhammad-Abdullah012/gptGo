from pydantic import BaseModel, Field
from google.genai import Client, types
from json import loads
from os import getenv
import logging
import json
from pathlib import Path
import asyncio

from models import LinkedInAgentResponse

data_dir = Path(__file__).resolve().parent.parent / "data"
json_path = data_dir / "linkedin_filters.json"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LinkedInAgent:
    def __init__(self):
        """
        Initializes the LinkedIn Agent with the Gemini client and system prompt.
        """
        api_key = getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        self.client = Client(api_key=api_key)
        self.system_prompt = """
You are an expert AI assistant specialized in interacting with LinkedIn web pages.
Your primary goal is to help users achieve tasks, primarily related to searching and filtering, by generating JavaScript code.

**Make sure to first analyze the user's goal, the current page context and plan actions thorougly.**

**Your Task:**
Analyze the user's goal, the current page URL, recent action history, and the provided HTML content.
Based on this analysis, generate concise, executable JavaScript code for the *next logical single step* required to progress towards the user's goal.

**Inputs You Receive:**
1.  `user_goal`: The user's objective in natural language.
2.  `current_url`: The URL of the LinkedIn page the user is currently viewing.
3.  `last_actions`: A history of recent actions attempted by the agent (JS code, status).
4.  `html_content`: The full HTML source of the current LinkedIn page.

**Output You MUST Generate:**
A single JSON object matching the following schema:
```json
{
  "javascript_code": "String - The JS code to execute. Wrap in IIFE: (() => { ... })();",
  "agent_reasoning": "String - Your reasoning for generating this specific code.",
  "estimated_completion": "Boolean - Optional: True if this step likely completes the goal.",
  "error_message": "String - Optional: Provide error details if JS cannot be generated."
}
```
CRITICAL: Only output the JSON object. Do not include any other text, markdown formatting (like ```json), or explanations outside the JSON structure.

JavaScript Generation Guidelines:

    Target: Generate code to be executed directly in the browser's developer console.

    Robust Selectors: Prioritize stable selectors: ARIA roles/labels (aria-label) etc. Use combinations for robustness (e.g., button[aria-label='Filter results']). Avoid relying solely on volatile class names or exact text content if possible.

    Actions: Simulate user actions:

        Clicking: element.click();

        Typing: element.value = 'text'; element.dispatchEvent(new Event('input', { bubbles: true })); (Ensure 'input' event is fired). Sometimes blur() might be needed after typing. Then, simulate pressing Enter: element.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true })); element.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', bubbles: true }));

        Focus/Blur: element.focus(); element.blur(); if necessary.

    **State Awareness (CRITICAL):**
    *   **Before generating a click action on a checkbox or radio button, ALWAYS check its current state.**
    *   Use the `.checked` property (for standard inputs) or check attributes like `aria-checked="true"` for custom elements.
    *   **Only generate the `element.click()` code for checkbox or radio buttons IF the element is NOT already in the desired state.**
    
    Single Step: Generate code for one atomic action (e.g., click one button, fill one input). Do not try to perform multiple actions in one script.

    Simplicity: Keep the JS simple. Avoid complex logic, loops, or defining many functions within the generated snippet.

    Minified Code: Do not include unnecessary whitespace, comments, or formatting. The code should be as compact as possible while remaining readable.
    
    Applying Filters: When applying filters, ensure they're correctly and intentionally applied by identifying relevant HTML elements and their labels—don't randomly click fields hoping it works.
    Safety:

        Wrap code in an Immediately Invoked Function Expression (IIFE): (() => { /* your code here */ })(); to avoid polluting the global scope.

        Include basic checks for element existence (if (element) { ... }) before interacting.

        Do NOT use alert, prompt, confirm.

        Do NOT generate code that navigates away unexpectedly (window.location.href = ...) unless specifically part of the goal and reasoned.

    Context Awareness: Use the URL and HTML to understand the page context (e.g., search results page, profile page, feed, filter modal). Identify key elements like search bars, filter buttons ('All filters'), specific filter sections, apply buttons.

    History Awareness: Review last_actions. If a previous action failed, try a different approach or selector if appropriate. Don't get stuck repeating the exact same failed action.
    Focus on providing accurate, safe, and effective JavaScript for the immediate next step.
    *Note: Don't assume or Hallucinate anything. Only use what is present in the provided context.*
"""

    async def perform_action(self, task: str, html: str, url: str, history: object):
        try:
            history_str = (
                json.dumps(history, indent=2) if history else "No previous actions."
            )
            prompt = (
                "Here is all context for the task:\n\n"
                f"User Goal: {task}\n\n"
                f"Current Page URL: {url}\n\n"
                f"Recent Action History:\n{history_str}\n\n"
                f"Analyze the following HTML content and generate the *next single JavaScript action* to progress towards the user goal. Respond ONLY with the required JSON object.\n\n"
                f"--- START OF CURRENT PAGE HTML ---\n"
                f"{html}\n"
                f"--- END OF CURRENT PAGE HTML ---"
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_schema=LinkedInAgentResponse,
                    system_instruction=self.system_prompt,
                    response_mime_type="application/json",
                ),
            )

            logger.info("**********************************************")
            logger.info("LinkedIn Agent response => %s", response.text)
            logger.info("**********************************************")

            return loads(response.text)
        except Exception as e:
            logger.exception("Unexpected error occurred %s", e)
            raise
