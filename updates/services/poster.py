import cv2
import numpy as np
from PIL import Image, ImageDraw

from updates.services.face_with_target_size import detect_head_and_crop_circle


class PosterTemplate:
    """
    Represents the poster template with a circular space for a headshot.
    """

    def __init__(self, base_image_path, circle_diameter, center_coordinates):
        """
        Initialize the Poster with the base image, circle diameter, and center coordinates.

        Parameters:
        - base_image_path: Path to the base poster image
        - circle_diameter: Diameter of the circle where the head will be placed
        - center_coordinates: (x, y) coordinates for the top-left corner where the head will be placed
        """
        # Load the base poster image
        self.base_image = Image.open(base_image_path).convert("RGBA")
        self.circle_diameter = circle_diameter
        self.center_coordinates = center_coordinates

    def place_head(self, head_image_path):
        """
        Places a person's head onto the self in the designated circular area.

        Parameters:
        - poster: A Poster object representing the base poster
        - head_image_path: Path to the image containing the person's head

        Returns:
        - result_image: The final image with the head placed on the poster
        """
        # Use the previous function to crop the head to a circle
        # We will assume detect_head_and_crop_circle exists and is working
        cropped_head_resized = detect_head_and_crop_circle(
            head_image_path, diameter_fraction=0.5, target_size=self.circle_diameter
        )

        # Convert OpenCV image (BGR) to PIL image (RGBA)
        cropped_head_resized_rgb = cv2.cvtColor(cropped_head_resized, cv2.COLOR_BGR2RGB)
        cropped_head_pil = Image.fromarray(cropped_head_resized_rgb).convert("RGBA")

        # Create an alpha mask (circle)
        width, height = cropped_head_pil.size
        alpha_mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(alpha_mask)
        draw.ellipse((0, 0, width, height), fill=255)

        # Add alpha channel to the image using the mask
        cropped_head_pil.putalpha(alpha_mask)

        # Prepare the result image by copying the base poster
        result_image = self.base_image.copy()

        # Paste the head onto the poster using the alpha channel as mask
        result_image.paste(
            cropped_head_pil, self.center_coordinates, mask=cropped_head_pil
        )

        return result_image


# if __name__ == "__main__":
#     # Example usage
#     # You can adjust these values based on your specific poster and head position
#
#     # Initialize the poster with its base image, circle diameter, and head position
#     poster = Poster(
#         base_image_path="updates/static/imparticipating.png",
#         circle_diameter=780,
#         center_coordinates=(175, 875),  # Top-left corner where the head will be placed
#     )
#
#     # Place the person's head on the poster
#     final_image = place_head_on_poster(poster, head_image_path="../sreya.jpg")
#
#     # Show or save the resulting image
#     show_image(final_image)
#     # save_image(final_image, "final_poster_with_head.png")
