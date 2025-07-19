import re
from gemini import get_gemini_response
from yolov8 import get_yolov8_estimations
from PIL import Image

def parse_dimensions_from_text(text, object_name):
    """
    Parse Gemini dimension text for object_name.
    Looks for dimensions like 'X meters tall', 'Y meters wide', 'Z meters long'
    Returns tuple (length, width, height) or None if not found.
    """
    # Basic regex patterns to find dimensions; adapt as needed
    height = width = length = None

    # Try to find height (tall)
    m = re.search(rf"{object_name}.*?(\d+\.?\d*)\s*meters\s*(tall|high)", text, re.I)
    if m:
        height = float(m.group(1))

    # Try to find width
    m = re.search(rf"{object_name}.*?(\d+\.?\d*)\s*meters\s*(wide|width)", text, re.I)
    if m:
        width = float(m.group(1))

    # Try to find length (long)
    m = re.search(rf"{object_name}.*?(\d+\.?\d*)\s*meters\s*(long|length)", text, re.I)
    if m:
        length = float(m.group(1))

    # Return as tuple (l,w,h) with None if missing
    return length, width, height

def fuse_dimensions(gemini_dims, depth_dims, weight_text=0.6, weight_depth=0.4):
    # For missing dims (None), fall back to available or zero
    fused = []
    for gt, dp in zip(gemini_dims, depth_dims):
        if gt is None and dp is None:
            fused.append(0.0)
        elif gt is None:
            fused.append(dp)
        elif dp is None:
            fused.append(gt)
        else:
            fused.append(weight_text * gt + weight_depth * dp)
    return tuple(fused)

def main(image_path):
    # 1. Get YOLOv8 estimates: list of (label, width_m, height_m)
    yolov8_results = get_yolov8_estimations(image_path)

    # Extract just labels for Gemini prompt
    labels = list(set(label for label, _, _ in yolov8_results))

    # 2. Get Gemini textual description
    img = Image.open(image_path)
    gemini_text = get_gemini_response(img, labels)

    print(f"\nGemini raw response:\n{gemini_text}\n")

    # 3. For each object, parse Gemini dims and fuse with YOLO+depth dims
    for label, width_d, height_d in yolov8_results:
        gemini_dims = parse_dimensions_from_text(gemini_text, label)
        depth_dims = (None, width_d, height_d)  # Assuming length unknown, use width,height from depth

        fused_dims = fuse_dimensions(gemini_dims, depth_dims)

        print(f"{label}: size (L, W, H) = ({fused_dims[0]:.2f}m, {fused_dims[1]:.2f}m, {fused_dims[2]:.2f}m)")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python merge.py <image_path>")
        sys.exit(1)
    main(sys.argv[1])