from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json
import base64
import requests
import os
from typing import Optional

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FREE_PROMPT = """
You are an expert botanist. Look at this plant photo and return ONLY a JSON object.
No extra text. No explanation. Just the JSON.

Return exactly this structure:
{
  "plant_name": "common name of the plant",
  "scientific_name": "scientific name",
  "needs_water": true or false,
  "health_status": "healthy or sick or stressed",
  "disease_found": true or false,
  "free_tip": "one specific sentence about THIS plant based on what you see",
  "disease_name": null,
  "treatment": null,
  "confidence": 85
}

Visual signs that needs_water = TRUE: wilting, drooping, dry cracked soil, brown crispy edges
Visual signs that needs_water = FALSE: upright firm leaves, moist soil, normal green color
"""

PRO_PROMPT = """
You are an expert botanist and plant pathologist. Look at this plant photo and return ONLY a JSON object.
No extra text. No explanation. Just the JSON.

Return exactly this structure:
{
  "plant_name": "common name of the plant",
  "scientific_name": "scientific name",
  "needs_water": true or false,
  "health_status": "healthy or sick or stressed",
  "disease_found": true or false,
  "free_tip": "one specific sentence about THIS plant based on what you see",
  "disease_name": "specific disease name if found, otherwise null",
  "treatment": "detailed step by step treatment if sick, otherwise null",
  "confidence": 85,
  "sunlight": "sunlight requirements for this plant",
  "soil": "ideal soil type for this plant",
  "humidity": "humidity requirements",
  "fertilizer": "fertilizer recommendations",
  "watering_schedule": "how often to water this specific plant",
  "care_tips": "3 specific care tips for this plant"
}

Be very specific about diseases. If you see yellowing, spots, pests, mold — name them exactly.
For treatment provide numbered steps that are practical and actionable.
Visual signs that needs_water = TRUE: wilting, drooping, dry cracked soil, brown crispy edges
Visual signs that needs_water = FALSE: upright firm leaves, moist soil, normal green color
"""

@app.post("/analyze")
async def analyze_plant(
    image: UploadFile = File(...),
    is_pro: Optional[str] = Form(default="false")
):
    image_bytes = await image.read()
    b64 = base64.b64encode(image_bytes).decode()

    prompt = PRO_PROMPT if is_pro == "true" else FREE_PROMPT

    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'nvidia/nemotron-nano-12b-v2-vl:free',
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
                    {'type': 'text', 'text': prompt}
                ]
            }]
        }
    )

    data = response.json()

    if "choices" not in data:
        return {"error": "AI error", "raw": data}

    raw_text = data["choices"][0]["message"]["content"].strip()

    if "```" in raw_text:
        parts = raw_text.split("```")
        raw_text = parts[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    result = json.loads(raw_text)
    return result

@app.get("/")
def home():
    return {"message": "SproutSense is running!"}