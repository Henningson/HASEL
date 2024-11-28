import numpy as np
import matplotlib.pyplot as plt


def get_rgb_from_colormap(value, colormap_name="viridis"):
    """
    Get the RGB color from a Matplotlib colormap for a given value.

    Parameters:
        value (float): A value between 0 and 1 representing the position in the colormap.
        colormap_name (str): The name of the Matplotlib colormap to use (default is 'viridis').

    Returns:
        tuple: A tuple (r, g, b) with RGB values in the range [0, 1].
    """
    # Ensure the value is within the range [0, 1]
    value = np.clip(value, 0, 1)

    # Get the colormap
    colormap = plt.get_cmap(colormap_name)

    # Get the RGB color
    rgb_color = colormap(value)

    # Return only the RGB part, excluding the alpha channel
    return (rgb_color[:3] * 255).astype(np.uint8)
