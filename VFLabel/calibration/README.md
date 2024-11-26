# Vocalfold 3D Reconstruction based on Endoscopic High Speed Video Recordings

This repository is an extension of the original calibration-tool based on a Camera-Laser System developed by the **UKE**.

Notable publications are:
>**3D Reconstruction of Human Laryngeal Dynamics Based on Endoscopic High-Speed Recordings** - Semmler et al.

>**Endoscopic Laser-Based 3D Imaging for Functional Voice Diagnostics** - Semmler et al.

It is depending on the following libraries:

 - [OpenCV](https://github.com/opencv/opencv) - Computer Vision Algorithms
 - [Ceres Solver](https://github.com/ceres-solver/ceres-solver) - Non-linear Optimization
 - [Eigen](https://eigen.tuxfamily.org/index.php?title=Main_Page) - C++ Template Library for Linear Algebra

# Installation
This installation is written for the **Windows** operating system, with **Visual Studio 19** as an exemplary IDE.
However, all of it's components are cross-platform compatible, so Unix or Mac OSX should be fine, as long as all of the dependencies (see above) are available.

## Preliminaries
- Download Visual Studio [here](https://visualstudio.microsoft.com/de/)
- Install [Qt](https://www.qt.io/), with **QTCore**, **QtDataVisualization**, **QtGUI** and **QtWidgets**.
- Install [Qt for Visual Studio 2019](https://marketplace.visualstudio.com/items?itemName=TheQtCompany.QtVisualStudioTools2019) from the Marketplace inside Visual Studio and close Visual Studio again.
(The current QT VS Tools Extension with Version 2.7.1.20 seems to be buggy, older versions can be found [here](https://download.qt.io/archive/vsaddin/).)
- Install vcpkg as explained [here](https://github.com/microsoft/vcpkg)

## Install dependencies
After downloading Visual Studio and vcpkg, use vcpkg to install the necessary dependencies.
Do not forget to add the system-dependent triplet (i.e. x64-windows) behind the package-name.
For example **opencv4:x64-windows**, or set a default triplet.

```
vcpkg install eigen3
vcpkg install opencv4
vcpkg install ceres
vcpkg integrate install
```

Now, open the provided **vocaloid++.sln** file and in Visual Studio, go to **Extensions** -> **Qt VS Tools** -> **Qt Versions** and specify the path to your Qt Installation (i.e. *C:\Qt\5.15.2\msvc2019_64*).
Now everything should be configured and ready to use. :-)

# Usage