#!/usr/bin/env python3
"""
Test script for the merged size estimator
This demonstrates how to use the MergedSizeEstimator class
"""

import os
from merged_size_estimator import MergedSizeEstimator

def test_single_image():
    """Test the estimator on a single image"""
    estimator = MergedSizeEstimator()
    
    # Test with a specific image
    test_image = "../pictures/3.00s - Desk: Chair: Laptop: Computer monitor: Bookshelf: Drawer: Lamp:.jpg"
    
    if os.path.exists(test_image):
        print(f"Testing with image: {test_image}")
        
        # Extract objects from filename
        objects = estimator.extract_objects_from_filename(os.path.basename(test_image))
        print(f"Objects found: {objects}")
        
        # Process the image
        results = estimator.process_image(test_image, objects)
        
        print("\nFinal Results:")
        for result in results:
            print(f"  {result['object']}:")
            print(f"    Length: {result['length']:.3f}m")
            print(f"    Width: {result['width']:.3f}m") 
            print(f"    Height: {result['height']:.3f}m")
            print(f"    Method: {result['method']}")
            if 'depth' in result:
                print(f"    Depth: {result['depth']:.3f}")
            if 'confidence' in result:
                print(f"    Confidence: {result['confidence']:.3f}")
            print()
    else:
        print(f"Test image not found: {test_image}")

def test_folder():
    """Test the estimator on all images in the pictures folder"""
    estimator = MergedSizeEstimator()
    
    print("Processing all images in pictures folder...")
    results = estimator.process_folder()
    
    print(f"\nProcessed {len(results)} images")
    return results

if __name__ == "__main__":
    print("Testing Merged Size Estimator")
    print("=" * 40)
    
    # Test single image
    test_single_image()
    
    print("\n" + "=" * 40)
    
    # Test entire folder
    # Uncomment the line below to process all images
    # test_folder() 