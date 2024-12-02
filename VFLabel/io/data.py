import os
import cv2
import scipy
import numpy as np
import json
import re

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


# Reads a JSON that was created with the PointClick or CotrackerPointClickWidget.
# Returns a numpy array with the point positions similar to the one used in PointClickWidgets.
def dict_from_json(filepath: str) -> dict:
    # Opening JSON file
    json_file = open(filepath)
    data = json.load(json_file)
    json_file.close()

    return data


def point_dict_to_numpy(
    point_dict: dict, grid_width: int, grid_height: int, video_length: int
) -> np.array:
    base = np.zeros([video_length, grid_height, grid_width, 2]) * np.nan
    keys = point_dict.keys()
    sorted_keys = sorted(keys, key=lambda x: int(re.search(r"\d+", x).group()))

    for key in sorted_keys:
        point_list = point_dict[key]

        for point in point_list:
            x = point["x_pos"]
            y = point["y_pos"]
            x_id = point["x_id"]
            y_id = point["y_id"]

            frame = int(key.replace("Frame", ""))

            base[frame, y_id, x_id] = np.array([x, y])

    return base


# Returns two arrays that look like this:
# [Frame, X, Y] and [Frame, x_id, y_id]
def point_dict_to_cotracker(point_dict: dict) -> np.array:
    positions = []
    ids = []
    keys = point_dict.keys()
    sorted_keys = sorted(keys, key=lambda x: int(re.search(r"\d+", x).group()))

    for key in sorted_keys:
        point_list = point_dict[key]

        for point in point_list:
            frame = int(key.replace("Frame", ""))
            x = point["x_pos"]
            y = point["y_pos"]
            x_id = point["x_id"]
            y_id = point["y_id"]

            positions.append(np.array([frame, x, y]))
            ids.append(np.array([frame, x_id, y_id]))

    return np.array(positions), np.array(ids)


def cotracker_to_point_dict(per_frame_points: np.array, ids: np.array) -> dict:
    final_dict = {}
    for frame_num, points in enumerate(per_frame_points):
        point_list = []
        for point, id in zip(points, ids):
            point_dict = {
                "x_pos": point[0].item(),
                "y_pos": point[1].item(),
                "x_id": id[1].item(),
                "y_id": id[0].item(),
            }
            point_list.append(point_dict)
        final_dict[f"Frame{frame_num}"] = point_list
    return final_dict


# Takes in per_frame_points and ids of shape FRAMES x NUM_POINTS x 2 and NUM_POINTS x 2 respectively.
# Outputs np array of size FRAMES x GRID_HEIGHT x GRID_WIDTH x 2 were points correspond to their respective laser id.
def cotracker_to_numpy_array(
    per_frame_points: np.array, ids: np.array, grid_width: int, grid_height: int
) -> np.array:
    base = np.zeros([per_frame_points.shape[0], grid_height, grid_width, 2]) * np.nan

    for frame, points in enumerate(per_frame_points):
        for point, id in zip(points, ids):
            x = point[0]
            y = point[1]
            x_id = id[0]
            y_id = id[1]

            base[frame, y_id, x_id] = np.array([x, y])

    return base


def write_json(filepath: str, dict: dict) -> None:
    with open(filepath, "w+") as outfile:
        json.dump(dict, outfile)


if __name__ == "__main__":
    video_length: int = 100
    grid_width = 18
    grid_height = 18
    data = dict_from_json("projects/test_project/clicked_laserpoints.json")
    point_array = point_dict_to_numpy(data, grid_width, grid_height, video_length)
    points, ids = point_dict_to_cotracker(data)
    a = 1

    # generate_laserpoint_images_from_json(os.path.join(base_path, file_basename), 1200, 800)
    # generate_laserpoint_images_from_mat("data/VideoClick_P181133_E010_A010_F3.mat", "data/laserpoints/", 1200, 800)
