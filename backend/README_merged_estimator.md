# Merged Size Estimator

This module combines Gemini AI predictions with YOLO + MiDaS depth-based predictions to provide more accurate object size estimates.

## How it works

The merged estimator uses two approaches:

1. **Depth-based estimation (YOLO + MiDaS)**: 
   - Uses YOLO to detect objects
   - Uses MiDaS to estimate depth
   - Calculates real-world dimensions using camera intrinsics
   - Weight: 70% in final merged result

2. **AI-based estimation (Gemini)**:
   - Uses Gemini AI to estimate object dimensions from visual analysis
   - Weight: 30% in final merged result

## Features

- **Intelligent merging**: Combines both methods with weighted averaging
- **Fallback handling**: Uses depth-only or Gemini-only when one method fails
- **JSON output**: Saves results in structured format
- **Batch processing**: Can process entire folders of images
- **Object matching**: Matches objects between methods using name similarity

## Usage

### Basic usage

```python
from merged_size_estimator import MergedSizeEstimator

# Initialize the estimator
estimator = MergedSizeEstimator()

# Process a single image
objects = ["Desk", "Chair", "Laptop"]
results = estimator.process_image("path/to/image.jpg", objects)

# Process all images in a folder
results = estimator.process_folder("pictures/")
```

### Running the test script

```bash
cd hackthesix/backend
python test_merged_estimator.py
```

### Running the main script

```bash
cd hackthesix/backend
python merged_size_estimator.py
```

## Output format

Each object gets a result dictionary with:

```json
{
  "object": "chair",
  "length": 0.45,
  "width": 0.45, 
  "height": 0.85,
  "depth": 2.3,
  "confidence": 0.92,
  "method": "merged"
}
```

Where `method` can be:
- `"merged"`: Both methods contributed
- `"depth_only"`: Only depth-based estimation worked
- `"gemini_only"`: Only Gemini estimation worked

## Configuration

### Camera intrinsics

Update these values in the `MergedSizeEstimator.__init__()` method for your camera:

```python
self.f_mm = 4.15  # focal length in mm
self.sensor_width_mm = 6.17  # sensor width in mm
```

### Weights

Adjust the merging weights in `merge_estimates()`:

```python
'length': self.weighted_average(depth_est.get('length', 0), gemini_est.get('length', 0), 0.7, 0.3)
#                                                                                           ^  ^
#                                                                                    depth  gemini
```

## Requirements

- `torch`
- `torchvision` 
- `opencv-python`
- `ultralytics`
- `PIL`
- `google-generativeai`
- `numpy`

## File structure

```
backend/
├── merged_size_estimator.py    # Main estimator class
├── test_merged_estimator.py    # Test script
├── pictures/                   # Input images
└── merged_size_estimates.json  # Output results
```

## Advantages over individual methods

1. **More accurate**: Combines the strengths of both approaches
2. **Robust**: Falls back to individual methods if one fails
3. **Depth information**: Provides actual depth values for 3D applications
4. **Confidence scores**: Includes YOLO confidence for reliability assessment
5. **Flexible**: Easy to adjust weights based on your use case 