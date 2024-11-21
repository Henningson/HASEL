import os
import cv2
import scipy
import numpy as np
import json

from typing import List


def create_image_data(image_dir, video_file):
    try:
        os.mkdir(image_dir)
    except:
        pass

    print("ffmpeg -i {0} {1}/%05d.png".format(video_file, image_dir))
    os.system(
        "ffmpeg -i {0} -start_number 0 {1}/%05d.png".format(video_file, image_dir)
    )


def generate_laserpoint_images_from_mat(matfile, save_path, image_height, image_width):
    f = scipy.io.loadmat(matfile)
    points_per_frame = list(
        np.moveaxis(f["PP"].reshape(-1, 2, 200).transpose(), -1, -2)
    )
    freezed_points = f["freeze"].reshape(-1, 200).transpose()

    for count, points in enumerate(points_per_frame):
        image = np.zeros((image_height, image_width), dtype=np.uint8)
        cleaned_points = points[~np.isnan(points).any(axis=1)]

        for i in range(cleaned_points.shape[0]):
            if freezed_points[count, i] == 1:
                continue

            cv2.circle(
                image,
                cleaned_points[i].astype(np.int),
                radius=6,
                thickness=-1,
                color=255,
            )

        write_laserdot_mask(save_path, count, image)


def generate_laserpoint_images_from_json(path, image_height, image_width):
    with open(path + ".rois") as file:
        # Load JSON File
        DICT = json.load(file)

        for frame in tqdm(DICT["frames"]):
            image = np.zeros((image_height, image_width), dtype=np.uint8)
            frame_num = frame["frame"]

            were_points_clicked = False
            for point in frame["roi_positions"]:
                y = point["pos"]["y"]
                x = point["pos"]["x"]

                if x > 0 and y > 0:
                    were_points_clicked = True
                    break

            if not were_points_clicked:
                print("No points clicked for Frame {0}".format(frame_num))
                continue

            for point in frame["roi_positions"]:

                y = point["pos"]["y"]
                x = point["pos"]["x"]

                if y < 0 or x < 0:
                    continue

                cv2.circle(
                    image,
                    np.array([x, y]).astype(np.int),
                    radius=6,
                    thickness=-1,
                    color=255,
                )

            write_laserdot_mask(path + "/", frame_num, image)


def write_laserdot_mask(path, index, mask_image):
    try:
        os.mkdir(path)
    except:
        pass

    cv2.imwrite("{}{:05d}.png".format(path, index), mask_image)


def read_video(path):
    cap = cv2.VideoCapture(path)

    frames = []
    ret = True
    while ret:
        ret, img = (
            cap.read()
        )  # read one frame from the 'capture' object; img is (H, W, C)
        if ret:
            frames.append(img)

    return np.array(frames)


def read_images_from_folder(path: str, is_gray: bool = False) -> List[np.array]:
    files = sorted(os.listdir(path))

    images = []
    for file in files:
        filepath = os.path.join(path, file)
        images.append(cv2.imread(filepath, 0 if is_gray else 1))

    return images


if __name__ == "__main__":
    base_path = "Dataset/"
    file_basename = "Human_P181154_Broc15"

    create_image_data(
        os.path.join(base_path, file_basename, "png"),
        "og_data/" + file_basename + ".mp4",
    )

    # generate_laserpoint_images_from_json(os.path.join(base_path, file_basename), 1200, 800)
    # generate_laserpoint_images_from_mat("data/VideoClick_P181133_E010_A010_F3.mat", "data/laserpoints/", 1200, 800)
