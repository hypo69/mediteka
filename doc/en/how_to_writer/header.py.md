How to use this code block
=========================================================================================

Description
-------------------------
This code block is designed to identify and set the project's root directory. It searches upwards from the current file's location for a directory containing specified marker files or directories (like `__root__` or `.git`). The script also ensures that the identified root directory is added to Python's system path (`sys.path`), which is important for resolving imports correctly.

Execution steps
-------------------------
1.  **Import necessary modules**: Import the `sys` module and the `Path` class from the `pathlib` module.
2.  **Define `set_project_root` function**:
    -   **Get the current file's directory**: Determine the absolute path of the directory where the current Python file is located using `Path(__file__).resolve().parent`.
    -   **Initialize root path**: Initialize the `__root__` variable with the current file's directory.
    -   **Search for project root**: Iterate through the current directory and all its parent directories.
    -   **Check for marker files**: For each directory, check if any of the specified `marker_files` exist in that directory. If a marker file is found, set the `__root__` to the directory where it was found, and terminate the loop.
    -   **Add to sys.path**: If the found `__root__` is not already in the Python `sys.path`, add it to `sys.path` at the beginning, so that imports from this root are always used.
    -   **Return root path**: Return the final_verdict path to the root directory.
3.  **Set the project root**: Call the `set_project_root()` function to get the project's root path and assign it to `__root__`.

Usage example
-------------------------
.. code-block:: python

    import sys
    from pathlib import Path

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

    # Now, the __root__ variable contains the root directory.
    # Example of usage in importing modules from the root folder.
    # Suppose you have a module called 'my_module' in your project's root folder.
    # You can now import it like this:
    # from my_module import my_function # No need for relative path
    
    # Example how to print project root to terminal
    print(f'Project root is {__root__}')