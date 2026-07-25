# Module gs

## Overview

This module is responsible for loading program parameters from a JSON configuration file.

## Table of Contents

- [Functions](#functions)

## Functions

### `j_loads_ns`

**Description**: Loads data from a JSON file.

**Parameters**:
- `file_path` (str | Path): The path to the JSON file.

**Returns**:
- `dict`: The data loaded from the JSON file.

**Raises**:
- `FileNotFoundError`: If the file specified by `file_path` does not exist.
- `JSONDecodeError`: If the file specified by `file_path` is not a valid JSON format.
```
## Changes
No changes were required to the provided `input_code`. The documentation was created based on the file path, structure, and inline comments. The function `j_loads_ns` has been documented.