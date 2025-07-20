import os
import PIL.Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
API_KEY = os.getenv("GAPI_KEY")

genai.configure(api_key=API_KEY)

# Determine the correct pictures folder path based on where the script is run from
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
    
    # Clear the measurements file before starting new analysis
    output_file = "gemini_measurements.txt"
    with open(output_file, "w") as f:
        f.write("")  # Clear the file
    print(f"Cleared {output_file} for new measurements")
    
    # Collect all object measurements for room size estimation
    all_objects = []
    
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
            
            # Extract dictionary from response and write to file
            import re
            import json
            
            # Look for dictionary pattern in the response
            dict_pattern = r'\{[^}]*\}'
            dict_matches = re.findall(dict_pattern, response.text)
            
            if dict_matches:
                # Write dictionaries to file and collect for room estimation
                with open(output_file, "a") as f:
                    f.write(f"# {filename}\n")
                    for dict_str in dict_matches:
                        f.write(f"{dict_str}\n")
                        # Parse and collect object data for room estimation
                        try:
                            import ast
                            obj_data = ast.literal_eval(dict_str)
                            if isinstance(obj_data, dict) and 'object' in obj_data:
                                all_objects.append(obj_data)
                        except:
                            pass  # Skip if parsing fails
                    f.write("\n")
                print(f"Wrote {len(dict_matches)} dictionary(ies) to {output_file}")
            else:
                print(f"No dictionary found in response for {filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Estimate room size based on all collected objects
    if all_objects:
        room_size = estimate_room_size(all_objects)
        print(f"Estimated room size: {room_size}")
        
        # Write room size to file
        with open(output_file, "a") as f:
            f.write(f"# Room Size Estimation\n")
            f.write(f"{{'length': {room_size['length']}, 'width': {room_size['width']}}}\n")
        
        print(f"Room size written to {output_file}")

def estimate_room_size(objects):
    """
    Estimate room size based on furniture objects and their typical spacing
    """
    # Common furniture types and their typical spacing from walls
    wall_spacing = {
        'bed': 0.6,      # Bed typically 0.6m from walls
        'desk': 0.8,     # Desk typically 0.8m from walls
        'chair': 0.5,    # Chair needs space to pull out
        'wardrobe': 0.3, # Wardrobe close to wall
        'bookshelf': 0.2, # Bookshelf close to wall
        'table': 0.8,    # Table needs space around it
        'couch': 0.5,    # Couch spacing from walls
        'mini-fridge': 0.2, # Mini-fridge close to wall
        'drawer': 0.3,   # Drawer close to wall
    }
    
    # Calculate total object dimensions
    total_length = 0
    total_width = 0
    max_length = 0
    max_width = 0
    
    for obj in objects:
        obj_name = obj.get('object', '').lower()
        
        # Convert string values to float, handle potential conversion errors
        try:
            length = float(obj.get('length', 0))
            width = float(obj.get('width', 0))
        except (ValueError, TypeError):
            length = 0
            width = 0
        
        if length > 0 and width > 0:
            total_length += length
            total_width += width
            max_length = max(max_length, length)
            max_width = max(max_width, width)
    
    # Estimate room size based on furniture layout
    # Assume furniture is arranged along walls with some spacing
    if total_length > 0 and total_width > 0:
        # Add spacing for furniture arrangement
        spacing_factor = 1.5  # Account for gaps between furniture
        wall_spacing_total = 0.6 * 2  # Typical spacing from opposite walls
        
        estimated_length = max(total_length * spacing_factor + wall_spacing_total, max_length * 2.5)
        estimated_width = max(total_width * spacing_factor + wall_spacing_total, max_width * 2.5)
        
        # Round to reasonable values
        estimated_length = round(estimated_length, 1)
        estimated_width = round(estimated_width, 1)
        
        return {
            'length': estimated_length,
            'width': estimated_width
        }
    else:
        # Fallback if no valid measurements
        return {
            'length': 4.0,  # Default room size
            'width': 3.0
        }

if __name__ == "__main__":
    process_images()
