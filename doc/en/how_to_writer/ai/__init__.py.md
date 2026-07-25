How to use this code block
=========================================================================================

Description
-------------------------
This code block imports the `GoogleGenerativeAI` class from the `gemini` module within the current package. This import statement makes the `GoogleGenerativeAI` class available for use in the current module or other modules that import it, allowing for interaction with Google's Gemini API.

Execution steps
-------------------------
1.  **Import `GoogleGenerativeAI`**: Import the `GoogleGenerativeAI` class using a relative import from the `gemini` module.

Usage example
-------------------------
.. code-block:: python

    # Example of usage within the same package
    # In a file inside the `src` folder:

    from .gemini import GoogleGenerativeAI
    
    # Now you can use GoogleGenerativeAI in this module
    
    # For example:
    # model = GoogleGenerativeAI(api_key="your_api_key")
    # response = model.generate_content("Hello, how are you?")
    # print(response)
    

    # Example of usage in a different module:
    # In a different folder:
    
    # from src.gemini import GoogleGenerativeAI
    # model = GoogleGenerativeAI(api_key="your_api_key")
    # response = model.generate_content("Hello, how are you?")
    # print(response)