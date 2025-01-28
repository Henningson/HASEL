![hasel](https://github.com/user-attachments/assets/eac052b4-affd-4f99-9758-9b05f36ca074)
#
**HASEL** (**H**igh-Speed Video **A**nnotation Tool for **S**tructured Light **E**ndoscopy in the Human **L**arynx) is a Deep-Learning-supported tool for generating ground-truth data for High-Speed Video Structured Light Laryngoscopy.
This tool enables to robustly and rapidly generate data of:
* Glottal segmentation with different segmentation architectures
* Vocal fold segmentation via frame-wise interpolation
* Semi-automatic and Deep Learning enhanced generation of laserpoint data.





# Installation
Please follow these instructions to make sure that Hasel runs as intended.
In general, we recommend a current nvidia graphics on par with a quadro RTX 4000.
First, create the environment and install necessary packages.
```
conda create --name VFLabel python=3.12
pip install torch torchvision torchaudio
conda install pyqt qtpy
pip install torchmetrics albumentations imageio kornia segmentation-models-pytorch matplotlib flow_vis tensorboard tqdm pyqtdarktheme-fork
```

Next, install Hasel for **development**:
```
git clone https://github.com/Henningson/VFLabel.git
cd VFLabel
python3 -m pip install -e .
```
  
Next, we need to create a model folder and install metas cotracker3.
For this, you can also follow [these instructions](https://github.com/facebookresearch/co-tracker?tab=readme-ov-file#installation-instructions).
```
cd ..
git clone https://github.com/facebookresearch/co-tracker
cd co-tracker
pip install -e .
```

Next, we need to download the cotracker3 offline version.
```
cd ../VFLabel
mkdir assets/models
cd assets/models
wget https://huggingface.co/facebook/cotracker3/resolve/main/scaled_offline.pth
cd .../..
```

Finally, download the glottis segmentation networks from [here](https://drive.google.com/drive/folders/1U525TcxZ1nhIp5yNJiyW-avK6qZG4rVV?usp=sharing) and move them to ```assets/models/```.

# How to use Hasel
Make a video here.



# Regarding the  glottal segmentation
Glottal Segmentations can also easily be generated from command line arguments, via the supplied script in the examples:
```
python examples/scripts/segment_glottis --encoder mobilenet_v2 --image_folder PATH_TO_WHERE_THE_IMAGES_Are --save_folder OUTPUT_FOLDER
```

##  Available CNNs
We supply four(*) U-Nets with different backbones in this repository.
They can be downloaded here. Make sure to extract the files into ```assets/models```.
Here is the evaluation of the models.
Generally the resnet based backbones are the best performing, but the other backbones are generally better to use on cpu only systems.
You should generally test out which ones work best for you.
You can find how to use the supplied networks in ```examples/scripts```.
*: There's also a efficientnet available, but it generally performs worse than the rest. However, I'd advise you to also test it out on some data.


## Evaluation of available U-Nets
We evaluated the Networks on a combined test-set of the [BAGLS](https://www.bagls.org/) and [HLE](https://github.com/Henningson/HLEDataset) datasets, as well as synthetically created vocal folds using [Fireflies](https://github.com/Henningson/Fireflies).

| Backbone | Eval IoU | Eval DICE | Test Dice | Test IoU |
|----------|----------|----------|----------|----------|
| mobilenet-v2             | 0.864   | 0.927   | 0.893  | 0.807   |
| mobilenetv3_large_100    | 0.845   | 0.916  | 0.789  | 0.65  |
| resnet18                 | 0.856 | 0.922  | 0.882  | 0.789  |
| resnet34                 | 0.846  | 0.917  | 0.883 | 0.791  |




# Train your own glottal segmentation network on large datasets
To train your own network on a bunch of vocalfold datasets, download the [HLE](https://github.com/Henningson/HLEDataset) and [BAGLS](https://www.bagls.org/) dataset, and put them into a common folder.
Next also download the fireflies dataset [from here](google.com) and also extract it into the folder.
The final folder structure should look like this:
```
dataset/
├── BAGLS/
├── HLEDataset/
└── fireflies_dataset_v5/
```
For training, please follow the code in the example script ```examples/scripts/train_glottis_segmentation_network.py```.
There, you will fine-tune the decoder of common segmentation model architectures that were pretrained on imagenet.


## Data preparation


# Examples

![GlotSegmentation](https://github.com/user-attachments/assets/bc77784e-d4ce-4dd8-a725-cfed5569b6bf)
![VFSegmentation](https://github.com/user-attachments/assets/ccc7a8ec-75cc-4073-afe1-7af80db5f443)
![PointTracking](https://github.com/user-attachments/assets/fccfdc43-069c-4751-92b8-9145ad257ee0)
