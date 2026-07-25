How to use this code block
=========================================================================================

Description
-------------------------
This code block initializes the `src.ai.gemini` package by importing the `GoogleGenerativeAI` class from the `src.ai.gemini.generative_ai` module. By importing the class here, it makes the class directly available when the `src.ai.gemini` package is imported, which simplifies the code when creating the Google Gemini model instance.

Execution steps
-------------------------
1.  **Import `GoogleGenerativeAI`**: Import the `GoogleGenerativeAI` class using a relative import from the `src.ai.gemini.generative_ai` module.

Usage example
-------------------------
.. code-block:: python

    # This __init__.py file is usually located in the package root
    # Inside src/ai/gemini/__init__.py
    
    # Import the GoogleGenerativeAI class
    from .generative_ai import GoogleGenerativeAI
    
    # Now, the class is available when importing the `src.ai.gemini` package.
    
    # Example usage in a separate module:
    # from src.ai.gemini import GoogleGenerativeAI
    
    # api_key = "your_api_key"
    # ai = GoogleGenerativeAI(api_key)
    # response = await ai.ask("Hello, Gemini!")
    # print(response)