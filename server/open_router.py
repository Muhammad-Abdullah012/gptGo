import requests
import json
from os import getenv
from dotenv import load_dotenv
from models import GenerateRequest
from prompt import PROMPT
from save_img import img_to_base64

load_dotenv()


def getresponse(request: GenerateRequest):
    return requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + getenv("OPENROUTER_API_KEY"),
            "Content-Type": "application/json",
        },
        data=json.dumps(
            {
                "model": "qwen/qwen2.5-vl-3b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/png;base64,"
                                    + img_to_base64("./images/vimium-controls.png"),
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": request.prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": request.image,
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "action",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "Text to type.",
                                },
                                "click": {
                                    "type": "string",
                                    "description": "A 1-2 letter sequence to click.",
                                },
                                "done": {
                                    "type": "boolean",
                                    "description": "Indicates task completion.",
                                },
                            },
                            "required": [],
                            "additionalProperties": False,
                        },
                    },
                },
            }
        ),
        timeout=30000,
    )
