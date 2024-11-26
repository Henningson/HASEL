![hasel](https://github.com/user-attachments/assets/eac052b4-affd-4f99-9758-9b05f36ca074)
#
**HASEL** (**H**igh-Speed Video **A**nnotation Tool for **S**tructured Light **E**ndoscopy in the Human **L**arynx) is a Deep-Learning-supported tool for generating ground-truth data for High-Speed Video Structured Light Laryngoscopy.
This tool enables to robustly and rapidly generate data of:
* Glottal segmentation with different segmentation architectures
* Vocal fold segmentation via frame-wise interpolation
* Semi-automatic and Deep Learning enhanced generation of laserpoint data.

# Installation (TODO)

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

# How to use VFLabel (TODO)
Hier könnte ihre Werbung stehen.
