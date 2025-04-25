from pydantic import BaseModel, Field
from google.genai import Client, types
from json import loads
from os import getenv
import logging
import json
from pathlib import Path
import asyncio

data_dir = Path(__file__).resolve().parent.parent / "data"
json_path = data_dir / "linkedin_filters.json"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LinkedInAgentResponse(BaseModel):
    javascript_css: str = Field(None, description="JavaScript to perform the action")
    done: bool = Field(None, description="Whether the task is completed or not!")


class BasicFiltersAgent:
    def __init__(self):
        self.client = Client(
            api_key=getenv("GOOGLE_API_KEY"),
        )
        self.system_prompt = """
            You are a highly specialized classification agent. Your sole purpose is to analyze a user's query and select the single most relevant filter from a provided list of options.

            **Instructions:**

            1.  **Analyze the Input:** You will receive two pieces of information:
                *   `User Query`: The text input from the user.
                *   `Available Filters`: A list of predefined filter names.
            2.  **Determine Intent:** Carefully examine the `User Query` to understand the user's core intent or the type of information they are seeking or describing.
            3.  **Match to Filter:** Compare the user's intent with the purpose implied by each filter name in the `Available Filters` list.
            4.  **Select the Best Fit:** Choose the *one* filter from the `Available Filters` list that most accurately corresponds to the user's query. There will always be one best fit in the list provided.
            5.  **Output:** Respond with **ONLY** the exact name of the selected filter from the `Available Filters` list.

            **Constraints:**

            *   **Output Format:** Your response MUST be the filter name and nothing else.
            *   **No Extra Text:** Do not include greetings, explanations, justifications, apologies, or any surrounding text.
            *   **Single Selection:** You must select exactly one filter from the provided list.
        """

    async def find_filter(self, task: str):
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                filters = json.load(file)
            prompt = (
                f"User wants to: {task}\n"
                f"Here is a list of basic filters available to decide from: {json.dumps(','.join(filters.keys()))}"
            )

            print("basic filters prompt => ", prompt)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    system_instruction=self.system_prompt,
                ),
            )

            logger.info("**********************************************")
            logger.info("LinkedIn Basic filters agent response => %s", response.text)
            logger.info("**********************************************")
            return response.text
        except Exception as e:
            logger.exception("Unexpected error occurred %s", e)
            raise


class AdvancedFiltersAgent:
    def __init__(self):
        self.client = Client(
            api_key=getenv("GOOGLE_API_KEY"),
        )
        self.basic_filters_agent = BasicFiltersAgent()
        self.system_prompt = """
        You are an intelligent filter identification agent. Your purpose is to analyze user queries, in conjunction with the provided HTML of available filters, to identify any explicit or strongly implied filtering criteria that have *not* already been applied.

        **Task:** Given a user query, the HTML content of available filters, and a single filter that has already been applied, determine the remaining filters mentioned or implied in the query.  Your output should be a structured JSON representation of these identified filters.

        **Input:**

        *   `user_query`: The user's search query (string).
        *   `applied_filter`: A single filter that has already been applied (string).
        *   `filters_html`: The HTML content of the filters popup, containing all available filter options (string).

        **Output Requirements:**

        1.  **Identify Additional Filters:** Parse the `user_query` and analyze the `filters_html` to identify all filter criteria (e.g., price range, brand, color, size, rating, specific features, sorting preferences like 'newest' or 'cheapest'). Use the `filters_html` to understand the possible filter values and categories.

        2.  **Exclude Applied Filter:** Compare the identified filters with the `applied_filter`.  Do NOT include the `applied_filter` or any filter that represents the exact same constraint in your output.

        3.  **JSON Format:** Return a JSON object containing a list of the *additional* identified filters. The JSON structure should be:

            ```json
            {
            "filters": [
                {"category": "filter_category_1", "value": "filter_value_1"},
                {"category": "filter_category_2", "value": "filter_value_2"},
                ...
            ]
            }
            ```

            *   `category`: The category of the filter (e.g., "Brand", "Price", "Color").  Extract this information from the `filters_html`.  Use the most descriptive and user-friendly category name available in the HTML.
            *   `value`: The specific value of the filter (e.g., "Nike", "Under $50", "Red").  Extract this information from the `user_query` and cross-reference with the `filters_html` to ensure it's a valid option.

        4.  **Empty JSON for No Additional Filters:** If the `user_query` only contains information already captured by the `applied_filter`, or if no other filter criteria are found, return an empty JSON object:

            ```json
            {
            "filters": []
            }
            ```

        5.  **Strictness:** Only include filters explicitly mentioned or very strongly implied in the `user_query`. Avoid making assumptions about filters not present in the query. Use the `filters_html` to validate that the inferred filter is a valid option.  If a filter is ambiguous or uncertain, do *not* include it.

        6.  **Conciseness:** Do not add any explanations, greetings, or introductory text. Output *only* the JSON object.

        7.  **HTML Awareness:** Use the `filters_html` to guide your understanding of available filters and their valid values.  This is critical for accurate identification and categorization.  Pay close attention to the structure and labels within the HTML to determine the correct `category` for each filter.

        **Example:**

        *   `user_query`: "red nike shoes under $100"
        *   `applied_filter`: "shoes"
        *   `filters_html`: (Assume this contains HTML for Brand, Color, Price filters)

            **Expected Output:**

            ```json
            {
            "filters": [
                {"category": "Brand", "value": "Nike"},
                {"category": "Color", "value": "Red"},
                {"category": "Price", "value": "Under $100"}
            ]
            }
            ```
        """

    async def find_advanced_filters_to_apply(self, task: str, html: str):
        try:
            filter_to_apply = await self.basic_filters_agent.find_filter(task)
            prompt = (
                f"User wants to: {task}\n"
                f"This filter is already applied: {filter_to_apply}"
                f"Here is the HTML of all available filters:"
            )

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_text(text=html),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    system_instruction=self.system_prompt,
                ),
            )

            logger.info("**********************************************")
            logger.info("LinkedIn Advanced filters agent response => %s", response.text)
            logger.info("**********************************************")
            return response.text
        except Exception as e:
            logger.exception("Unexpected error occurred %s", e)
            raise


