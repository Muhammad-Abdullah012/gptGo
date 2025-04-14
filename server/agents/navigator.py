from pydantic import BaseModel, Field
from google.genai import Client, types
from os import getenv

class NavigatorResponse(BaseModel):
    navigate: str= Field(None, description="Full url to navigate to")

class Navigator:
    def __init__(self):
        self.client = Client(
            api_key=getenv("GOOGLE_API_KEY"),
        )
        self.system_prompt = (
            "You are a navigation AI agent that decides whether to navigate to a new URL based on a user query, the current page URL, and a screenshot of the browser. "
            "Your task is to determine if a navigation action is needed, and if so, provide the full URL to navigate to.\n\n"
            "Always respond in the following JSON format ONLY:\n"
            '{"navigate": "<full_url>"}\n\n'
            "Rules:\n"
            "1. Use both the screenshot and the user query to understand the user's intent.\n"
            '2. If the user is already on the correct page to fulfill the task (i.e., current_url matches the intended site), respond with: {"navigate": ""}.\n'
            '3. If the task requires a specific website (e.g., Instagram, Twitter, Gmail), return the full URL to that site (e.g., "https://www.instagram.com").\n'
            '4. If the target site is unclear or ambiguous, return: {"navigate": ""}.\n'
            "5. Do not explain your answer. Return only the JSON. No extra text.\n\n"
            "Examples:\n"
            "- Query: 'Like 2 Instagram posts'\n"
            '  Current URL: \'https://www.instagram.com\' → {"navigate": ""}\n'
            '  Current URL: \'https://www.google.com\' → {"navigate": "https://www.instagram.com"}\n\n'
            "- Query: 'Send an email'\n"
            '  Current URL: \'https://mail.google.com\' → {"navigate": ""}\n'
            '  Current URL: \'https://www.facebook.com\' → {"navigate": "https://mail.google.com"}\n\n'
            "- Query: 'No idea what to do'\n"
            '  Current URL: \'https://www.google.com\' → {"navigate": ""}\n\n'
            "Return JSON only. Do not include explanations, comments, or formatting outside the JSON object."
        )

    def decide_navigation(self, user_query: str, current_url: str, screenshot: str):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=screenshot, mime_type="image/png"),
                types.Part.from_text(text=user_query),
                types.Part.from_text(text=f"Current URL: {current_url}"),
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_schema=NavigatorResponse,
                system_instruction=self.system_prompt,
                response_mime_type="application/json",
            ),
        )
        print("**********************************************")
        print("Navigator response => ", response.text)
        print("**********************************************")
        return response.text
