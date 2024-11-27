![hasel](https://github.com/user-attachments/assets/eac052b4-affd-4f99-9758-9b05f36ca074)
#
**HASEL** (**H**igh-Speed Video **A**nnotation Tool for **S**tructured Light **E**ndoscopy in the Human **L**arynx) is a Deep-Learning-supported tool for generating ground-truth data for High-Speed Video Structured Light Laryngoscopy.
This tool enables to robustly and rapidly generate data of:
* Glottal segmentation with different segmentation architectures
* Vocal fold segmentation via frame-wise interpolation
* Semi-automatic and Deep Learning enhanced generation of laserpoint data.

# Installation

Install requirements
```
conda create --name VFLabel python=3.12
pip install torch torchvision torchaudio
conda install pyqt qtpy
pip install torchmetrics albumentations imageio kornia segmentation-models-pytorch

```

Install VFLabel for **development**:
```
git clone https://github.com/Henningson/VFLabel.git
cd VFLabel
python3 -m pip install -e .
```

Install VFLabel for **general usage**:
```
git clone https://github.com/Henningson/VFLabel.git
cd VFLabel
pip install .
```
  
Next, download the glottis segmentation networks from [here](https://drive.google.com/drive/folders/1U525TcxZ1nhIp5yNJiyW-avK6qZG4rVV?usp=sharing) and move them to ```assets/test_data/```.

# How to use VFLabel (TODO)
Hier könnte ihre Werbung stehen.



# Regarding the Glottal Segmentation
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

| Backbone | Eval IoU | Eval DICE | Test IoU | Test Dice |
|----------|----------|----------|----------|----------|
| mobilenet-v2             | 0.864   | 0.927   | 0.893  | 0.807   |
| mobilenetv3_large_100    | 0.845   | 0.916  | 0.789  | 0.65  |
| resnet18                 | TODO  | Data 14  | Data 15  | Data 16  |
| resnet34                 | TODO  | Data 18  | Data 19  | Data 20  |




# Train your own glottal segmentation net.

## Data preparation
