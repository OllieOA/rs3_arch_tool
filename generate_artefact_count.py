from typing import List, Tuple

import cv2
from PIL import ImageGrab, Image, ImageFilter
import numpy as np

from artefact_image_utils import (
    ARTEFACT_LIST_FILE,
    ARTEFACT_PATH,
    convert_name_to_filename,
    download_images,
)

BANK_COLOR_RGB = (28, 47, 67)  # Assumption!
BANK_COLOR_TOLERANCE = 4
MIN_OBJECT_SIZE = 20
MAX_OBJECT_SIZE = 100

NORMALISED_OBJECT_SIZE = 64


def is_color_similar(color1, color2, tolerance):
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))


def find_artefact_bounding_boxes() -> List[Tuple[int, int, int, int]]:
    """
    Find the bounding boxes of artefacts in the image.
    Returns a list of tuples (x1, y1, x2, y2) for each artefact candidate.
    """
    bounding_boxes = []

    full_img = ImageGrab.grabclipboard()
    if full_img is None:
        raise ValueError("No image found in clipboard.")

    # First we will find the best base bank-coloured pixel in the image
    # Assume that the bank interface is in the middle of the screen
    width, height = full_img.size
    target_pixel = (width // 2, height // 2)

    pixel_color = full_img.getpixel(target_pixel)
    while not is_color_similar(pixel_color, BANK_COLOR_RGB, BANK_COLOR_TOLERANCE):
        target_pixel = (target_pixel[0] + 1, target_pixel[1])  # Move in a line until pixel is found

    # Now we will start marking all pixels in a flood fill that match the colour

    bank_pixels = set()
    pixels_to_check = [target_pixel]
    checked_pixels = set()

    while len(pixels_to_check) > 0:
        pixel = pixels_to_check.pop()
        if pixel in checked_pixels:
            continue

        checked_pixels.add(pixel)
        pixel_color = full_img.getpixel(pixel)

        if is_color_similar(pixel_color, BANK_COLOR_RGB, BANK_COLOR_TOLERANCE):
            bank_pixels.add(pixel)

            # Check the 4 adjacent pixels
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                new_pixel = (pixel[0] + dx, pixel[1] + dy)
                if 0 <= new_pixel[0] < width and 0 <= new_pixel[1] < height:
                    pixels_to_check.append(new_pixel)

    # Now we can make a mask of the bank pixels to isolate the objects with
    # bounding boxes around the black smudges

    mask = Image.new("L", full_img.size, 255)
    for pixel in bank_pixels:
        mask.putpixel(pixel, 0)

    mask = np.array(mask, dtype=np.uint8)
    mask_check = mask.copy()
    mask_check = cv2.cvtColor(mask_check, cv2.COLOR_GRAY2BGR)

    contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours[0]:
        x, y, w, h = cv2.boundingRect(contour)
        if any(
            [w < MIN_OBJECT_SIZE, h < MIN_OBJECT_SIZE, w > MAX_OBJECT_SIZE, h > MAX_OBJECT_SIZE]
        ):
            continue
        bounding_boxes.append((x, y, w, h))

    def normalise_box(box: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        center_x = box[0] + box[2] // 2
        center_y = box[1] + box[3] // 2

        new_x = int(center_x - NORMALISED_OBJECT_SIZE // 2)
        new_y = int(center_y - NORMALISED_OBJECT_SIZE // 2)
        new_w = NORMALISED_OBJECT_SIZE
        new_h = NORMALISED_OBJECT_SIZE

        return new_x, new_y, new_w, new_h

    normalised_bounding_boxes = [normalise_box(box) for box in bounding_boxes]

    return normalised_bounding_boxes


def main():
    download_images()

    bounding_boxes = find_artefact_bounding_boxes()
    if bounding_boxes is None:
        print("No artefacts found.")
        return

    all_artefact_images = {str(x): Image.open(x) for x in ARTEFACT_PATH.glob("*.png")}

    for k, v in all_artefact_images.items():
        print(k, v)
        raise

    counts = {x: {"normal": 0, "damaged": 0} for x in sorted(all_artefact_images.keys())}


if __name__ == "__main__":
    main()
