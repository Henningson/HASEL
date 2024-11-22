import torch
import torch.optim as optim
from torch.utils.data import DataLoader

import os
import torch.nn as nn
import dataset
import models

import torchmetrics
import torchmetrics.detection

from VFLabel.utils.defines import NN_MODE
import torch

# TODO: Pass device along in functions instead of defining it globally
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class PolynomialLR:
    def __init__(self, optimizer, total_iters=30, power=0.9, last_epoch=0):
        self._optimizer = optimizer
        self._total_iters = total_iters
        self._power = power
        self._last_epoch = last_epoch
        self._base_lr = self._optimizer.param_groups[0]["lr"]

    def load_state_dict(self, state_dict) -> None:
        self._total_iters = state_dict["total_iters"]
        self._power = state_dict["power"]
        self._last_epoch = state_dict["last_epoch"]

    def state_dict(self) -> dict:
        return {
            "total_iters": self._total_iters,
            "power": self._power,
            "last_epoch": self._last_epoch,
        }

    def get_current_lr(self):
        return self._base_lr * pow(
            1 - self._last_epoch / self._total_iters, self._power
        )

    def update_lr(self):
        for g in self._optimizer.param_groups:
            g["lr"] = self._base_lr * pow(
                1 - self._last_epoch / self._total_iters, self._power
            )

        self._last_epoch += 1

    def step(self):
        self._optimizer.step()

    def zero_grad(self):
        self._optimizer.zero_grad()


def train_point_predictor_network(project_path: str) -> nn.Module:
    checkpoint_path = os.path.join(project_path, "unet_point_predictor.pth.tar")

    # TODO: Decide if we should load this from a JSON file.
    # Up until then, i'll hardcode stuff that has worked good for me in the past.
    batch_size = 8
    num_epochs = 100
    learning_rate = 0.1

    train_ds = dataset.HaselDataset(project_path, NN_MODE.TRAIN)
    eval_ds = dataset.HaselDataset(project_path, NN_MODE.EVAL)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        num_workers=4,
        pin_memory=True,
        shuffle=True,
    )
    val_loader = DataLoader(
        eval_ds,
        batch_size=batch_size,
        num_workers=4,
        pin_memory=True,
        shuffle=True,
    )

    model = models.UNet(in_channels=1, out_channels=1).to(DEVICE)
    loss_func = nn.BCEWithLogitsLoss()
    optimizer = optim.SGD(
        model.parameters(),
        lr=learning_rate,
        momentum=0.9,
    )

    best_iou = 0.0
    scheduler = PolynomialLR(optimizer, num_epochs, power=0.9)
    for epoch in range(num_epochs):
        scheduler.update_lr()

        # Train the network
        train_loss = train(train_loader, loss_func, model, scheduler)

        # Eval
        eval_dice, eval_iou, eval_loss = evaluate(val_loader, model, loss_func)

        if eval_iou.item() > best_iou:
            checkpoint = {"optimizer": optimizer.state_dict()} | model.get_statedict()
            torch.save(checkpoint, checkpoint_path)
            best_iou = eval_iou

    del model

    return models.UNet(
        in_channels=1, out_channels=1, state_dict=torch.load(checkpoint_path)
    )


def train(train_loader, loss_func, model, scheduler):
    model.train()
    running_average = 0.0
    count = 0
    for images, gt_seg in train_loader:
        if images.shape[0] != 8:
            continue

        scheduler.zero_grad()

        images = images.to(device=DEVICE)
        gt_seg = gt_seg.to(device=DEVICE)

        # forward
        pred_seg = model(images).squeeze()
        loss = loss_func(pred_seg.float(), gt_seg.float())

        loss.backward()
        scheduler.step()

        running_average += loss.item()
        count += images.shape[0]

    return running_average / count


def evaluate(val_loader, model, loss_func):
    running_average = 0.0
    count = 0

    model.eval()

    dice = torchmetrics.F1Score(task="binary")
    iou = torchmetrics.JaccardIndex(task="binary")

    for images, gt_seg in val_loader:
        if images.shape[0] != 8:
            continue

        images = images.to(device=DEVICE)
        gt_seg = gt_seg.long().to(device=DEVICE)

        pred_seg = model(images).squeeze()
        softmax = pred_seg.sigmoid()
        dice(softmax.cpu(), gt_seg.cpu())
        iou(softmax.cpu(), gt_seg.cpu())

        loss = loss_func(pred_seg.detach(), gt_seg.float()).item()
        running_average += loss
        count += images.shape[0]

    dice_score = dice.compute()
    iou_score = iou.compute()

    print("DICE: {0:03f}, IoU: {1:03f}".format(dice_score, iou_score))

    return dice_score, iou_score, running_average / count


if __name__ == "__main__":
    main()
