import torch
import torch.optim as optim
from torch.utils.data import DataLoader

import os
import torch.nn as nn
import VFLabel.nn.dataset as dataset
import VFLabel.nn.lr_scheduler as lr_scheduler
import VFLabel.nn.train_binary_seg_model

from VFLabel.utils.enums import NN_MODE
import torch
import csv
import segmentation_models_pytorch as smp
from segmentation_models_pytorch.encoders import get_preprocessing_fn
from tqdm import tqdm

# TODO: Pass device along in functions instead of defining it globally
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def train_glottis_segmentation_network(
    save_checkpoint_path: str,
    dataset_path: str,
    encoder: str = "mobilenet_v2",
    batch_size: int = 16,
) -> nn.Module:
    checkpoint_path = os.path.join(
        save_checkpoint_path, "glottis_" + encoder + ".pth.tar"
    )

    # TODO: Decide if we should load this from a JSON file.
    # Until then, i'll hardcode stuff that has worked good for me in the past.
    num_epochs: int = 25
    learning_rate: float = 0.0005
    in_channels: int = 3
    csv_eval_filename: str = os.path.join(
        save_checkpoint_path, "glottis_" + encoder + "_eval.csv"
    )
    csv_train_filename: str = os.path.join(
        save_checkpoint_path, "glottis_" + encoder + "_train.csv"
    )

    train_ds = dataset.HLE_BAGLS_Fireflies_Dataset(dataset_path, NN_MODE.TRAIN)
    eval_ds = dataset.HLE_BAGLS_Fireflies_Dataset(dataset_path, NN_MODE.EVAL)
    test_ds = dataset.HLE_BAGLS_Fireflies_Dataset(dataset_path, NN_MODE.TEST)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        num_workers=8,
        pin_memory=True,
        shuffle=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        eval_ds,
        batch_size=batch_size,
        num_workers=8,
        pin_memory=True,
        shuffle=False,
        drop_last=True,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        num_workers=8,
        pin_memory=True,
        shuffle=False,
        drop_last=True,
    )

    model = smp.Unet(
        encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=in_channels,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=1,
    ).to(DEVICE)

    loss_func = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(
        model.decoder.parameters(),
        lr=learning_rate,
    )

    best_iou = 0.0
    scheduler = lr_scheduler.PolynomialLR(optimizer, num_epochs, power=2.0)

    csvfile = open(csv_eval_filename, "a", newline="")
    writer = csv.writer(csvfile)
    writer.writerow(["Dice", "IoU", "Eval Loss", "Train Loss"])

    for epoch in tqdm(range(num_epochs)):
        scheduler.update_lr()

        # Train the network
        train_loss = VFLabel.nn.train_binary_seg_model.train(
            train_loader, loss_func, model, scheduler
        )

        # Eval
        eval_dice, eval_iou, eval_loss = VFLabel.nn.train_binary_seg_model.evaluate(
            val_loader, model, loss_func
        )

        print(
            f"Train loss {train_loss}, Eval IOU: {eval_iou.item()}, Eval loss: {eval_loss}"
        )

        if eval_iou.item() > best_iou:
            state_dict = model.state_dict()
            torch.save(state_dict, checkpoint_path)
            best_iou = eval_iou

        writer.writerow([eval_dice.item(), eval_iou.item(), eval_loss, train_loss])
    csvfile.close()

    best_model = smp.Unet(
        encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=in_channels,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=1,
    ).cpu()
    best_model = model.load_state_dict(state_dict)

    eval_dice, eval_iou, eval_loss = VFLabel.nn.train_binary_seg_model.evaluate(
        test_loader, model, loss_func
    )

    with open(csv_train_filename, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Dice", "IoU"])
        writer.writerow([eval_dice.item(), eval_iou.item()])

    return best_model


if __name__ == "__main__":
    train_glottis_segmentation_network(
        "assets/models", "/media/nu94waro/Windows_C/save/datasets", "mobilenet_v2"
    )
    train_glottis_segmentation_network(
        "assets/models",
        "/media/nu94waro/Windows_C/save/datasets",
        "efficientnet-b0",
        batch_size=8,
    )
    train_glottis_segmentation_network(
        "assets/models",
        "/media/nu94waro/Windows_C/save/datasets",
        "timm-mobilenetv3_large_100",
        batch_size=8,
    )
    train_glottis_segmentation_network(
        "assets/models",
        "/media/nu94waro/Windows_C/save/datasets",
        "resnet18",
        batch_size=8,
    )
    train_glottis_segmentation_network(
        "assets/models",
        "/media/nu94waro/Windows_C/save/datasets",
        "resnet34",
        batch_size=8,
    )
