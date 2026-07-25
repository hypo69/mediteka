How to use this code block
=========================================================================================

Description
-------------------------
This code block is designed to load the application's configuration parameters from a JSON file named `config.json`. It uses a custom JSON loading function, `j_loads_ns`, from the `src.utils.jjson` module, which handles loading the JSON data from the specified file path. The loaded configurations are then stored in the `gs` variable, which is intended to be used as a global configuration object.

Execution steps
-------------------------
1.  **Import necessary modules**: Import the `header` module, the `j_loads_ns` function from the `src.utils.jjson` module, and the `Path` class from the `pathlib` module.
2.  **Create a `Path` object**: Create a `Path` object representing the `config.json` file. This creates a Path instance, that stores the path to the config file, and makes it usable with functions from `pathlib`
3.  **Load JSON configuration**: Use the `j_loads_ns` function to load the configuration data from the `config.json` file specified in the `Path` object, and assign it to the `gs` variable.

Usage example
-------------------------
.. code-block:: python

    from pathlib import Path
    from src.utils.jjson import j_loads_ns
    
    # Load configuration parameters from 'config.json'
    gs = j_loads_ns(Path('config.json'))
    
    # Now, the 'gs' variable contains the loaded configurations.
    # You can access specific configuration parameters like this (assuming 'config.json' is loaded):
    # For example, if 'config.json' contains:
    # {
    #   "api_key": "your_api_key",
    #   "model_name": "gemini-pro"
    # }
    # You can access these values like this:
    # api_key = gs.api_key
    # model_name = gs.model_name
    # or
    # api_key = gs.get("api_key")
    # model_name = gs.get("model_name")
    # depending on what the `j_loads_ns` function returns.