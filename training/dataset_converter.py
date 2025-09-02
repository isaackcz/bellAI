"""
COCO to YOLO Dataset Converter for Bell Pepper Training
Converts COCO format annotations to YOLO format for training
"""

import json
import os
import shutil
from pathlib import Path
import cv2
from sklearn.model_selection import train_test_split

def convert_coco_to_yolo(coco_json_path, images_source_path, output_dataset_path, train_split=0.8):
    """
    Convert COCO format dataset to YOLO format
    
    Args:
        coco_json_path: Path to COCO JSON file
        images_source_path: Path to source images directory
        output_dataset_path: Output directory for YOLO dataset
        train_split: Training split ratio (0.8 = 80% train, 20% val)
    """
    
    # Load COCO JSON
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    print(f"Loading COCO dataset...")
    print(f"Images: {len(coco_data['images'])}")
    print(f"Annotations: {len(coco_data['annotations'])}")
    print(f"Categories: {len(coco_data['categories'])}")
    
    # Create output directories
    output_path = Path(output_dataset_path)
    (output_path / 'images' / 'train').mkdir(parents=True, exist_ok=True)
    (output_path / 'images' / 'val').mkdir(parents=True, exist_ok=True)
    (output_path / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
    (output_path / 'labels' / 'val').mkdir(parents=True, exist_ok=True)
    
    # Create category mapping
    categories = {cat['id']: cat['name'] if cat['name'] else f'bell_pepper_{cat["id"]}' 
                 for cat in coco_data['categories']}
    
    print("Categories mapping:")
    for cat_id, cat_name in categories.items():
        print(f"  {cat_id}: {cat_name}")
    
    # Create image mapping
    images = {img['id']: img for img in coco_data['images']}
    
    # Group annotations by image
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        image_id = ann['image_id']
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(ann)
    
    # Get list of images that have annotations
    valid_image_ids = list(annotations_by_image.keys())
    print(f"Images with annotations: {len(valid_image_ids)}")
    
    # Split into train/val
    train_ids, val_ids = train_test_split(valid_image_ids, train_size=train_split, random_state=42)
    
    print(f"Train images: {len(train_ids)}")
    print(f"Validation images: {len(val_ids)}")
    
    def process_split(image_ids, split_name):
        """Process train or val split"""
        processed = 0
        skipped = 0
        
        for image_id in image_ids:
            image_info = images[image_id]
            image_filename = image_info['file_name']
            
            # Handle the path format from your COCO file
            if '\\' in image_filename:
                # Extract just the filename from the full path
                image_filename = os.path.basename(image_filename)
            
            source_image_path = Path(images_source_path) / image_filename
            
            if not source_image_path.exists():
                print(f"Warning: Image not found: {source_image_path}")
                skipped += 1
                continue
            
            # Copy image
            dest_image_path = output_path / 'images' / split_name / image_filename
            shutil.copy2(source_image_path, dest_image_path)
            
            # Convert annotations to YOLO format
            image_width = image_info['width']
            image_height = image_info['height']
            
            yolo_annotations = []
            
            for ann in annotations_by_image[image_id]:
                bbox = ann['bbox']  # [x, y, width, height] in COCO format
                category_id = ann['category_id']
                
                # Convert COCO bbox to YOLO format
                x_center = (bbox[0] + bbox[2] / 2) / image_width
                y_center = (bbox[1] + bbox[3] / 2) / image_height
                width = bbox[2] / image_width
                height = bbox[3] / image_height
                
                # YOLO format: class_id x_center y_center width height (normalized)
                yolo_annotations.append(f"{category_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
            
            # Save YOLO annotation file
            label_filename = os.path.splitext(image_filename)[0] + '.txt'
            label_path = output_path / 'labels' / split_name / label_filename
            
            with open(label_path, 'w') as f:
                f.write('\n'.join(yolo_annotations))
            
            processed += 1
            
            if processed % 50 == 0:
                print(f"  Processed {processed}/{len(image_ids)} {split_name} images...")
        
        print(f"Completed {split_name}: {processed} processed, {skipped} skipped")
        return processed, skipped
    
    # Process train and validation splits
    train_processed, train_skipped = process_split(train_ids, 'train')
    val_processed, val_skipped = process_split(val_ids, 'val')
    
    # Create dataset.yaml for YOLO training
    yaml_content = f"""# Bell Pepper Dataset Configuration
path: {output_dataset_path}  # dataset root dir
train: images/train  # train images (relative to 'path')
val: images/val  # val images (relative to 'path')

# Classes
nc: {len(categories)}  # number of classes
names: {list(categories.values())}  # class names

# Training info
total_images: {train_processed + val_processed}
train_images: {train_processed}
val_images: {val_processed}
"""
    
    yaml_path = output_path / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"\nDataset conversion completed!")
    print(f"YOLO dataset saved to: {output_dataset_path}")
    print(f"Configuration file: {yaml_path}")
    print(f"Total processed: {train_processed + val_processed} images")
    print(f"Total skipped: {train_skipped + val_skipped} images")
    
    return str(yaml_path)

def verify_dataset(dataset_path):
    """Verify the converted dataset"""
    dataset_path = Path(dataset_path)
    
    print("\nDataset Verification:")
    print("=" * 50)
    
    # Check directory structure
    required_dirs = [
        'images/train', 'images/val',
        'labels/train', 'labels/val'
    ]
    
    for dir_path in required_dirs:
        full_path = dataset_path / dir_path
        if full_path.exists():
            count = len(list(full_path.glob('*')))
            print(f"✓ {dir_path}: {count} files")
        else:
            print(f"✗ {dir_path}: Missing!")
    
    # Load and display dataset.yaml
    yaml_path = dataset_path / 'dataset.yaml'
    if yaml_path.exists():
        print(f"\n✓ dataset.yaml found")
        with open(yaml_path, 'r') as f:
            print(f.read())
    else:
        print(f"\n✗ dataset.yaml missing!")
    
    # Sample verification - check a few label files
    train_labels = list((dataset_path / 'labels' / 'train').glob('*.txt'))
    if train_labels:
        sample_label = train_labels[0]
        print(f"\nSample label file ({sample_label.name}):")
        with open(sample_label, 'r') as f:
            lines = f.readlines()[:3]  # Show first 3 annotations
            for line in lines:
                print(f"  {line.strip()}")
            if len(f.readlines()) > 3:
                print(f"  ... and {len(f.readlines())-3} more annotations")

if __name__ == "__main__":
    # Configuration
    COCO_JSON_PATH = "dataset/dataset_620_red_yellow_cart_only_coco.json"
    IMAGES_SOURCE_PATH = r"D:\datasets\all_620_images_red_yellow_cart_only\images"
    OUTPUT_DATASET_PATH = "dataset/yolo_dataset"
    
    print("Bell Pepper COCO to YOLO Converter")
    print("=" * 40)
    
    # Convert dataset
    yaml_path = convert_coco_to_yolo(
        coco_json_path=COCO_JSON_PATH,
        images_source_path=IMAGES_SOURCE_PATH,
        output_dataset_path=OUTPUT_DATASET_PATH,
        train_split=0.8
    )
    
    # Verify the conversion
    verify_dataset(OUTPUT_DATASET_PATH)
    
    print(f"\nNext steps:")
    print(f"1. Upload the '{OUTPUT_DATASET_PATH}' folder to Google Colab")
    print(f"2. Use the training notebook to train your model")
    print(f"3. Download the trained model and integrate it into your Flask app")
