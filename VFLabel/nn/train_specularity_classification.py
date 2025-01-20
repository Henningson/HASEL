import albumentations as A
import cv2
import models
import nn.dataset as datasets
import torch
import torchmetrics
import torchmetrics.classification
import torchmetrics.classification.average_precision
from torch.utils.data import DataLoader
from tqdm import tqdm
from utils.enums import NN_MODE

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# The data for this can be generated using the PointClassification gui in the root folder of the project.


if __name__ == "__main__":
    epochs = 100
    batch_size = 8

    train_transform = A.Compose(
        [
            A.Affine(translate_percent=0.15, p=0.5),
            A.Rotate(limit=40, border_mode=cv2.BORDER_CONSTANT, p=0.5),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.Perspective(scale=(0.05, 0.2), p=0.5),
            A.Normalize(
                mean=[0.0],
                std=[1.0],
                max_pixel_value=255.0,
            ),
            A.pytorch.ToTensorV2(),
        ],
    )

    eval_transform = A.Compose(
        [
            A.Normalize(
                mean=[0.0],
                std=[1.0],
                max_pixel_value=255.0,
            ),
            A.pytorch.ToTensorV2(),
        ],
    )

    train_transform = eval_transform

    train_dataset = datasets.Specularity(
        "SpecularHighlights", NN_MODE.train, transform=train_transform
    )
    train_dataset.printStatistics()
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    eval_dataset = datasets.Specularity(
        "SpecularHighlights", NN_MODE.eval, transform=eval_transform
    )
    eval_dataset.printStatistics()
    eval_loader = DataLoader(eval_dataset, batch_size=batch_size, shuffle=False)

    model = models.FullyConnected().to(DEVICE)
    loss = torch.nn.CrossEntropyLoss()
    optim = torch.optim.Adam(model.parameters(), lr=0.0001)

    accuracy_scores = []
    dice_scores = []
    precision_scores = []

    per_epoch_train_loss = []
    per_epoch_val_loss = []

    best_score = 0.0

    for epoch in tqdm(range(epochs)):
        model.train()
        mean_train_loss = []
        mean_val_loss = []

        loop = tqdm(train_loader, desc="TRAINING")
        for images, labels in loop:
            optim.zero_grad()

            # forward
            prediction = model(images)
            loss_val = loss(prediction, labels.squeeze())

            loss_val.backward()
            mean_train_loss.append(loss_val.item())
            optim.step()

            loop.set_postfix(loss=sum(mean_train_loss) / len(mean_train_loss))
        per_epoch_train_loss.append(sum(mean_train_loss) / len(mean_train_loss))

        precision = torchmetrics.classification.AveragePrecision(
            task="multiclass", num_classes=3
        ).to(DEVICE)

        accuracy = torchmetrics.classification.Accuracy(
            task="multiclass", num_classes=3
        ).to(DEVICE)

        recall = torchmetrics.classification.Recall(
            task="multiclass", num_classes=3
        ).to(DEVICE)

        f1_score = torchmetrics.classification.F1Score(
            task="multiclass", num_classes=3
        ).to(DEVICE)

        model.eval()
        for images, labels in eval_loader:
            # forward
            prediction = model(images)

            loss_val = loss(prediction, labels.squeeze()).item()

            mean_val_loss.append(loss_val)
            accuracy(prediction, labels.squeeze())
            precision(prediction, labels.squeeze())
            recall(prediction, labels.squeeze())
            f1_score(prediction, labels.squeeze())

        torch.save(model.state_dict(), f"models/{epoch:05d}.pth.tar")

        per_epoch_val_loss.append(sum(mean_val_loss) / len(mean_val_loss))
        acc = accuracy.compute()
        pr = precision.compute()
        rec = recall.compute()
        f1 = f1_score.compute()

        score = (pr + rec + f1) / 3.0
        if score > best_score:
            best_score = score
            torch.save(model.state_dict(), "models/best_model.pth.tar")

        print(
            "Loss: {0:0.2f}, Accuracy {1:0.2f}, Precision {2:0.2f}, Recall: {3:0.2f}, F1: {4:0.2f}".format(
                per_epoch_val_loss[-1], acc, pr, rec, f1
            )
        )
        accuracy_scores.append(acc)
        precision_scores.append(pr)
