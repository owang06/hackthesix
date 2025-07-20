import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from coordinates_llm import get_coordinates

# Load environment variables
load_dotenv(".env.local")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Configure the Gemini SDK
genai.configure(api_key=GOOGLE_API_KEY)

if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env.local")

# Create the model (use "gemini-pro", not "models/gemini-pro")
model = genai.GenerativeModel("gemini-2.5-pro")

def get_coordinates_validation(input_json):
    prompt = f"""
Analyze and validate each piece of furniture in the given data. If any furniture overlaps or is outside the room dimensions, adjust the coordinates accordingly. 

You have to output coordinates for each piece of furniture in the room following the example JSON format below, using their appropriate names and dimensions:
{{
  "room": {{"l": 5.0, "w": 4.5, "x": 0, "y": 0}},
  "furniture1": {{"l": 0.1, "w": 2, "x": 0, "y": 0, "rotation": 0}},
  "furniture2": {{"l": 1.6, "w": 2.0, "x": 3.4, "y": 1.25, "rotation": 0}},
}}
The center of the room is at (0,0,0) and coordinates should refer to the center of the object. 
Only change the coordinates and rotation of the furniture, do not change the dimensions.

Room layout and furniture data (in JSON):
{json.dumps(input_json)}

Output only the JSON response, no other text.

"""
    # Generate the response
    response = model.generate_content(prompt)

    # Strip code block wrappers if they exist
    content = response.text
    if content.startswith("```json"):
        content = content.strip("```json").strip("```").strip()
    
    return content
    # return json.loads(content)

# === TEST ===
if __name__ == "__main__":
    layout = {
  "room": {
    "l": 3.8,
    "w": 4.5,
    "x": 0,
    "y": 0
  },
  "bed": {
    "l": 0.6,
    "w": 0.6,
    "x": -1.95,
    "y": 1.3,
    "rotation": 90
  },
  "nightstand": {
    "l": 0.6,
    "w": 0.6,
    "x": -1.95,
    "y": 0.7,
    "rotation": 0
  },
  "chair": {
    "l": 0.6,
    "w": 0.6,
    "x": 1.8,
    "y": -1.45,
    "rotation": 135
  }
}

    try:
        result = get_coordinates_validation(layout)
        # print(json.dumps(result, indent=2))
        print (result)
    except Exception as e:
        print("Error:", e)
