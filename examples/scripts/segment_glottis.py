import VFLabel.nn.segmentation
import argparse
import cv2
import os
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Glottis Segmentation",
        "Generate glottal segmentation for images inside a folder.",
    )

    parser.add_argument("--encoder", type=str, default="mobilenet-v2")
    parser.add_argument("--image_folder", type=str, required=True)
    parser.add_argument("--save_folder", type=str, required=True)

    args = parser.parse_args

    images = VFLabel.io.data.read_images_from_folder(args.image_folder)
    segmentations = VFLabel.nn.segment_glottis_from_folder(args.encoder, images)

    if not os.path.isdir(args.save_folder):
        print(f"Folder {args.save_folder} does not exist. Aborting.")
        exit()

    for id, segmentation in tqdm(enumerate(segmentations)):
        cv2.imwrite(os.path.join(args.save_folder, f"{id:5d}.png"), segmentation)
