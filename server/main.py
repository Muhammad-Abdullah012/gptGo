from fastapi import FastAPI, HTTPException
from google.genai import Client, types
import PIL.Image
from dotenv import load_dotenv
from prompt import PROMPT
from models import GenerateRequest, Action

load_dotenv()

app = FastAPI()
client = Client()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/generate/")
async def generate_text(request: GenerateRequest):
    """
    Endpoint to generate text based on the provided prompt and image.
    The image (base64 encoded) and prompt are both inside request body.
    """
    try:
        print("request => ", request.prompt)
        pil_image = PIL.Image.open("./images/vimium-controls.png")
        # # Generate content using the Gemini API
        # save_base64_image(request.image, "./images/webpage.png")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=request.image.split(",")[1], mime_type="image/jpeg"
                ),
                pil_image,
                (
                    f"You are helping a user perform the following task: {request.prompt}. "
                    "Refer to the instructions below for guidance."
                ),
                PROMPT,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": Action,
                "temperature": 0,
            },
        )
        # Return the generated response
        return {"prompt": request.prompt, "generated_text": response.parsed}

    except Exception as e:
        print("Error generating text: ", str(e))
        # Handle any errors during text generation
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")
