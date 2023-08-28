from PIL import Image
import numpy as np

# Define RGB values for the four colors
colors = {
    "grey": (128, 128, 128),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "brown": (165, 42, 42),
}


def find_nearest_color(pixel):
    min_distance = float("inf")
    nearest_color = None

    for color_name, color_rgb in colors.items():
        distance = np.sqrt(np.sum((np.array(pixel) - np.array(color_rgb)) ** 2))
        if distance < min_distance:
            min_distance = distance
            nearest_color = color_name

    return nearest_color


def get_main_color(image_path):
    img = Image.open(image_path)
    img.thumbnail((1000, 1000))
    img_array = np.array(img)
    color_counts = {color: 0 for color in colors}
    for row in img_array:
        for pixel in row:
            nearest_color = find_nearest_color(pixel)
            color_counts[nearest_color] += 1

    sorted_color_counts = sorted(color_counts.items(), key=lambda x: x[1])
    primary_color = sorted_color_counts[-1]
    return primary_color[0]
