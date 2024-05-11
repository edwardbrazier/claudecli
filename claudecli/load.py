"""
Utility functions for loading configuration, history data, and codebase files.

This module provides functions to:
1. Load a YAML configuration file, creating it with default values if it doesn't exist.
2. Load a JSON session history file.
3. Get the timestamp of the last saved session.
4. Load and concatenate the contents of files in a directory and its subdirectories,
   with headers indicating each file's path relative to the base path.

Functions:
    load_config(logger, config_file)
    load_history_data(history_file)
    get_last_save_file()
    load_codebase(logger, base_path, extensions)
"""

import logging
import os
import yaml

from pathlib import Path
from typing import List

from claudecli import constants
from claudecli.printing import console
from claudecli.pure import get_size
from claudecli.codebase_watcher import CodebaseState


class Codebase:
    def __init__(
        self,
        concatenated_contents: str,
        file_paths: list[str],
        codebase_state: CodebaseState,
    ):
        self.concatenated_contents = concatenated_contents
        self.file_paths = file_paths
        self.codebase_state = codebase_state

    def __add__(self, other: "Codebase") -> "Codebase":
        """
        Overload the `+` operator to concatenate two `Codebase` objects.
        Args:
            other (Codebase): The other `Codebase` object to concatenate with.

        Preconditions:
            - `other` is a valid `Codebase` object.

        Side effects:
            None.
        """
        concatenated_contents = self.concatenated_contents + other.concatenated_contents
        file_paths = self.file_paths + other.file_paths
        codebase_state = self.codebase_state + other.codebase_state
        return Codebase(concatenated_contents, file_paths, codebase_state)

    def __str__(self) -> str:
        # Include both the string and the file names.
        return f"{self.concatenated_contents}\n\n---\n\n{self.file_paths}"


def load_config(logger: logging.Logger, config_file: str) -> dict:  # type: ignore
    """
    Read a YAML config file and return its content as a dictionary.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        config_file (str): Path to the YAML configuration file.

    Preconditions:
        - The config_file path is a valid file path.

    Side effects:
        - If the config file does not exist, it is created with default configurations.
        - If the config file is missing keys, they are populated with default values.

    Exceptions:
        None

    Returns:
        dict: The configuration data loaded from the YAML file.
        Guarantees: The returned dictionary will contain all required configuration keys.
    """
    # If the config file does not exist, create one with default configurations
    if not Path(config_file).exists():
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as file:
            yaml.dump(constants.DEFAULT_CONFIG, file, default_flow_style=False)  # type: ignore
        logger.info(f"New config file initialized: [green bold]{config_file}")

    # Load existing config
    with open(config_file, encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update the loaded config with any default values that are missing
    for key, value in constants.DEFAULT_CONFIG.items():  # type: ignore
        if key not in config:
            config[key] = value

    return config


def load_codebase(base_path: str, extensions: List[str]) -> Codebase:
    """
    Concatenate the contents of files in the given directory and its subdirectories
    that match the specified file extensions.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        base_path (str): The starting directory path to search for files.
        extensions (List[str]): A list of file extension strings to include (e.g., ['py', 'txt']).

    Preconditions:
        - The base_path is a valid directory path.
        - The extensions list contains valid file extension strings.

    Side effects:
        None

    Exceptions:
        ValueError: If base_path does not exist or is not a directory.

    Returns:
        Codebase: A Codebase object containing the concatenated file contents, a list of loaded file paths, and the initial CodebaseState.
        guarantees: The returned Codebase object will contain the concatenated file contents, a list of file paths, and the initial CodebaseState.
                    These may be empty.
    """

    # Verify the base path exists and is a directory
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise ValueError(f"The path {base_path} does not exist or is not a directory.")

    concatenated_contents = ""

    encodings = ["utf-8", "cp1252", "iso-8859-1"]

    concatenated_contents += "<codebase_subfolder>\n"

    codebase_files: list[str] = []
    codebase_state = CodebaseState()

    # Walk through the directory and subdirectories recursively
    for root, _, files in os.walk(base_path):
        if "__pycache__" not in root:
            for file_name in files:
                if (
                    any(file_name.endswith(f".{ext}") for ext in extensions)
                    or not extensions
                ):
                    file_path_absolute = os.path.join(root, file_name)
                    file_path_relative = os.path.relpath(file_path_absolute, base_path)

                    file_loaded = False
                    for encoding in encodings:
                        try:
                            with open(
                                file_path_absolute, "r", encoding=encoding
                            ) as file:
                                contents = file.read()
                                concatenated_contents += (
                                    f"<file>\n"
                                    f"<path>{file_path_relative}</path>\n"
                                    f"<content>{contents}</content>\n"
                                    f"</file>\n"
                                )
                                codebase_files.append(file_path_relative)
                                codebase_state.add_file(
                                    file_path_relative,
                                    os.path.getmtime(file_path_absolute),
                                )
                                file_loaded = True
                                break
                        except (OSError, IOError) as e:
                            console.print(
                                f"Error reading file {file_path_absolute} with encoding {encoding}: {e}"
                            )

                    if not file_loaded:
                        console.print(
                            f"Failed to load file {file_path_absolute} with any encoding."
                        )

    concatenated_contents += "</codebase_subfolder>\n"

    console.print(
        f"\tLoaded [green bold]{len(codebase_files)} files[/green bold] from codebase."
    )
    console.print(
        f"\tCodebase size: [green bold]{get_size(concatenated_contents)}[/green bold]"
    )

    return Codebase(
        concatenated_contents=concatenated_contents,
        file_paths=codebase_files,
        codebase_state=codebase_state,
    )
