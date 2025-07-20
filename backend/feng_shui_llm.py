import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv(".env.local")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Configure the Gemini SDK
genai.configure(api_key=GOOGLE_API_KEY)

if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env.local")

# Create the model (use "gemini-pro", not "models/gemini-pro")
model = genai.GenerativeModel("gemini-2.5-pro")

def get_fengshui_recommendations(layout_json):
    prompt = f"""
You are a Feng Shui expert. Given a room layout with furniture details, consider how you could arrange each piece of furniture to improve the flow of Qi and comply with Feng Shui principles. 

The center of the room is at (0,0,0) and coordinates should refer to the center of the object. 

For this case, a piece of furniture is defined as one of the following:
bed
nightstand
wardrobe
desk 
chair 
door 
couch 
table 
bookshelf
fridge
window


If you encounter anything else:
- If it is a synonym or alternative name for one of the above, treat it as that piece of furniture.
- If it is not a piece of furniture, ignore it

You have to output coordinates for each piece of furniture in the room following the JSON format below, using their appropriate names and dimensions:
{{
  "room": {{"l": 5.0, "w": 4.5, "x": 0, "y": 0}},
  "furniture1": {{"l": 1, "w": 2, "x": 0, "y": 0, "rotation": 0}},
  "furniture2": {{"l": 2, "w": 3, "x": 4, "y": 2, "rotation": 90}},
}} 

Room and furniture data (in JSON):
{json.dumps(layout_json, indent=2)}

Ensure the response makes sense logically (chair by the desk, not wasting space, etc) and there is no overlapping furniture, and that all furniture is within the room dimensions. Output only a json response, no other text."""
    # Generate the response
    response = model.generate_content(prompt)

    # Strip code block wrappers if they exist
    content = response.text
    if content.startswith("```json"):
        content = content.strip("```json").strip("```").strip()

    return content

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
            "object": "chair",
              "length": 0.6,
              "width": 0.6,
              "height": 0.9
            },
            {
            "object": "bed",
              "length": 0.6,
              "width": 0.6,
              "height": 0.9
            },
            {
            "object": "nightstand",
              "length": 0.6,
              "width": 0.6,
              "height": 0.9
            }
        ]
    }

    try:
        result = get_fengshui_recommendations(layout)
        # print(json.dumps(result, indent=2))
        print(result)
    except Exception as e:
        print("Error:", e)
