from fastapi import FastAPI, HTTPException
from google.genai import Client, types
from dotenv import load_dotenv
from prompt import PROMPT, SYSTEM_PROMPT
from models import GenerateRequest, Action

from save_img import save_base64_image, img_to_base64
from datetime import datetime
import json

load_dotenv()

app = FastAPI()
client = Client()


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
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text="This is browser screenshot with activated link hints: "),
                        types.Part.from_bytes(
                            data=request.image.split(",")[1], mime_type="image/jpeg"
                        ),
                        types.Part.from_text(text=formatted_prompt),
                        types.Part.from_text(text="These are extra vimium controls: "),
                        types.Part.from_bytes(
                            data=img_to_base64("./images/vimium-controls.png"),
                            mime_type="image/png",
                        ),
                        types.Part.from_text(
                            text="This is how like icon looks like in instagram: "
                        ),
                        types.Part.from_bytes(
                            data=img_to_base64("./images/like.png"),
                            mime_type="image/png",
                        ),
                    ],
                ),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Action,
                temperature=0,
                system_instruction=[
                    types.Part.from_text(text=SYSTEM_PROMPT),
                ],
            ),
        )

        return {"prompt": request.prompt, "generated_text": response.parsed}

    except Exception as e:
        print("Error generating text: ", str(e))
        # Handle any errors during text generation
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}") from e
