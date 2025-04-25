from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models import GenerateRequest
from agents.navigator import Navigator
from agents.instagram import InstagramLikePostAgent
from agents.linkedin import LinkedInAgent

from save_img import save_base64_image, extract_base64_from_data_uri
from datetime import datetime

load_dotenv()

app = FastAPI()


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

        # Save the image
        save_base64_image(
            request.image,
            f"./images/webpage_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
        )

        # Initialize Navigator and call decide_navigation
        # navigator = Navigator()
        # navigation_response = navigator.decide_navigation(
        #     user_query=request.prompt,
        #     current_url=request.current_url,
        # )
        if "instagram" in request.current_url:
            instagram = InstagramLikePostAgent()
            response = instagram.perform_action(
                task=request.prompt, html=request.current_page_html
            )
        elif "linkedin" in request.current_url:
            linkedin = LinkedInAgent()
            response = await linkedin.perform_action(
                task=request.prompt, html=request.current_page_html
            )
        else:
            response = {}

        return {
            "prompt": request.prompt,
            # "generated_text": navigation_response,
            "generated_text": response,
        }

    except Exception as e:
        print("Error generating text: ", str(e))
        # Handle any errors during text generation
        raise HTTPException(
            status_code=500, detail=f"Error generating text: {str(e)}"
        ) from e
