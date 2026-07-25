How to use this code block
=========================================================================================

Description
-------------------------
This document provides a comprehensive guide on how to use the `GoogleGenerativeAI` class for interacting with Google's Gemini models. It outlines the features of the class, setup instructions, usage examples, and details on how to utilize the various methods for text generation, chat, image description, and file upload. It also covers error handling, logging, and chat history management.

Execution steps
-------------------------
1. **Overview**:
    - Explains that the project provides `GoogleGenerativeAI` class for interacting with Google Gemini AI models.
    - Lists the main features of the project, such as different Gemini models support, chat history saving, error handling, and customizable parameters.

2. **Requirements**:
    - Specifies Python 3.7 or higher as a requirement.
    - Lists necessary Python libraries: `google-generativeai`, `requests`, `grpcio`, `google-api-core`, and `google-auth`.
    - Notes the need for a valid Google Gemini API key.

3. **Installation**:
    - Provides instructions on cloning the repository: `git clone <repository_url>`, `cd <repository_directory>`.
    - Instructs users to install dependencies using pip: `pip install -r requirements.txt`.
    - Explains how to create or adjust `config.json` file with API key and other settings and provides sample json config.

4. **Usage**:
    - **Initialization**: Shows how to import `GoogleGenerativeAI` and `gs` and initialize the class with an API key and system instruction.
    - **`GoogleGenerativeAI` class methods**:
        -   **`__init__`**: Describes the initialization method with parameters like `api_key`, `model_name`, `generation_config`, and `system_instruction`.
        -   **`ask(q: str, attempts: int = 15) -> Optional[str]`**: Explains the method for sending a text query and receiving a response, including retry attempts.
        -   **`chat(q: str) -> Optional[str]`**: Describes the chat method that maintains the conversation history and provides response from Gemini model.
        -   **`describe_image(image: Path | bytes, mime_type: Optional[str] = 'image/jpeg', prompt: Optional[str] = '') -> Optional[str]`**: Explains the method for describing an image with optional `mime_type` and a text `prompt`.
        -   **`upload_file(file: str | Path | IOBase, file_name: Optional[str] = None) -> bool`**: Describes the method for uploading a file to the Gemini API.

5.  **Usage Example**:
    - Provides a comprehensive code example demonstrating how to use the class for image description, file upload, and interactive chat.
    - The example includes:
        - Initializing `GoogleGenerativeAI`.
        - Handling the image path and checking the file existence.
        - Using `describe_image` with JSON-formatted prompt and without.
        - Using `upload_file` for uploading text files.
        - Interactive chat loop with the model.

6. **Additional Information**:
    - **Logging**: Mentions that all dialogues and errors are logged in files located in `external_storage/gemini_data`.
    - **Chat history**: Notes that the chat history is stored in `external_storage/gemini_data/history/` in JSON and text formats.
    - **Error handling**: Points out that the program is designed to handle network, authentication, and API errors using retry mechanisms.

7. **Notes**:
    - Emphasizes the need to replace `gs.credentials.gemini.api_key` with a valid API key.
    - Reminds users to install required libraries and make sure `test.jpg` exist in the root folder.

8. **License**:
    - Indicates that the project is distributed under the MIT License.
9. **Author**:
    - Provides the author's name: `hypo69`.

Usage example
-------------------------
.. code-block:: python

    # Import necessary modules for the API usage
    import asyncio
    from pathlib import Path
    from src.ai.gemini.generative_ai import GoogleGenerativeAI
    from src.utils.jjson import j_loads
    import gs


    # Initialize the GoogleGenerativeAI class with your API key, and system instruction.
    system_instruction = "You are a helpful assistant. Answer all questions concisely."
    ai = GoogleGenerativeAI(api_key=gs.credentials.gemini.api_key, system_instruction=system_instruction)  # Replace with your API key

    async def main():
        # Example usage for image description
        image_path = Path(r"test.jpg")
        if not image_path.is_file():
             print(
                f"File {image_path} not found. Please put a file named 'test.jpg' in the program's root folder."
            )
        else:
            # Example with JSON format prompt
            prompt = """Analyze this image. Provide a JSON formatted response,
            where the key is the object name and the value is its description.
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
            
            # Example without JSON formatted prompt
            prompt = "Analyze this image. List all objects that you can recognize."
            description = await ai.describe_image(image_path, prompt=prompt)
            if description:
                print("Image description (without JSON format):")
                print(description)
        
        # Example usage of uploading file function.
        file_path = Path('test.txt')
        with open(file_path, "w") as f:
            f.write("Hello, Gemini!")
        file_upload = await ai.upload_file(file_path, 'test_file.txt')
        print(file_upload)

        # Interactive chat loop with Gemini model.
        while True:
            user_message = input("You: ")
            if user_message.lower() == 'exit':
                break
            ai_message = await ai.chat(user_message)
            if ai_message:
                print(f"Gemini: {ai_message}")
            else:
                print("Gemini: Error getting response")


    if __name__ == "__main__":
        asyncio.run(main())