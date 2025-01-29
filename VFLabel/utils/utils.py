import os
import random
import string

import cv2
import numpy as np
import torch
import torchvision


def random_ascii_string(
    num_characters: int = 5, chars=string.ascii_uppercase + string.digits
) -> str:
    return "".join(random.choice(chars) for _ in range(num_characters))


def save_checkpoint(state, filename="my_checkpoint.pth.tar"):
    torch.save(state, filename)


def load_checkpoint(checkpoint, model):
    model.load_state_dict(checkpoint["state_dict"])


def check_accuracy(loader, model, device="cuda"):
    num_correct = 0
    num_pixels = 0
    model.eval()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            preds = model(x).argmax(axis=1)
            # print(preds.size())
            # preds = (preds > 0.5).float()
            num_correct += (preds == y).sum()
            num_pixels += torch.numel(preds)
    #        dice_score += (2 * (preds * y).sum()) / (
    #            (preds + y).sum() + 1e-8
    #        )

    print(f"Got {num_correct}/{num_pixels} with acc {num_correct/num_pixels*100:.2f}")
    # print(f"Dice score: {dice_score/len(loader)}")
    model.train()


def save_predictions_as_imgs(loader, model, folder="saved_images/", device="cuda"):

    try:
        os.mkdir(folder)
    except:
        pass

    model.eval()
    for idx, (x, y) in enumerate(loader):
        x = x.to(device=device)
        y = y.to(device=device)

        with torch.no_grad():
            preds = model(x).argmax(axis=1)  # torch.sigmoid(model(x))
            # preds = (preds > 0.5).float()

        class_colors = [
            torch.tensor([0, 0, 0], device=device),
            torch.tensor([0, 255, 0], device=device),
            torch.tensor([0, 0, 255], device=device),
        ]
        colored = class_to_color(preds, class_colors, device=device)
        colored_gt = class_to_color(y, class_colors)
        torchvision.utils.save_image(colored, f"{folder}/pred_{idx}.png")
        torchvision.utils.save_image(colored_gt, f"{folder}{idx}.png")

    model.train()


def class_to_color(prediction, class_colors, device="cuda"):
    prediction = prediction.unsqueeze(0)
    output = torch.zeros(
        prediction.shape[0],
        3,
        prediction.size(-2),
        prediction.size(-1),
        dtype=torch.float,
        device=device,
    )
    for class_idx, color in enumerate(class_colors):
        mask = class_idx == torch.max(prediction, dim=1)[0]
        curr_color = color.reshape(1, 3, 1, 1)
        segment = mask * curr_color
        output += segment

    return output


def class_to_color_np(prediction, class_colors):
    prediction = np.expand_dims(prediction, 0)
    output = np.zeros(
        [prediction.shape[0], 3, prediction.shape[-2], prediction.shape[-1]]
    )
    for class_idx, color in enumerate(class_colors):
        mask = class_idx == prediction
        curr_color = color.reshape(1, 3, 1, 1)
        segment = mask * curr_color
        output += segment

    # Return CV Style image: WIDTH x HEIGHT x CHANNELS
    output = output.squeeze()
    return np.moveaxis(output, 0, -1)


def add_alpha_to_segmentations(image):
    # Create an alpha channel
    alpha_channel = (
        np.ones((image.shape[0], image.shape[1]), dtype=np.uint8) * 255
    )  # Fully opaque

    # Identify black pixels (where all RGB channels are 0)
    black_pixels = np.all(image == [0, 0, 0], axis=-1)

    # Set alpha to 0 for black pixels
    alpha_channel[black_pixels] = 0

    # Combine RGB and alpha channels
    image_with_alpha = np.dstack((image, alpha_channel))

    return image_with_alpha


def draw_per_batch(im, points, color=(255, 255, 255)):
    points = points.astype(np.int32)
    points = points[:, [1, 0]]
    in_bounds = np.bitwise_and(
        np.bitwise_and(points[:, 0] > 0, points[:, 1] > 0),
        np.bitwise_and(points[:, 0] < im.shape[0], points[:, 1] < im.shape[1]),
    )
    points = points[in_bounds, :]
    points = points[:, [1, 0]]

    for j in range(points.shape[0]):
        cv2.circle(im, points[j], radius=2, color=color, thickness=-1)

    return im


def pointLineSegmentDistance(linePointA, linePointB, point):
    l2 = np.sum((linePointB - linePointA) ** 2)

    if l2 == 0.0:
        return np.linalg.norm(point - linePointA)

    t = max(0, min(1, np.dot(point - linePointA, linePointB - linePointA) / l2))
    projection = linePointA + t * (linePointB - linePointA)
    return np.linalg.norm(point - projection)
