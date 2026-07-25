How to use this code block
=========================================================================================

Description
-------------------------
This code block initializes the `gemini_simplechat` package by importing the `gs` variable from the `gemini_simplechat.gs` module. The `gs` variable is intended to contain global settings loaded from a configuration file. This step ensures that the global settings are available when the package is imported into other modules or scripts.

Execution steps
-------------------------
1. **Import `gs`**: Import the `gs` variable from the `gemini_simplechat.gs` module using a relative import.

Usage example
-------------------------
.. code-block:: python

    # This __init__.py file is usually located in the package root
    # Inside gemini_simplechat/__init__.py
    
    # Import the global settings (gs)
    from .gs import gs
    
    # Now, the global settings object 'gs' can be used when importing the `gemini_simplechat` package.
    
    # Example usage in a separate module:
    # from gemini_simplechat import gs
    # api_key = gs.get('api_key')  # Access an api_key config value
    # model_name = gs.get('model_name') # Access a model_name value