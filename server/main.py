from fastapi import FastAPI, HTTPException
from openai import OpenAI
from dotenv import load_dotenv
from prompt import PROMPT, SYSTEM_PROMPT
from models import GenerateRequest
import google.generativeai as genai
from save_img import save_base64_image, img_to_base64
from datetime import datetime
from os import getenv
import json
import re
from PIL import Image
import base64

load_dotenv()

app = FastAPI()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
)

genai.configure(api_key=getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-pro")


@app.get("/")
def read_root():
    return {"Status": "OK"}


@app.post("/generate/googleai/")
async def generate_googleai(request: GenerateRequest):
    """
    Endpoint to generate text based on the provided prompt and image.
    The image (base64 encoded) and prompt are both inside request body.
    """
    try:
        print("request => ", request.prompt)

        image_path = f"./images/webpage_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        # # Generate content using the Gemini API
        save_base64_image(
            request.image,
            image_path,
        )
        prompt = {
            "prompt": """
Context:
You're on a social media feed page. Each post has a "Like" icon. It may be off-screen initially.
Goal:
Like 3 posts.

Instructions:
You are a Vimium power-user agent. Think step by step. Inspect whether the Like icon is visible; if so, click its hint. If it's not visible, scroll down by pressing 'j' until it appears. Then click it. Always explain your reasoning.

Output schema:
{
  "click": "string — Vimium hint(s) to click (e.g. 'f', '1', 'gg'). Empty if none.",
  "key":   "string — Vimium key(s) to press (e.g. 'j', 'k'). Empty if none.",
  "type":  "string — Text to type into the page. Empty if none.",
  "done":  "boolean — True if no further actions are needed.",
  "target_visible": "boolean — True if the Like icon is already on screen.",
  "scroll": "boolean — True if you need to scroll to find it.",
  "reason": "string — Detailed explanation of your decision."
}

Example:
{
  "click": "",
  "key": "j",
  "type": "",
  "done": false,
  "target_visible": false,
  "scroll": true,
  "reason": "The Like icon is not in view yet, so we scroll down using 'j' to reveal it."
}
        
            """,
        }
# Step 3: Open and encode image to base64
        with open(image_path, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode("utf-8")
        print("request => ", request.image)

        response = model.generate_content(
            [
                {
                    "mime_type": "image/png",
                    "data": b64_string,
                },
                json.dumps(prompt),
            ],
            generation_config={
                "temperature": 0  # Lower temp = more deterministic, use 0–0.3 for precise tasks
            },
        )

        print("**********************************************")
        print("response => ", response.text)
        return {
            "prompt": request.prompt,
            "generated_text": response.text,
        }

    except Exception as e:
        print("Error generating text: ", str(e))
        # Handle any errors during text generation
        raise HTTPException(
            status_code=500, detail=f"Error generating text: {str(e)}"
        ) from e


@app.post("/generate/")
async def generate_text(request: GenerateRequest):
    """
    Endpoint to generate text based on the provided prompt and image.
    The image (base64 encoded) and prompt are both inside request body.
    """
    try:
        print("request => ", request.prompt)
        # # Generate content using the Gemini API
        save_base64_image(
            request.image,
            f"./images/webpage_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
        )
        formatted_prompt = PROMPT.format(
            prompt=request.prompt,
            previous_actions=json.dumps(request.previous_actions, indent=2),
        )
        completion = client.chat.completions.create(
            model="google/gemini-pro-1.5",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                        },
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": formatted_prompt},
                        {"type": "image_url", "image_url": {"url": request.image}},
                    ],
                },
            ],
            response_format="json",
        )
        raw_content = completion.choices[0].message.content
        print("response => ", completion)
        print("**********************************************")
        print("generated text => " + raw_content)
        match = re.search(r"```json\n(.*?)\n```", raw_content, re.DOTALL)
        if not match:
            raise HTTPException(
                status_code=500,
                detail="Failed to parse response: No JSON content found",
            )

        json_str = match.group(1)
        try:
            parsed_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to decode JSON: {str(e)}"
            ) from e

        print("Parsed data =>", parsed_data)

        return {
            "prompt": request.prompt,
            "generated_text": parsed_data,
            "raw_response": raw_content,
        }

    except Exception as e:
        print("Error generating text: ", str(e))
        # Handle any errors during text generation
        raise HTTPException(
            status_code=500, detail=f"Error generating text: {str(e)}"
        ) from e
