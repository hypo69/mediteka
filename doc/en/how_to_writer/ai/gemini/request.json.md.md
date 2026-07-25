How to use this code block
=========================================================================================

Description
-------------------------
This JSON block defines the structure of a request object for interacting with Google's Gemini API. It specifies the format for providing content, system instructions, tool definitions, safety settings, generation configurations, and labels. This structure serves as a template for creating requests to the Gemini models, allowing for various customization options.

Execution steps
-------------------------
1.  **`cachedContent`**: This field, a string, holds cached content (if any).
2.  **`contents`**: This is an array of content objects. Each object represents a turn in the conversation.
    -   **`role`**: The role of the content's author (e.g., "user", "model").
    -   **`parts`**: An array containing different parts of the content. Each part can have one of the following types:
        -   **`text`**: A plain text string.
        -   **`inlineData`**: An inline data object, containing:
            -   `mimeType`: The MIME type of the data (e.g., "image/jpeg").
            -   `data`: The base64 encoded data string.
        -  **`fileData`**: Data that represents the a file, containing:
             -   `mimeType`: The MIME type of the file (e.g., "text/plain").
             -   `fileUri`: The link to file.
        - **`videoMetadata`**: An object that contains meta data for video content
            - **`startOffset`**: An object that specifies starting offset of video
                 -  `seconds`: The starting point of the video in seconds.
                 -  `nanos`: Nanoseconds part of the starting point.
            -  **`endOffset`**: An object that specifies ending offset of video
                 -  `seconds`: The ending point of the video in seconds.
                 -  `nanos`: Nanoseconds part of the ending point.
3.  **`systemInstruction`**: An object defining system instructions that model should follow.
    -   **`role`**: Specifies the role for this instruction (e.g., "system").
    -   **`parts`**: An array of content parts. Each part in this case should be a string with the instruction.
4.  **`tools`**: This is an array of tool objects. Each object describes a tool that the model can use.
    -   **`functionDeclarations`**: An array of function declarations that define the functions of available tools.
        -   **`name`**: The name of the function.
        -   **`description`**: A textual description of the function.
        -   **`parameters`**: An object describing the function's parameters.
5.  **`safetySettings`**: An array of safety setting objects.
    -   **`category`**: Category of the safety setting (enum).
    -   **`threshold`**: The threshold for the safety setting (enum).
6.  **`generationConfig`**: An object describing the configuration of the model generation:
    -   **`temperature`**: Controls the randomness of the output.
    -   **`topP`**: Nucleus sampling parameter for top-p sampling.
    -   **`topK`**: Top-k sampling parameter for top-k sampling.
    -   **`candidateCount`**: The number of candidate responses to generate.
    -   **`maxOutputTokens`**: The maximum number of tokens for the output.
    -    **`presencePenalty`**: Affects probability of existing tokens in prompt.
    -    **`frequencyPenalty`**: Affects probability of frequent tokens in prompt.
    -   **`stopSequences`**: An array of sequences where the model stops generating.
    -   **`responseMimeType`**: The MIME type of the response (e.g., "text/plain").
    -   **`responseSchema`**: Schema for the output of model.
    -   **`seed`**: Integer to control randomness.
     -   **`responseLogprobs`**: Enables output of token probabilities
    -   **`logprobs`**: Numbers of logprobs in output.
    -   **`audioTimestamp`**: Enables output of audio timestamp.
7.  **`labels`**: Key-value pairs for labeling the request.

Usage example
-------------------------
.. code-block:: python
    import json
    
    # Example of a JSON structure for sending requests to Google Gemini API
    request_data = {
      "cachedContent": "previous_chat_data",
      "contents": [
        {
          "role": "user",
          "parts": [
              {
                  "text": "Hello, how are you?"
              }
          ]
        },
          {
              "role": "model",
              "parts": [
                  {
                      "text": "I'm fine, thank you. How can I help you today?"
                  }
              ]
          }
      ],
      "systemInstruction": {
        "role": "system",
        "parts": [
          {
            "text": "You are a helpful assistant."
          }
        ]
      },
        "tools": [
              {
                  "functionDeclarations": [
                      {
                          "name": "get_current_weather",
                          "description": "Get current weather in the given location.",
                            "parameters": {
                              "location": "string"
                            }
                      }
                  ]
              }
        ],
      "safetySettings": [
        {
          "category": "HARM_CATEGORY_HATE_SPEECH",
          "threshold": "BLOCK_LOW_AND_ABOVE"
        }
      ],
      "generationConfig": {
        "temperature": 0.8,
        "topP": 0.9,
        "maxOutputTokens": 256,
        "responseMimeType": "text/plain"
      },
        "labels": {
            "user_id": "123456"
        }
    }
    
    # You can use this dictionary to create a JSON string
    request_json = json.dumps(request_data, indent=2)
    print(request_json)
    
    # This JSON string can be used as the body of the request to the Gemini API.

    # For example you can send this json in your python code using 'requests' library:
    
    # import requests
    #
    # url = "https://generativeai.googleapis.com/v1/models/gemini-pro:generateContent"
    # headers = {
    #   "Content-Type": "application/json"
    # }
    # response = requests.post(url, headers=headers, json=request_data)
    #
    # if response.status_code == 200:
    #   print(response.json())
    # else:
    #   print(f"Error: {response.status_code}, {response.text}")