# Google Gemini API Integration

This project provides the `GoogleGenerativeAI` class for interacting with Google Generative AI models (Gemini). It allows sending text requests, conducting dialogues, describing images, and uploading files using the Google Gemini API.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Initialization](#initialization)
  - [Methods of `GoogleGenerativeAI` Class](#methods-of-google-generativeai-class)
  - [Usage Example](#usage-example)
- [Additional Information](#additional-information)
- [Remarks](#remarks)
- [License](#license)
- [Author](#author)

## Features

- Support for various Gemini models.
- Saving dialogue history to JSON and text files.
- Working with text, images, and files.
- Error handling with retry mechanisms.
- Ability to configure generation parameters and system instructions.
- Usage example in `main()` with loading and reading images and files, as well as with interactive chat.

## Requirements

- Python 3.7 or higher
- Installed libraries:
  - `google-generativeai`
  - `requests`
  - `grpcio`
  - `google-api-core`
  - `google-auth`
- Valid Google Gemini API key (replace `gs.credentials.gemini.api_key` with your own)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Create or configure the configuration file:**

    In `/src/ai/gemini/config.json` you can place the settings that will be required for your work.
    Example:

    ```json
    {
        "api_key": "YOUR_API_KEY",
        "model_name": "gemini-2.0-flash-exp",
        "generation_config": {
            "response_mime_type": "text/plain"
        }
    }
    ```
    
    **Note:** The API key must be replaced with your own.

## Usage

### Initialization

```python
from src.ai.gemini import GoogleGenerativeAI
import gs

system_instruction = "You are a helpful assistant. Answer all questions briefly"
ai = GoogleGenerativeAI(api_key=gs.credentials.gemini.api_key, system_instruction=system_instruction)
```

### Methods of `GoogleGenerativeAI` Class

- **`__init__(api_key: str, model_name: str = "gemini-2.0-flash-exp", generation_config: Dict = None, system_instruction: Optional[str] = None)`:**
    - Initializes a `GoogleGenerativeAI` object with an API key, model name, and generation settings.
    - The `system_instruction` parameter allows you to specify system instructions for the model.

- **`ask(q: str, attempts: int = 15) -> Optional[str]`:**
    - Sends a text query `q` to the model and returns a response.
    - `attempts` - the number of attempts if the query fails.

- **`chat(q: str) -> Optional[str]`:**
    - Sends a query `q` to the chat, maintaining the dialogue history.
    - Returns the model's response.
    - The chat history is saved in a JSON file.

- **`describe_image(image: Path | bytes, mime_type: Optional[str] = 'image/jpeg', prompt: Optional[str] = '') -> Optional[str]`:**
    - Describes an image sent as a file path or bytes.
    - `image`: the path to the image file or image bytes.
    - `mime_type`: the MIME type of the image.
    - `prompt`: a text prompt for describing the image.
    - Returns a textual description of the image.

- **`upload_file(file: str | Path | IOBase, file_name: Optional[str] = None) -> bool`:**
    - Uploads a file to the Gemini API.
    - `file`: the path to the file, file name, or file object.
    - `file_name`: the file name for the Gemini API.

### Usage Example

```python
import asyncio
from pathlib import Path

# Replace with your API key
system_instruction = "You are a helpful assistant. Answer all questions briefly"
ai = GoogleGenerativeAI(api_key=gs.credentials.gemini.api_key, system_instruction=system_instruction)

async def main():
    # Example of calling describe_image with a prompt
    image_path = Path(r"test.jpg")  # Replace with the path to your image

    if not image_path.is_file():
        print(
            f"File {image_path} does not exist. Place a file named test.jpg in the root folder with the program"
        )
    else:
        prompt = """Analyze this image. Return the answer in JSON format,
        where the key will be the name of the object, and the value will be its description.
         If there are people, describe their actions."""

        description = await ai.describe_image(image_path, prompt=prompt)
        if description:
            print("Image description (with JSON format):")
            print(description)
            try:
                parsed_description = j_loads(description)

            except Exception as ex:
                print("Failed to parse JSON. Received text:")
                print(description)

        else:
            print("Failed to get image description.")

        # Example without JSON output
        prompt = "Analyze this image. List all the objects you can recognize."
        description = await ai.describe_image(image_path, prompt=prompt)
        if description:
            print("Image description (without JSON format):")
            print(description)

    file_path = Path('test.txt')
    with open(file_path, "w") as f:
        f.write("Hello, Gemini!")

    file_upload = await ai.upload_file(file_path, 'test_file.txt')
    print(file_upload)

    # Example of chat
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            break
        ai_message = await ai.chat(user_message)
        if ai_message:
            print(f"Gemini: {ai_message}")
        else:
            print("Gemini: Error getting a response")

if __name__ == "__main__":
    asyncio.run(main())
```

## Additional Information

- **Logging:** All dialogues and errors are recorded in the corresponding files in the `external_storage/gemini_data` directory.
- **Chat History:** The dialogue history is stored in JSON and text files in the `external_storage/gemini_data/history/` directory.
- **Error Handling:** The program handles network errors, authentication errors, and API errors with a retry mechanism.

## Remarks

- Be sure to replace `gs.credentials.gemini.api_key` with your valid Google Gemini API key.
- Make sure you have `google-generativeai`, `requests`, `grpcio`, `google-api-core`, and `google-auth` installed.
- Make sure you have a `test.jpg` file in the root folder with the program or change the image path in the `main` example.

## License

This project is distributed under the [MIT] license.

## Author

[hypo69]
```
## Changes
No changes were required to the provided `input_code`. The documentation was created based on the file path, structure, and inline comments. All required sections have been documented.