"""
Utility functions for loading configuration, history data, and codebase files.

This module provides functions to:
1. Load a YAML configuration file, creating it with default values if it doesn't exist.
2. Load a JSON session history file.
3. Get the timestamp of the last saved session.
4. Load and concatenate the contents of files in a directory and its subdirectories,
   with headers indicating each file's path relative to the base path.
5. Load the contents of a single file, with a header indicating its path.

Functions:
    load_config(logger, config_file)
    load_history_data(history_file)
    get_last_save_file()
    load_codebase(logger, base_path, extensions)
    load_file_xml(file_path)
"""

import os
import yaml

from pathlib import Path
from typing import List

from claudecli import constants
from claudecli.printing import console
from claudecli.codebase_watcher import Codebase, CodebaseState


def load_config(config_file: str) -> dict:  # type: ignore
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
        # logger.info(f"New config file initialized: [green bold]{config_file}")

    # Load existing config
    with open(config_file, encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update the loaded config with any default values that are missing
    for key, value in constants.DEFAULT_CONFIG.items():  # type: ignore
        if key not in config:
            config[key] = value

    return config


def load_codebase_state(base_path: str, extensions: List[str]) -> CodebaseState:
    """
    Load the codebase state from the given directory and its subdirectories
    that match the specified file extensions.
    If base_path is a file instead of a directory, load the state for just that single file.

    Args:
        base_path (str): The starting directory path or file path to load. 
        extensions (List[str]): A list of file extension strings to include (e.g., ['py', 'txt']).

    Preconditions:
        - The base_path is a valid directory path or file path.
        - The extensions list contains valid file extension strings.

    Side effects:
        None

    Exceptions:
        ValueError: If base_path does not exist or is not a directory or file.

    Returns:
        CodebaseState: The CodebaseState object representing the state of the codebase.
                       A single file specified by the user can be a codebase with a single element in it.
        guarantees: The returned CodebaseState object will contain the file paths and their last modified timestamps.
    """

    # Verify the base path exists
    if not os.path.exists(base_path):
        raise ValueError(f"The path {base_path} does not exist.")

    codebase_state = CodebaseState()

    # If base_path is a file, load the codebase from that file
    file_path = base_path

    if os.path.isfile(file_path):
        codebase_state.add_file(
            os.path.relpath(file_path, os.path.dirname(file_path)),
            os.path.getmtime(file_path),
        )

    # If base_path is a directory, load the codebase from there
    if os.path.isdir(base_path):
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

                        codebase_state.add_file(
                            file_path_relative,
                            os.path.getmtime(file_path_absolute),
                        )

    return codebase_state

def load_file_xml(file_path: str) -> str:
    """
    Load the contents of a single file and return it as an XML string.

    Args:
        file_path (str): The path to the file to load.

    Preconditions:
        - file_path is a valid file path.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The XML representation of the file contents.
        guarantees: The returned string will be a valid XML representation of the file.
    """

    assert os.path.isfile(file_path), f"{file_path} is not a valid file path"

    encodings = ["utf-8", "cp1252", "iso-8859-1"]
    file_loaded = False
    file_xml = ""

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                contents = file.read()
                file_xml = f"<single_file>\n<file>\n<path>{file_path}</path>\n<content>{contents}</content>\n</file>\n</single_file>"
                file_loaded = True
                break
        except (OSError, IOError) as e:
            console.print(
                f"Error reading file {file_path} with encoding {encoding}: {e}"
            )

    if not file_loaded:
        console.print(f"Failed to load file {file_path} with any encoding.")
        return ""

    return file_xml


def load_codebase_xml(codebase_locations: List[str], extensions: List[str]) -> str:
    """
    Load the codebase XML representation from the given directories and their subdirectories
    that match the specified file extensions.

    Args:
        codebase_locations (List[str]): A list of directory paths to search for files.
        extensions (List[str]): A list of file extension strings to include (e.g., ['py', 'txt']).

    Preconditions:
        - The codebase_locations list contains valid directory paths.
        - The extensions list contains valid file extension strings.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The XML representation of the codebase.
        guarantees: The returned string will be a valid XML representation of the codebase.
    """

    codebase_xml = "<codebase>\n"

    encodings = ["utf-8", "cp1252", "iso-8859-1"]

    for base_path in codebase_locations:
        codebase_xml += "<codebase_subfolder>\n"

        # Walk through the directory and subdirectories recursively
        for root, _, files in os.walk(base_path):
            if "__pycache__" not in root:
                for file_name in files:
                    if (
                        any(file_name.endswith(f".{ext}") for ext in extensions)
                        or not extensions
                    ):
                        file_path_absolute = os.path.join(root, file_name)
                        file_path_relative = os.path.relpath(
                            file_path_absolute, base_path
                        )

                        file_loaded = False
                        for encoding in encodings:
                            try:
                                with open(
                                    file_path_absolute, "r", encoding=encoding
                                ) as file:
                                    contents = file.read()
                                    codebase_xml += (
                                        f"<file>\n"
                                        f"<path>{file_path_relative}</path>\n"
                                        f"<content>{contents}</content>\n"
                                        f"</file>\n"
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

        codebase_xml += "</codebase_subfolder>\n"

    codebase_xml += "</codebase>\n"

    return codebase_xml


def load_codebase_xml_(codebases: list[Codebase], extensions: list[str]) -> str:
    """
    A wrapper over load_codebase_xml()
    """

    codebase_locations: list[str] = [c.location for c in codebases]
    return load_codebase_xml(codebase_locations, extensions)
