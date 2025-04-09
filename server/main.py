from fastapi import FastAPI, HTTPException
from openai import OpenAI
from dotenv import load_dotenv
from prompt import PROMPT, SYSTEM_PROMPT
from models import GenerateRequest

from save_img import save_base64_image, img_to_base64
from datetime import datetime
from os import getenv
import json
import re

load_dotenv()

app = FastAPI()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("OPENROUTER_API_KEY"),
)


@app.get("/")
def read_root():
    return {"Status": "OK"}


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
