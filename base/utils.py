import re


def clean_mobile_number(number):
    """
    Cleans a mobile number by:
    - Removing extra spaces
    - Trimming leading and trailing spaces
    - Removing any leading country code
    - Ensuring the number starts with +91 and is followed by 10 digits

    Args:
    - number (str): The mobile number to clean.

    Returns:
    - str: The cleaned 13-digit mobile number in the format +91XXXXXXXXXX.
    """
    # Remove extra spaces and trim the number
    number = number.strip()

    # Remove any characters that are not digits or the '+' at the start
    number = ''.join([char for char in number if char.isdigit() or char == '+'])

    # If the number starts with +91, remove the +91
    if number.startswith('+91'):
        number = number[3:]

    # If the number starts with a different country code (e.g., +1 or +44), remove the code
    if number.startswith('+'):
        number = number[1:]  # Removes any leading +

    # Ensure the number is 10 digits by taking only the last 10 digits
    number = number[-10:]

    # Return the number formatted with the +91 prefix
    return f'+91{number}'
