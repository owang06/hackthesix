import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from feng_shui_llm import get_fengshui_recommendations

# Load environment variables
load_dotenv(".env.local")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Configure the Gemini SDK
genai.configure(api_key=GOOGLE_API_KEY)

if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env.local")

# Create the model (use "gemini-pro", not "models/gemini-pro")
model = genai.GenerativeModel("gemini-2.5-pro")


def get_coordinates(layout_json):
    description = get_fengshui_recommendations(layout_json)
    prompt = f"""
You are an interior design expert. Analyze the given data containing a room layout with furniture details and a description of how each piece should be placed. Then decide coordinates and rotation for each piece of furniture in the room.

you have to output coordinates for each piece of furniture in the room following the JSON format below, using their appropriate names and dimensions:
{{
  "room": {{"l": 5.0, "w": 4.5, "x": 0, "y": 0}},
  "furniture1": {{"l": 0.1, "w": 2, "x": 0, "y": 0, "rotation": 0}},
  "furniture2": {{"l": 1.6, "w": 2.0, "x": 3.4, "y": 1.25, "rotation": 0}},
}}

Room layout description:
{description}

Output only the json, nothing else. 
"""
    # Generate the response
    response = model.generate_content(prompt)

    # Strip code block wrappers if they exist
    content = response.text
    if content.startswith("```json"):
        content = content.strip("```json").strip("```").strip()
    

    return json.loads(content)

# === TEST ===
if __name__ == "__main__":
    layout = {
        "room": {
            "width": 4.5,
            "length": 3.8,
            "height": 2.4
        },
        "furniture": [
            {
                "type": "bed",
                "position": [1.0, 0.5],
                "dimensions": [2.0, 1.5, 0.5],
                "orientation": 90
            },
            {
                "type": "desk",
                "position": [3.5, 2.2],
                "dimensions": [1.2, 0.6, 0.75],
                "orientation": 0
            }
        ]
    }

    try:
        result = get_coordinates(layout)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("Error:", e)
