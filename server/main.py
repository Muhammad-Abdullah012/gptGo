from pydantic import BaseModel, Field
from typing import Literal, Optional
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from google.genai import Client, types
import base64
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
client = Client()


class GenerateRequest(BaseModel):
    prompt: str
    image: str


class Action(BaseModel):
    """
    Represents the expected JSON response structure.
    Only one of the fields (`navigate`, `type`, `click`, `done`) should be present.
    """

    navigate: Optional[str] = Field(None, description="A URL to navigate to.")
    type: Optional[str] = Field(None, description="Text to type.")
    click: Optional[str] = Field(None, description="A 1-2 letter sequence to click.")
    done: Optional[Literal[None]] = Field(
        None, description="Indicates task completion."
    )


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/generate/")
async def generate_text(request: GenerateRequest):
    """
    Endpoint to generate text based on the provided prompt and image.
    The image is uploaded as a file, and the prompt is passed as form data.
    """
    try:
        # Open the image using PIL
        image =base64.b64decode(request.image)
        # Generate content using the Gemini API
        # response = client.models.generate_content(
        #     model="gemini-2.0-flash",
        #     contents=[
        #         f"You need to choose which action to take to help a user do this task: {prompt}. "
        #         "Your options are navigate, type, click, and done. Navigate should take you to the specified URL. "
        #         "Type and click take strings where if you want to click on an object, return the string with the yellow "
        #         "character sequence you want to click on, and to type just a string with the message you want to type. "
        #         "For clicks, please only respond with the 1-2 letter sequence in the yellow box, and if there are multiple "
        #         "valid options choose the one you think a user would select. For typing, please return a click to click on "
        #         "the box along with a type with the message to write. When the page seems satisfactory, return done as a key "
        #         "with no value. You must respond in JSON only with no other fluff or bad things will happen. The JSON keys "
        #         "must ONLY be one of navigate, type, or click. Do not return the JSON inside a code block.",
        #         types.Part.from_bytes(data=image, mime_type="image/jpeg"),
        #     ],
        #     config={
        #         "response_mime_type": "application/json",
        #         "response_schema": Action,
        #     },
        # )
        # Return the generated response
        return {"prompt": request.prompt, "generated_text": "gemini call is commented!"}

    except Exception as e:
        # Handle any errors during text generation
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")
