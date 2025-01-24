import numpy as np
import cv2
from typing import List
from scipy.optimize import curve_fit


def gaussian_2d(xy, x0, y0, sigma) -> np.array:
    x, y = xy
    return (
        255
        * np.exp(
            -(((x - x0) ** 2) / (2 * sigma**2) + ((y - y0) ** 2) / (2 * sigma**2))
        ).ravel()
    )


def fit_gaussian_2d(
    images: List[np.array], initial_sigma_guess: float = 5
) -> List[np.array]:
    param_list = []
    for image in images:

        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        image = image.astype(float)

        x = np.arange(image.shape[1])
        y = np.arange(image.shape[0])
        x, y = np.meshgrid(x, y)
        x_data = np.vstack((x.ravel(), y.ravel()))
        y_data = image.ravel()

        argmax = np.unravel_index(image.argmax(), image.shape)

        # Initial guess for the parameters: amplitude, x0, y0, sigma_x, sigma_y
        initial_guess = [argmax[1], argmax[0], initial_sigma_guess]

        # Fit the 2D Gaussian to the image
        params, _ = curve_fit(
            gaussian_2d, x_data, y_data, p0=initial_guess, maxfev=5000
        )

        param_list.append(params)

    return param_list


def generate_gaussian_2d_from_params(
    images: List[np.array], param_list: List[np.array]
) -> List[np.array]:
    gaussian_images = []
    for image, params in zip(images, param_list):
        x = np.arange(image.shape[1])
        y = np.arange(image.shape[0])
        x, y = np.meshgrid(x, y)
        x_data = np.vstack((x.ravel(), y.ravel()))

        fitted_image = gaussian_2d(x_data, *params).reshape(image.shape)
        gaussian_images.append(fitted_image)

    return gaussian_images
