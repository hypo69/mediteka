How to use this code block
=========================================================================================

Description
-------------------------
This code block implements a class `GoogleGenerativeAI` for interacting with Google's Gemini models. It supports text generation, chat functionality with history management, image description, and file uploading. The code also includes error handling, logging, and utility functions for text normalization and JSON processing. The `main` function provides usage examples for all the capabilities.

Execution steps
-------------------------
1.  **Import necessary modules**: Import modules for file handling, asynchronous operations, data classes, Google AI, and project-specific utilities.
2.  **Define `normalize_text` function**:  This function normalizes text by converting escape sequences to their corresponding characters.
3.  **Define `remove_html_blocks` function**: This function removes HTML blocks enclosed within `\`\`\`html`\`\`\` tags from a given text.
4.  **Define `GoogleGenerativeAI` dataclass**:
    -   **Initialization (`__post_init__`)**: Initializes the Gemini model, sets up file paths for dialogue logs and chat history, and starts a new chat session.
    -   **`_start_chat`**: Initializes a new chat session with or without a system instruction.
    -   **`clear_history`**: Clears the chat history in memory and deletes the history file.
    -   **`_save_chat_history`**: Saves the chat history to a JSON file.
    -   **`_load_chat_history`**: Loads chat history from a JSON file.
    -   **`chat`**: Sends a chat message to the model, handles different chat history management modes ("save_chat", "read_and_clear", "clear", "start_new"), and returns the model's response.
    -   **`ask`**: Sends a text query to the model, retries on errors, and returns the response, also saves a log of conversations.
    -    **`describe_image`**: Sends an image to the model and returns a text description, also with prompt functionality.
    -   **`upload_file`**: Uploads a file to the Gemini service.
5.  **Define `main` function**:
    -   **Initialize `GoogleGenerativeAI`**: Create an instance of `GoogleGenerativeAI` with the API key and system instructions.
    -   **Image Description Example**: Call `describe_image` with an image path, including a JSON structured response, and then a plain text response.
    -   **File Upload Example**: Call `upload_file` to upload a text file to Gemini.
    -   **Chat Example**: Start a loop to interactively chat with the model via terminal input.
6.  **Run `main`**: Execute the main function in an asynchronous environment when the script is run directly.

Usage example
-------------------------
.. code-block:: python

    import asyncio
    import time
    from pathlib import Path
    import google.generativeai as genai
    from src.utils.jjson import j_loads
    from src.ai.gemini.generative_ai import GoogleGenerativeAI

    async def main():
        # Initialize the GoogleGenerativeAI class with your API key
        system_instruction = "You are a helpful assistant. Answer all questions concisely."
        ai = GoogleGenerativeAI(api_key="YOUR_API_KEY", system_instruction=system_instruction)  # Replace with your API key

        # Image description example
        image_path = Path("test.jpg")
        if not image_path.is_file():
            print(f"File {image_path} not found. Please put a file named 'test.jpg' in the program's root folder.")
        else:
            # Example with JSON structured prompt
            prompt = """Analyze this image. Provide a JSON formatted response,
            where the key is the object name and the value is its description.
             If there are people, describe their actions."""
            description = await ai.describe_image(image_path, prompt=prompt)
            if description:
                print("Image description (with JSON format):")
                print(description)
                try:
                    parsed_description = j_loads(description) # parse json
                except Exception:
                    print("Failed to parse JSON. Received text:")
                    print(description)
            else:
                print("Failed to get image description.")

            # Example with plain text prompt
            prompt = "Analyze this image. List all objects that you can recognize."
            description = await ai.describe_image(image_path, prompt=prompt)
            if description:
                print("Image description (without JSON format):")
                print(description)

        # File upload example
        file_path = Path('test.txt')
        with open(file_path, "w") as f:
            f.write("Hello, Gemini!")
        file_upload = await ai.upload_file(file_path, 'test_file.txt')
        print(file_upload)

        # Chat example
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