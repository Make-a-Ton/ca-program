import cv2
import numpy as np


class FaceNotDetectedError(Exception):
    """Custom exception to raise when no face is detected."""

    def __init__(self, message="No face detected in the image."):
        self.message = message
        super().__init__(self.message)


def detect_head_and_crop_circle(image_path, diameter_fraction=1, target_size=None):
    """
    Detects a head in the image using face detection, crops the image into a circular region
    around the detected head, and returns the cropped image. The circle's diameter is based on
    a fraction of the image width. If the circle overflows the top or bottom of the image, adjust
    it to fit within the image boundaries.

    Parameters:
    - image_path: Path to the input image
    - diameter_fraction: Fraction of the image width to be used as the diameter of the circle
    - target_size: Desired size to resize the final image (int). If None, the image is not resized.

    Returns:
    - final_image: The circular cropped (and possibly resized) image centered on the detected head

    Raises:
    - FaceNotDetectedError: If no face is detected in the image
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image not found or unable to load image from the path: {image_path}")

    original_height, original_width = image.shape[:2]

    # Calculate the circle's diameter as a fraction of the image's width
    circle_diameter = int(original_width * diameter_fraction)
    radius = circle_diameter // 2

    # Convert the image to grayscale (Haar cascades work better on grayscale images)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Load the Haar Cascade classifier for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Detect faces (heads) in the image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
        # Raise custom exception if no faces are detected
        raise FaceNotDetectedError()

    # Assume we only care about the first detected face
    (x, y, w, h) = faces[0]

    # Calculate the center of the face/head
    center_x = x + w // 2
    center_y = y + h // 2

    # Check for top or bottom overflow and adjust the center_y
    if center_y - radius < 0:  # If the circle overflows the top
        center_y = radius  # Adjust to touch the top
    elif center_y + radius > original_height:  # If the circle overflows the bottom
        center_y = original_height - radius  # Adjust to touch the bottom
    # check for left or right overflow and adjust the center_x
    if center_x - radius < 0:  # If the circle overflows the left
        center_x = radius  # Adjust to touch the left
    elif center_x + radius > original_width:  # If the circle overflows the right
        center_x = original_width - radius  # Adjust to touch the right

    # Create a mask with the same dimensions as the original image
    mask = np.zeros((original_height, original_width), dtype=np.uint8)

    # Draw a white-filled circle on the mask based on the adjusted diameter and center
    cv2.circle(mask, (center_x, center_y), radius, (255, 255, 255), -1)

    # Create a circular cropped version of the original image
    circular_crop = cv2.bitwise_and(image, image, mask=mask)

    # Crop the square that bounds the circle
    left = max(center_x - radius, 0)
    right = min(center_x + radius, original_width)
    top = max(center_y - radius, 0)
    bottom = min(center_y + radius, original_height)
    cropped_image = circular_crop[top:bottom, left:right]

    # Resize the image to ensure the head is centered (optional)
    desired_size = max(cropped_image.shape[:2])
    final_image = cv2.copyMakeBorder(
        cropped_image,
        top=(desired_size - cropped_image.shape[0]) // 2,
        bottom=(desired_size - cropped_image.shape[0] + 1) // 2,
        left=(desired_size - cropped_image.shape[1]) // 2,
        right=(desired_size - cropped_image.shape[1] + 1) // 2,
        borderType=cv2.BORDER_CONSTANT,
        value=(0, 0, 0)  # Black padding
    )

    # Optionally resize the image to the target size
    if target_size is not None:
        final_image = cv2.resize(final_image, (target_size, target_size), interpolation=cv2.INTER_AREA)

    return final_image


# if __name__ == "__main__":
#     try:
#         # Path to the input image
#         input_image_path = "../test_images/IMG-20240713-WA0013.jpeg"
#
#         # Detect head and crop the image to a circle based on image width
#         # Specify the target_size if you want to resize the final image
#         target_size = 1000  # For example, resize the image to 256x256 pixels
#         masked_image = detect_head_and_crop_circle(input_image_path, diameter_fraction=1, target_size=target_size)
#
#         # Save and display the final result
#         output_path = "cropped_head_circle.png"
#         cv2.imwrite(output_path, masked_image)
#
#         # Display the circular cropped image
#         cv2.imshow("Cropped Head with Circle", masked_image)
#         cv2.waitKey(0)  # Wait until a key is pressed
#         cv2.destroyAllWindows()
#
#     except FaceNotDetectedError as e:
#         print(e)
#     except Exception as e:
#         print(f"An error occurred: {e}")
