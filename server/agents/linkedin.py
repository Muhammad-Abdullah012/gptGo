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
        You are an intelligent filter identification agent. Your purpose is to analyze user queries and identify any explicit or strongly implied filtering criteria that have *not* already been applied.
        **Task:** Given a user query and a single filter that has already been applied, determine the remaining filters mentioned or implied in the query.
        
        **Output Requirements:**
        1.  **Identify Additional Filters:** Parse the `user_query` to find all filter criteria (e.g., price range, brand, color, size, rating, specific features, sorting preferences like 'newest' or 'cheapest').
        2.  **Exclude Applied Filter:** Compare the identified filters with the `applied_filter`. Do NOT include the `applied_filter` or any filter that represents the exact same constraint in your output.
        3.  **Format:** Return a comma-separated string of the *additional* identified filters.
        4.  **Empty String for No Additional Filters:** If the `user_query` only contains information already captured by the `applied_filter`, or if no other filter criteria are found, return an empty string (`""`). **Do not return "None", "N/A", or any other text.** Just the empty string.
        5.  **Strictness:** Only include filters explicitly mentioned or very strongly implied. Avoid making assumptions about filters not present in the query.
        6.  **Conciseness:** Do not add any explanations, greetings, or introductory text. Output *only* the comma-separated list or the empty string.
        """

    async def find_advanced_filters_to_apply(self, task: str):
        try:
            filter_to_apply = await self.basic_filters_agent.find_filter(task)
            prompt = (
                f"User wants to: {task}\n"
                f"This filter is already applied: {filter_to_apply}"
            )

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

            1.  **Analyze the User's Goal:** Understand the complete objective described by the user (e.g., search for specific terms, then apply a specific set of filters).
            2.  **Identify Target Elements:** Use the *complete set* of provided HTML snippets or descriptions to pinpoint all necessary elements for the entire workflow: initial search input, initial search trigger, all filter controls (inputs, selects, checkboxes, etc.), and the filter application trigger (if any).
            3.  **Generate Complete JavaScript Code:** Create a single block of JavaScript code that performs the required actions in the **correct, predefined sequence**. You will receive all necessary HTML information at the start.

            **Mandatory Workflow Sequence for Generated Code:**

            1.  **Initial Search:**
                *   Locate the primary search input field using the provided HTML information.
                *   Programmatically set its value based on the user's initial search term(s).
                *   Trigger search action by pressing enter.
            2.  **Wait for Initial Results:**
                *   **Crucially, introduce a waiting period.** Use `async/await` with `new Promise(resolve => setTimeout(resolve, milliseconds));` to pause execution. Assume a reasonable default delay (e.g., 3000 milliseconds) to allow initial results to load before attempting to interact with filter elements.
                *   *(Self-correction Note: A timed delay is required. Do not attempt to wait for specific filter elements to appear unless explicitly instructed and provided with selectors for those elements *as they appear after the initial search*.)*
            3.  **Apply Filter:**
                * Apply {filter} by clicking on button with the same text.
                * Then wait for results to load
                * Then click on "All Filters" button to reveal all filters.
                
            4.  **Trigger Filtered Search/Update:**
                *   Locate and trigger the action that applies the filters (this might be a dedicated "Apply Filters" button, the original search button again, or the filtering might happen automatically upon changing filter values).
                *   If a final action button exists, add another short wait (e.g., 500ms) *after* applying all filters but *before* clicking the final button to ensure all filter changes have registered. If filtering is automatic, this step might be omitted or simply be the completion of the filter interactions.
            5.  *   If all tasks are completed according to user's query and html, then set "done" to true, else set "done" to false.
            **Input You Will Receive:**

            1.  **User Goal:** A clear description of the overall task, including initial search terms and desired filter settings.
            2.  **Comprehensive HTML Information:** Snippets or descriptions for *all* relevant HTML elements needed for the *entire* sequence (initial search input/button, all filter controls, filter apply button/mechanism), including attributes like `id`, `class`, `name`, `placeholder`, `aria-label`, etc.

            **Code Requirements:**

            *   **Standard DOM APIs:** Use standard browser JavaScript and DOM manipulation methods (`document.querySelector`, `document.getElementById`, `.value`, `.click()`, `.checked`, `dispatchEvent`, `new Event('change')`, etc.).
            *   **`async/await` for Waiting:** Structure the code within an `async` IIFE (Immediately Invoked Function Expression) like `(async () => {{ ... }})();` to handle waiting periods using `await new Promise(resolve => setTimeout(resolve, milliseconds));`.
            *   **Robust Selectors:** Generate CSS selectors based *precisely* on the HTML information provided by the user. Use specific selectors (like IDs) when available.
            *   **Clarity & Sequence:** The code logic must be clear and strictly follow the specified Search -> Wait -> Filter -> Apply sequence.
            *   **Error Handling (Basic):** Include basic checks (e.g., `if (element) {{ ... }}`) before interacting with elements to prevent errors if an element isn't found. Log errors to the console using `console.error`.
            *   **Execution Context:** The code will be executed in the browser's developer console or injected via a browser extension within the context of the target web page.
        
            **Output Requirements:**

            *   **Strictly JSON Format:** The entire output must be a single, valid JSON object, starting with `{{` and ending with `}}`.
            *   **Specific Key:** The JSON object must contain exactly one key: `javascript_css`.
            *   **Single-Line String Value:** The value associated with `javascript_css` must be a single string containing the complete, runnable JavaScript code. This string should **not** contain newline characters (`\n` or literal newlines). It should resemble minified code (minimal whitespace, semicolons where needed) but remain syntactically correct JavaScript.
            *   **JSON String Escaping:** The JavaScript code within the string value must be correctly escaped for JSON validity (e.g., backslashes `\` become `\\`, double quotes `"` become `\"`).
            *   **Directly Executable:** The string value must be directly executable when passed to `new Function()`, like `const fn = new Function(output.javascript_css); fn();`.
            *   **No Extra Text:** Do not include *any* text before or after the JSON object (no explanations, greetings, apologies, markdown formatting like ```json).

            Constraint Checklist Before Outputting:

            Is the output ONLY JavaScript code in a single block?
            Does the code follow the sequence: Search -> Wait -> Filter -> Apply/Update?
            Is async/await within an IIFE used for waiting?
            Are selectors based only on the user-provided HTML info?
            Does it handle interactions (.value, .click, .checked, dispatchEvent) correctly?
            Are basic if (element) checks included?
            Is the code runnable in a browser console context?
            Generate the complete JavaScript code in one single block based on the user's goal and the full set of provided HTML element information. Do not ask for more information. Do not add any conversational text.
        """

    # *   Locate *all* specified filter elements (dropdowns, checkboxes, text inputs, etc.) using the provided HTML information.
    # *   Programmatically interact with these elements to set the filter values according to the user's goal:
    #   *   Set `.value` for text inputs and select dropdowns.
    #    *   Set `.checked = true/false` for checkboxes and radio buttons.
    #   *   Trigger `change` events using `element.dispatchEvent(new Event('change'));` immediately after setting the value for elements like `<select>` or others that might require it to update the UI or internal state.
    async def perform_action(self, task: str, html: str):
        try:
            prompt = (
                f"User wants to: {task}\n"
                "Here is a list of visible, clickable elements from the LinkedIn page HTML."
            )
            filter_to_apply = await self.basic_filters_agent.find_filter(task)
            advanced_filters = (
                await self.advance_filters_agent.find_advanced_filters_to_apply(task)
            )
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_text(text=html),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_schema=LinkedInAgentResponse,
                    system_instruction=self.system_prompt.format(
                        filter=filter_to_apply, advanced_filters=advanced_filters
                    ),
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
