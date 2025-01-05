import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from typing import Optional
import json
# app = FastAPI()

# BASE_API_URL = "https://api.langflow.astra.datastax.com"
# LANGFLOW_ID = "489ebc0a-bb8c-4d89-89c5-b9ee2a5274e0"
# FLOW_ID = "308997f1-06db-45d7-9da6-906785762474"
# APPLICATION_TOKEN = "AstraCS:eForrRsMEPLjMSfYRzhlXxmk:56e7e683e128ac6b4b3bd77129c56fee9cb3d530681c7fbec7c9fd7b1bcfc16d"
#
# class FlowRequest(BaseModel):
#     message: str
#     endpoint: Optional[str] = FLOW_ID
#     tweaks: Optional[dict] = {}
#     output_type: Optional[str] = "chat"
#     input_type: Optional[str] = "chat"
#
# @app.post("/run_flow/")
# def run_flow_api(request: FlowRequest):
#     api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{request.endpoint}"
#
#     payload = {
#         "input_value": request.message,
#         "output_type": request.output_type,
#         "input_type": request.input_type,
#         "tweaks": request.tweaks,
#     }
#
#     headers = {"Authorization": f"Bearer {APPLICATION_TOKEN}", "Content-Type": "application/json"}
#     response = requests.post(api_url, json=payload, headers=headers)
#
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)
#
#     return response.json()
#


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from typing import Optional
from dotenv import load_dotenv, dotenv_values
load_dotenv()
# Constants
BASE_API_URL = os.getenv("BASE_API_URL")
LANGFLOW_ID = os.getenv("LANGFLOW_ID")
APPLICATION_TOKEN = os.getenv("APPLICATION_TOKEN")

FLOW_ID = os.getenv("FLOW_ID")

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Allow both localhost and IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Request and Response Models
class ChatRequest(BaseModel):
    user_message: str
    tweaks: Optional[dict] = {}
    output_type: Optional[str] = "chat"
    input_type: Optional[str] = "chat"

class ChatResponse(BaseModel):
    session_id: str
    response_message: str
    sender: str

# Helper Function to Call LangFlow API
def call_langflow_api(message: str, endpoint: str, tweaks: dict, output_type: str, input_type: str):
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"
    headers = {
        "Authorization": f"Bearer {APPLICATION_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
        "tweaks": tweaks
    }
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"LangFlow API Error: {response.text}")
    return response.json()

# Function to Simplify API Response
def simplify_response(api_response):
    try:
        outputs = api_response.get("outputs", [])
        if not outputs:
            raise ValueError("No outputs in the response.")

        message_data = outputs[0].get("outputs", [])[0].get("results", {}).get("message", {})
        if not message_data:
            raise ValueError("No message found in the response.")

        return {
            "session_id": api_response.get("session_id", ""),
            "response_message": message_data.get("text", "No response text available."),
            "sender": message_data.get("sender_name", "AI")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")

# FastAPI Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Call LangFlow API
        raw_response = call_langflow_api(
            message=request.user_message,
            endpoint=FLOW_ID,
            tweaks=request.tweaks,
            output_type=request.output_type,
            input_type=request.input_type
        )
        # Simplify and return the response
        simplified_response = simplify_response(raw_response)
        return simplified_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
