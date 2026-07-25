How to use this code block
=========================================================================================

Description
-------------------------
This code block defines a header module for a project, setting up the project root, loading configurations from `config.json`, and reading documentation from `README.MD`. It also defines several global variables such as project name, version, documentation string, and author information. This module is intended to centralize project settings and make them accessible throughout the application.

Execution steps
-------------------------
1.  **Import necessary modules**: Import `sys`, `json`, `Version` from `packaging.version` and `Path` from `pathlib`.
2.  **Define `set_project_root` function**:
    -   **Get current file's directory**: Determine the absolute path of the directory where the current Python file is located.
    -   **Initialize root path**: Initialize the `__root__` variable with the current file's directory.
    -   **Search for project root**: Iterates through the current directory and all its parent directories.
    -   **Check for marker files**: For each directory, check if any of the specified `marker_files` exist in that directory. If a marker file is found, the `__root__` variable is set to that directory and the loop is terminated.
    -   **Add to `sys.path`**: If the found `__root__` is not already in Python's `sys.path`, add it to `sys.path` at the beginning.
    -   **Return root path**: Return the determined root path of the project.
3.  **Set the project root**: Call the `set_project_root()` function to get the project's root path and assign it to `__root__`.
4.  **Import global settings `gs`**: Import the `gs` variable from the `src` module which contains global settings of the program.
5.  **Load configuration**:
    -   Attempt to open and load `config.json` from the `src` directory of the project.
    -   If loading fails due to `FileNotFoundError` or `json.JSONDecodeError`, skip and continue with default settings.
6.  **Load documentation**:
    -   Attempt to open and read `README.MD` from the `src` directory of the project.
    -   If loading fails due to `FileNotFoundError` or `json.JSONDecodeError`, skip and continue with default settings.
7.  **Set global variables**:
    -   Set `__project_name__` to the value of the `project_name` key from the loaded `config`, otherwise, default to `hypotez`.
    -   Set `__version__` to the value of the `version` key from the loaded `config`, otherwise, default to `''`.
    -   Set `__doc__` to the content of the `README.MD` file, if it exists, otherwise, default to `''`.
    -   Set `__details__` to `''`.
    -   Set `__author__` to the value of the `author` key from the loaded `config`, otherwise, default to `''`.
    -   Set `__copyright__` to the value of the `copyrihgnt` key from the loaded `config`, otherwise, default to `''`.
    -   Set `__cofee__` to the value of the `cofee` key from the loaded `settings`, otherwise use a default message.

Usage example
-------------------------
.. code-block:: python

    import sys
    from pathlib import Path
    import json

    def set_project_root(marker_files=('__root__','.git')) -> Path:
        """
        Finds the root directory of the project starting from the current file's directory,
        searching upwards and stopping at the first directory containing any of the marker files.

        Args:
            marker_files (tuple): Filenames or directory names to identify the project root.
        
        Returns:
            Path: Path to the root directory if found, otherwise the directory where the script is located.
        """
        __root__:Path
        current_path:Path = Path(__file__).resolve().parent
        __root__ = current_path
        for parent in [current_path] + list(current_path.parents):
            if any((parent / marker).exists() for marker in marker_files):
                __root__ = parent
                break
        if __root__ not in sys.path:
            sys.path.insert(0, str(__root__))
        return __root__

    # Get the root directory of the project
    __root__: Path = set_project_root()

    from src import gs

    config:dict = None
    try:
        with open(gs.path.root / 'src' /  'config.json', 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ...

    doc_str:str = None
    try:
        with open(gs.path.root / 'src' /  'README.MD', 'r') as settings_file:
            doc_str = settings_file.read()
    except (FileNotFoundError, json.JSONDecodeError):
        ...

    __project_name__ = config.get("project_name", 'hypotez') if config else 'hypotez'
    __version__: str = config.get("version", '')  if config else ''
    __doc__: str = doc_str if doc_str else ''
    __details__: str = ''
    __author__: str = config.get("author", '')  if config else ''
    __copyright__: str = config.get("copyrihgnt", '')  if config else ''
    __cofee__: str = "Treat the developer to a cup of coffee for boosting enthusiasm in development: https://boosty.to/hypo69"  

    # Example Usage:
    # To access project configuration and documentation.
    print(f"Project Name: {__project_name__}")
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print(f"Documentation: {__doc__[:100]}...")  # Display the first 100 characters of documentation