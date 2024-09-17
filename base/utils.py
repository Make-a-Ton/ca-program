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
    # number = re.sub(r'^\+91', '', number)
    number = re.sub(r'\D', '', number)
    if not number.startswith('+91') or len(number) == 10:
        number = '+91' + number
    if number.startswith('91') and len(number) == 12:
        number = '+' + number[2:]


    # Ensure we only return the last 10 digits
    return number
