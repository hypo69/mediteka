# JSON Schema Documentation

## Overview

This document describes the structure of a JSON schema used for configuring and managing content generation with Google Gemini models. It includes configurations for cached content, content parts, system instructions, tools, safety settings, generation configurations, and labels.

## Table of Contents

- [Root Object](#root-object)
    - [Properties](#properties)
- [Content Object](#content-object)
    - [Properties](#properties-1)
    - [Part Object](#part-object)
        - [Properties](#properties-2)
- [System Instruction Object](#system-instruction-object)
    - [Properties](#properties-3)
    - [Instruction Part Object](#instruction-part-object)
        - [Properties](#properties-4)
- [Tool Object](#tool-object)
    - [Properties](#properties-5)
    - [Function Declaration Object](#function-declaration-object)
        - [Properties](#properties-6)
- [Safety Setting Object](#safety-setting-object)
    - [Properties](#properties-7)
- [Generation Configuration Object](#generation-configuration-object)
    - [Properties](#properties-8)
- [Labels Object](#labels-object)
    - [Properties](#properties-9)

## Root Object

### Properties

-   `cachedContent` (string): Cached content string.
-   `contents` (array of [Content Object](#content-object)): Array of content objects.
-   `systemInstruction` ([System Instruction Object](#system-instruction-object)): Object containing system instructions.
-   `tools` (array of [Tool Object](#tool-object)): Array of tool objects.
-  `safetySettings` (array of [Safety Setting Object](#safety-setting-object)): Array of safety setting objects.
-   `generationConfig` ([Generation Configuration Object](#generation-configuration-object)): Object containing generation configurations.
-   `labels` ([Labels Object](#labels-object)): Object containing labels.

## Content Object

### Properties

-   `role` (string): Role of the content, e.g., "user" or "model".
-   `parts` (array of [Part Object](#part-object)): Array of content parts.

### Part Object

#### Properties

-   **Data (Union Field):** Represents different types of content data. Only one of these fields can be present.
    -   `text` (string): Textual content.
    -   `inlineData` (object): Inline data, includes:
        -   `mimeType` (string): MIME type of the inline data.
        -   `data` (string): Base64 encoded data.
    -   `fileData` (object): File data, includes:
        -   `mimeType` (string): MIME type of the file.
        -   `fileUri` (string): URI of the file.
-    `videoMetadata` (object): Video metadata, includes:
        -    `startOffset` (object): The start offset of the video, includes:
            - `seconds` (integer):  Start offset in seconds.
            - `nanos` (integer):  Start offset in nanoseconds.
        -    `endOffset` (object): The end offset of the video, includes:
            - `seconds` (integer):  End offset in seconds.
            - `nanos` (integer):  End offset in nanoseconds.

## System Instruction Object

### Properties

-   `role` (string): Role of the instruction, typically "system".
-   `parts` (array of [Instruction Part Object](#instruction-part-object)): Array of instruction parts.

### Instruction Part Object

#### Properties

-   `text` (string): Textual instruction.

## Tool Object

### Properties

-   `functionDeclarations` (array of [Function Declaration Object](#function-declaration-object)): Array of function declarations.

### Function Declaration Object

#### Properties

-   `name` (string): Name of the function.
-   `description` (string): Description of the function.
-  `parameters` (object): The parameters of the function.

## Safety Setting Object

### Properties
- `category` (enum): The category of the harm (HarmCategory).
- `threshold` (enum): The harm blocking threshold (HarmBlockThreshold)

## Generation Configuration Object

### Properties

-   `temperature` (number): Temperature for sampling.
-   `topP` (number): Top P for nucleus sampling.
-   `topK` (number): Top K for sampling.
-   `candidateCount` (integer): Number of candidate responses.
-   `maxOutputTokens` (integer): Maximum number of output tokens.
-   `presencePenalty` (float): Presence penalty.
-   `frequencyPenalty` (float): Frequency penalty.
-   `stopSequences` (array of string): Array of stop sequences.
-   `responseMimeType` (string): MIME type of the response.
-   `responseSchema` (schema): Response schema.
-   `seed` (integer): Seed for random number generation.
-    `responseLogprobs` (boolean): Flag indicating whether response log probabilities should be returned.
-    `logprobs` (integer): Number of log probabilities to return.
-   `audioTimestamp` (boolean): Flag indicating whether the audio timestamp should be returned.

## Labels Object

### Properties

-   `(string)`: Any string key with a string value.
```
## Changes
No changes were required to the provided `input_code`. The documentation was created based on the provided JSON schema structure and inline comments. All sections are documented according to the specifications.