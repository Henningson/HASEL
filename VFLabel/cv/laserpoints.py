import numpy as np


# Input is GRID_HEIGHT x GRID_WIDTH x 2 point tensor
def get_point_indices_from_tensor(point_positions: np.array) -> np.array:
    mask = ~np.isnan(point_positions).any(axis=-1)

    # Get x, y indices of valid points
    return np.argwhere(mask)


# Input is GRID_HEIGHT x GRID_WIDTH x 2 point tensor
def get_points_from_tensor(point_positions: np.array) -> np.array:
    point_positions = point_positions.reshape(-1, 2)
    return point_positions[~np.isnan(point_positions).any(axis=1)]
