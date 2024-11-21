# Laser-Based Structured Light Data Labelling Tool

This is a small tool that I programmed to efficiently label data for a classification task.  
This was made for Structured Light data, but can be easily repurposed for arbitrary images.  
Don't expect anything too much here, lol.

<img src="https://github.com/Henningson/FastLabeling/assets/27073509/4262716b-e2c4-412e-9d9d-dec24b416358" width="200">

## Installation

To get started with the labelling tool, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Henningson/FastLabeling.git
    cd FastLabeling
    ```

2. **Install dependencies**:
    ```bash
    pip install numpy pyqt5 opencv-python
    ```

3. **Run the tool**:
    ```bash
    python main.py
    ```

## Key-Bindings

- `1` - Label as Laserpoint
- `2` - Label as Specular Highlight
- `3` - Label as Other

Labels are then highlighted in the following colors:
- 🟩 Laserpoint
- 🟥 Specular Highlight
- 🟦 Other
- ⬛ Not yet labeled

## Usage

1. **Open Image Folder**:
    - Use the dropdown menu to navigate to and select the folder containing your images.

2. **Label Images**:
    - Use the key-bindings (`1`, `2`, `3`) to label images as Laser Dot, Specular Highlight, or Other. The GUI will automatically advance to the next image after each label is applied.

3. **Save Progress**:
    - Use the save dropdown to save your current labelling progress to a specified path.

4. **Generate Dataset**:
    - Use the generate dataset option to split your labelled data into train, validation, and test sets (80/10/10 split). Note that unlabeled data is ignored in this step. The split can be changed in the code itself.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
