import re


def clean_mobile_number(number):
    """
    Cleans a mobile number by:
    - Removing extra spaces
    - Trimming leading and trailing spaces
    - Removing the country code (e.g., +91)
    - Returning only the final 10-digit number

    Args:
    - number (str): The mobile number to clean.

    Returns:
    - str: The cleaned 10-digit mobile number.
    """
    # Remove extra spaces and trim
    number = number.strip()

    # Remove country code (+91) and other non-digit characters
    number = re.sub(r'^\+91', '', number)
    number = re.sub(r'\D', '', number)

    # Ensure we only return the last 10 digits
    return number[-10:]
