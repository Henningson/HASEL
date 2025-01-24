import albumentations as A
import cv2
import models
import numpy as np
import VFLabel.nn.dataset as datasets
import torch
import torchmetrics
import torchmetrics.classification
import torchmetrics.classification.average_precision
from torch.utils.data import DataLoader
from tqdm import tqdm
from VFLabel.utils.enums import NN_MODE, PointLabel


import VFLabel.cv.gauss_fitting as gauss_fitting

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# The data for this can be generated using the PointClassification gui in the root folder of the project.


if __name__ == "__main__":
    test_transform = A.Compose([A.pytorch.ToTensorV2()])

    test_dataset = datasets.Specularity(
        "SpecularHighlights", NN_MODE.TEST, transform=test_transform
    )
    test_dataset.printStatistics()

    accuracy_scores = []
    dice_scores = []
    precision_scores = []

    precision = torchmetrics.classification.AveragePrecision(
        task="binary", num_classes=2
    ).to(DEVICE)

    accuracy = torchmetrics.classification.Accuracy(task="binary", num_classes=2).to(
        DEVICE
    )

    recall = torchmetrics.classification.Recall(task="binary", num_classes=2).to(DEVICE)

    f1_score = torchmetrics.classification.F1Score(task="binary", num_classes=2).to(
        DEVICE
    )

    mse_values = []
    thresholds = [i * 100 for i in range(1, 50)]
    for threshold in thresholds:
        for image, label in test_dataset:
            image = image.numpy()
            label = label.numpy()

            if label[0] != 0:
                label[0] = 1

            prediction = np.ones_like(label)

            params = gauss_fitting.fit_gaussian_2d(image)
            reconstruction = gauss_fitting.generate_gaussian_2d_from_params(
                image, params
            )
            mse = np.mean((image - reconstruction) ** 2)

            if mse < threshold:
                prediction[0] = 0
            else:
                prediction[0] = 1

            prediction = torch.from_numpy(prediction).float()
            label = torch.from_numpy(label)

            accuracy(prediction, label)
            precision(prediction, label)
            recall(prediction, label)
            f1_score(prediction, label)
            mse_values.append(mse)

        acc = accuracy.compute()
        pr = precision.compute()
        rec = recall.compute()
        f1 = f1_score.compute()

        print(
            f"Threshold: {threshold}, meanMSE: {(sum(mse_values) / len(mse_values)):0.2f}Accuracy {acc:0.2f}, Precision {pr:0.2f}, Recall: {rec:0.2f}, F1: {f1:0.2f}"
        )
