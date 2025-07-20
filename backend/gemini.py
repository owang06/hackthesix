import os
import PIL.Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
API_KEY = os.getenv("GAPI_KEY")

genai.configure(api_key=API_KEY)

# Determine the correct pictures folder path based on where the script is run from
import os
script_dir = os.path.dirname(os.path.abspath(__file__))  # backend/
project_root = os.path.dirname(script_dir)  # hackthesix/
PICTURES_FOLDER = os.path.join(project_root, "pictures")

def extract_objects_from_filename(filename):
    # Assumes filename format: "2.00s - Object1 Object2 Object3.jpg"
    # Remove extension
    base = os.path.splitext(filename)[0]
    # Split on " - " to separate timestamp and object names
    parts = base.split(" - ", 1)
    if len(parts) != 2:
        return []
    objects_str = parts[1]
    # Objects separated by space or maybe underscore, adjust if needed
    # Your example uses spaces, so split by space
    objects = objects_str.split()
    return objects

def generate_prompt(objects):
    n = len(objects)
    objects_str = " ".join(objects)
    prompt = (
        f"There are {n} objects visible in this picture: {objects_str}. "
        f"Estimate the real life dimensions of all of these objects IN METERS. "
        f"Be specific, no ranges."
        f"Also do not tell me its not easily measurable. try your best to estimate. if you cant, tell me its 0"
        f"Finally, give me answers in the format of a dictionary {{ 'object': 'Trash Can', 'length': 0.3, 'width': 0.3, 'height': 0.4 }}, if any field is unknown enter 0"
        f"Dont give filler words, only respond with the list"
    )
    return prompt

def process_images():
    print(f"Looking for images in: {PICTURES_FOLDER}")
    print(f"Directory exists: {os.path.exists(PICTURES_FOLDER)}")
    
    if not os.path.exists(PICTURES_FOLDER):
        print(f"Error: Pictures folder not found at {PICTURES_FOLDER}")
        return
    
    files = os.listdir(PICTURES_FOLDER)
    print(f"Found {len(files)} files in pictures folder")
    
    for filename in files:
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        filepath = os.path.join(PICTURES_FOLDER, filename)
        objects = extract_objects_from_filename(filename)
        if not objects:
            print(f"Skipping {filename}: can't parse objects")
            continue

        prompt = generate_prompt(objects)
        # print(f"Processing {filename} with prompt:\n{prompt}\n")

        img = PIL.Image.open(filepath)
        model = genai.GenerativeModel('gemini-1.5-flash')

        try:
            response = model.generate_content(contents=[img, prompt])
            print(f"Response for {filename}:\n{response.text}\n{'-'*40}\n")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    process_images()