class LinkedInAgent:
    def __init__(self):
        self.basic_filters_agent = BasicFiltersAgent()
        self.advance_filters_agent = AdvancedFiltersAgent()
        self.client = Client(
            api_key=getenv("GOOGLE_API_KEY"),
        )
        self.system_prompt = """
            You are an expert JavaScript automation agent. Your sole purpose is to generate clean, efficient, and directly runnable JavaScript code to automate interactions on a web page based on a user's goal and a comprehensive set of provided HTML element information.

            **Your Task:**

            1.  **Analyze the User's Goal:** Understand the complete objective, including initial search terms and specific filter criteria (e.g., location, industry, connection degree) that might be located within an "All filters" dialog.
            2.  **Identify Target Elements:** Use the *complete set* of provided HTML snippets/descriptions to pinpoint all necessary elements for the *entire* workflow: initial search input, initial search trigger, the "All filters" button, relevant filter controls *inside the dialog* (inputs, checkboxes, selects, specific option labels/buttons), and the "Apply" or "Show results" button *within the dialog*.
            3.  **Generate Complete JavaScript Code:** Create a single block of JavaScript code that performs the required actions in the **correct, predefined sequence**. You will receive all necessary HTML information at the start.

            **Mandatory Workflow Sequence for Generated Code:**

            1.  **Initial Search:**
                *   Locate the primary search input field using provided HTML info.
                *   Set its value based on the user's initial search term(s).
                *   Trigger search action by pressing enter.
                *   *(Retry Logic: Attempt this step up to 3 times. If unsuccessful after 3 attempts, set `"done": true` and exit the loop.)*
            2.  **Wait for Initial Results:**
                *   Introduce a waiting period using `async/await` with `new Promise(resolve => setTimeout(resolve, milliseconds));` (e.g., 3000ms) to allow initial results page elements (like the "All Filters" button) to load.
            3.  **Open Advanced Filters Dialog:**
                *   Locate and click the "All filters" button using provided HTML info.
                *   Introduce another waiting period (e.g., 1500ms) to allow the filter dialog/modal to fully appear and its elements to become interactive.
                *   *(Retry Logic: Attempt this step up to 3 times. If unsuccessful after 3 attempts, set `"done": true` and exit the loop.)*
            4.  **Apply Filters Within Dialog:**
                *   For *each* filter specified in the user's goal that resides *within the dialog*:
                    *   Locate the corresponding filter control (checkbox, input, select, specific option button/label) using the provided HTML info for elements *inside the dialog*.
                    *   Interact with the control:
                        *   Checkboxes: Set `.checked = true;` and potentially dispatch a 'change' event: `element.dispatchEvent(new Event('change', {{ bubbles: true }}));`
                        *   Inputs: Set `.value = '...';` and dispatch 'input' and 'change' events if necessary.
                        *   Selects/Dropdowns: Set value or click specific options.
                        *   Specific Option Buttons/Labels: `.click();`
                    *   *(Retry Logic: Attempt interaction with each filter control up to 3 times. If unsuccessful after 3 attempts, skip to the next filter or proceed to the next step.)*
            5.  **Trigger Filter Application from Dialog:**
                *   Introduce a short wait (e.g., 500ms) *after* interacting with the last filter control but *before* clicking the dialog's apply button, to ensure changes register.
                *   Locate and click the "Apply" or "Show results" button *specific to the dialog* using provided HTML info.
                *   Introduce a final waiting period (e.g., 3000ms) *after* clicking the dialog's apply button to allow the main page results to update based on the applied filters.
                *   *(Retry Logic: Attempt this step up to 3 times. If unsuccessful after 3 attempts, set `"done": true` and exit the loop.)*
            6.  **Completion Check:**
                *   If all steps (Search, Wait, Open Dialog, Wait, Apply Filters in Dialog, Apply from Dialog, Wait) were successfully included in the generated code based on the user's goal and provided HTML, set `"done": true`. Otherwise, if any part of the requested workflow couldn't be mapped to the provided HTML, set `"done": false` (though the primary goal is to generate the full code if possible).

            **Input You Will Receive:**

            1.  **User Goal:** Description including initial search terms and desired filter settings (mentioning which filters are expected inside the "All Filters" dialog).
            2.  **Comprehensive HTML Information:** Snippets/descriptions for *all* relevant elements: initial search input/trigger, "All Filters" button, *all necessary filter controls and labels inside the dialog*, and the dialog's "Apply"/"Show results" button.

            **Code Requirements:**

            *   **Standard DOM APIs:** Use `document.querySelector`, `document.getElementById`, `.value`, `.click()`, `.checked`, `dispatchEvent`, `new Event(...)`, etc.
            *   **`async/await` for Waiting:** Structure within an `async` IIFE `(async () => {{ ... }})();` using `await new Promise(resolve => setTimeout(resolve, milliseconds));`.
            *   **Robust Selectors:** Base CSS selectors *precisely* on the provided HTML info.
            *   **Clarity & Sequence:** Strictly follow the Search -> Wait -> Open Dialog -> Wait -> Filter in Dialog -> Apply from Dialog -> Wait sequence.
            *   **Error Handling (Basic):** Include `if (element) {{ ... }}` checks. Log errors via `console.error`.
            *   **Event Dispatching:** Use `element.dispatchEvent(new Event('change', {{ bubbles: true }}));` or similar after changing input/checkbox values programmatically if needed to trigger framework updates.
            *   **Execution Context:** Assume browser console or extension execution.
            *   **Retry Logic Implementation:** Add retry logic for each step using a counter variable (e.g., `let attempt = 0;`) and increment it after each failed attempt. If `attempt >= 3`, log the failure, set `"done": true`, and exit the loop.

            **Output Requirements:**

            *   **Strictly JSON Format:** Single JSON object `{{"..."}}`.
            *   **Specific Key:** Exactly two keys: `javascript_css`.
            *   **Single-Line String Value:** The value is a single string with the complete JS code, JSON-escaped, no literal newlines, minified.
            *   **Directly Executable:** String value runnable via `new Function()`.
            *   **No Extra Text:** Only the JSON object.

            Constraint Checklist Before Outputting:
            1. Is output ONLY JSON? (`{{"javascript_css": "..."}}`)
            2. Is the JS value a single, escaped string?
            3. Does the code follow the sequence: Search -> Wait -> Click 'All Filters' -> Wait -> Interact with Dialog Filters -> Click Dialog Apply -> Wait?
            4. Is async/await IIFE used for waits?
            5. Are selectors based ONLY on provided HTML?
            6. Are interactions (.value, .click, .checked, dispatchEvent) correct?
            7. Are basic `if (element)` checks included?
            8. Is the code runnable in a browser?
            9. Is retry logic implemented with a maximum of 3 attempts per step?
            10. Is `"done": true` set appropriately if any step fails after 3 attempts?

            Generate the complete JavaScript code in one single block based on the user's goal and the full set of provided HTML element information (including elements inside the filter dialog). Do not ask for more information. Do not add any conversational text.
            """

    # *   Locate *all* specified filter elements (dropdowns, checkboxes, text inputs, etc.) using the provided HTML information.
    # *   Programmatically interact with these elements to set the filter values according to the user's goal:
    #   *   Set `.value` for text inputs and select dropdowns.
    #    *   Set `.checked = true/false` for checkboxes and radio buttons.
    #   *   Trigger `change` events using `element.dispatchEvent(new Event('change'));` immediately after setting the value for elements like `<select>` or others that might require it to update the UI or internal state.
    async def perform_action(self, task: str, html: str, url: str, history: list):
        try:
            prompt = (
                f"User wants to: {task}\n"
                f"Here is current page url: {url}\n"
                f"Here are previous actions: {history}\n"
                "Here is a list of visible, clickable elements from the LinkedIn page HTML."
            )
            # filter_to_apply = await self.basic_filters_agent.find_filter(task)
            # advanced_filters = (
            #     await self.advance_filters_agent.find_advanced_filters_to_apply(
            #         task, html=html
            #     )
            # )
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_text(text=html),
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
