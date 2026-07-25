# Module header

## Overview

This module defines the root path for the project. All imports are constructed relative to this path.

## Table of Contents

- [Functions](#functions)

## Functions

### `set_project_root`

**Description**: Finds the root directory of the project by searching upwards from the current file's directory until a marker file is found.

**Parameters**:
- `marker_files` (tuple): Filenames or directory names used to identify the project root. Defaults to `('__root__', '.git')`.

**Returns**:
- `Path`: The path to the root directory of the project.

### `__root__`

**Description**: Path to the root directory of the project.

**Type**:
- `Path`
```
## Changes
No changes were required to the provided `input_code`. The documentation was created based on the file path, structure, and inline comments. The functions `set_project_root` and variable `__root__` have been documented.