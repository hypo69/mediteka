# Module generative_ai

## Overview

This module provides integration with Google's Generative AI, offering functionalities such as text generation, image description, and file uploading.

## Table of Contents

- [Functions](#functions)
- [Classes](#classes)

## Functions

### `normalize_text`

**Description**: Normalizes the input text by replacing escaped sequences.

**Parameters**:
- `text` (str): The input text.

**Returns**:
- `str`: The normalized text.

### `remove_html_blocks`

**Description**: Removes HTML blocks enclosed in `\`\`\`html` and `\`\`\`` or `\`\`\`\
`.

**Parameters**:
- `text` (str): The input text.

**Returns**:
- `str`: The text with HTML blocks removed.

## Classes

### `GoogleGenerativeAI`

**Description**: A class for interacting with Google Generative AI models.

**Attributes**:
- `api_key` (str): The API key for accessing Google Generative AI services.
- `model_name` (str): The name of the model to use (default: "gemini-2.0-flash-exp").
- `generation_config` (Dict): Configuration settings for the model (default: `{"response_mime_type": "text/plain"}`).
- `system_instruction` (Optional[str]): An optional instruction to give the model at the start of the conversation.
- `dialogue_log_path` (Path): The path to the directory where dialogue logs are stored.
- `dialogue_txt_path` (Path): The path to the text file where dialogue logs are stored.
- `history_dir` (Path): The path to the directory where chat histories are stored.
- `history_txt_file` (Path): The path to the text file where chat histories are stored.
- `history_json_file` (Path): The path to the JSON file where chat histories are stored.
- `chat_history` (List[Dict]): A list storing the chat history.
- `model` (Any): The Google Generative AI model.
- `_chat` (Any): The chat object.
- `MODELS` (List[str]): A list of available models.

**Methods**:

#### `__post_init__`
**Description**: Initializes the `GoogleGenerativeAI` instance.

#### `_start_chat`
**Description**: Starts a new chat session with optional system instructions.

#### `clear_history`
**Description**: Clears the chat history.

#### `_save_chat_history`
**Description**: Saves chat history to a JSON file.

**Parameters**:
- `chat_data_folder` (Optional[str | Path]): The folder where to save the chat history.

#### `_load_chat_history`
**Description**: Loads chat history from a JSON file.

**Parameters**:
- `chat_data_folder` (Optional[str | Path]): The folder where to load the chat history from.

#### `chat`
**Description**: Processes a chat query with different history management modes.

**Parameters**:
- `q` (str): The user's query.
- `chat_data_folder` (Optional[str | Path]): The folder for chat history storage.
- `flag` (str): The chat history mode ("save_chat", "read_and_clear", "clear", "start_new").

**Returns**:
- `Optional[str]`: The model's response, or `None` on failure.

#### `ask`
**Description**: Sends a text query to the model and returns the response.

**Parameters**:
- `q` (str): The user's query.
- `attempts` (int): Number of attempts to send the query. Defaults to 15.

**Returns**:
- `Optional[str]`: The model's response, or `None` on failure.

#### `describe_image`
**Description**: Sends an image to the Gemini Pro Vision model for a textual description.

**Parameters**:
- `image` (Path | bytes): The path to the image or image bytes.
- `mime_type` (Optional[str]): The MIME type of the image. Defaults to `image/jpeg`.
- `prompt` (Optional[str]): A prompt for describing the image. Defaults to ''.

**Returns**:
- `Optional[str]`: The model's textual description, or `None` on failure.

#### `upload_file`
**Description**: Uploads a file to Google's generative AI service.

**Parameters**:
- `file` (str | Path | IOBase): Path to the file or an IO stream.
- `file_name` (Optional[str]): The name of the file.

**Returns**:
- `bool`: `True` if the file is uploaded successfully, `None` otherwise.

### `main`

**Description**: The main function that demonstrates the use of the `GoogleGenerativeAI` class.
```
## Changes
No changes were required to the provided `input_code`. The documentation was created based on the file path, structure, and inline comments. All functions and classes have been documented according to the specifications.