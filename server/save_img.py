import base64


def extract_base64_from_data_uri(data_uri: str) -> str:
    """
    Extracts the base64-encoded content from a data URI.
    Args:
        data_uri (str): A string expected to be in the format 'data:[<mediatype>][;base64],<data>'.
    Returns:
        str: The base64-encoded data portion of the URI. If no comma is present,
             returns the input as-is.
    """
    if not isinstance(data_uri, str):
        raise TypeError("Expected a string as data_uri")

    if "," not in data_uri:
        return data_uri

    return data_uri.split(",", 1)[1]

def save_base64_image(base64_string: str, output_file_path: str):
    """
    Saves a base64-encoded image to a file.

    :param base64_string: The base64-encoded image string (e.g., request.image).
    :param output_file_path: The path where the image will be saved (e.g., "output.jpg").
    """
    try:
        # Split the base64 string to remove the header (e.g., "data:image/jpeg;base64,")
        # Assume it's already just the base64 data
        base64_data = extract_base64_from_data_uri(base64_string)
        # Decode the base64 string into binary data
        image_data = base64.b64decode(base64_data)

        # Save the binary data to the specified file
        with open(output_file_path, "wb") as file:
            file.write(image_data)

        print(f"Image saved successfully to {output_file_path}")

    except Exception as e:
        print(f"Error saving image: {str(e)}")


def img_to_base64(file_path: str):
    try:
        # Open the PNG file in binary mode
        with open(file_path, "rb") as image_file:
            # Read the binary data of the image
            image_data = image_file.read()

            # Encode the binary data to Base64
            base64_encoded = base64.b64encode(image_data)

            # Convert the Base64 bytes to a UTF-8 string (optional)
            base64_string = base64_encoded.decode("utf-8")

            return base64_string

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
