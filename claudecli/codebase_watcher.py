from typing import List, Set, NamedTuple
from pathlib import Path
import os


FilePath = str
ModificationDate = float


class FileUpdate(NamedTuple):
    file_path: FilePath
    last_modified: ModificationDate


class CodebaseState:
    def __init__(self):
        self.files: dict[FilePath, ModificationDate] = {}

    def add_file(self, file_path: FilePath, last_modified: ModificationDate):
        """
        Add a file to the codebase state.

        Args:
            file_path (FilePath): The relative path of the file.
            last_modified (ModificationDate): The last modified timestamp of the file.

        Preconditions:
            - file_path is a non-empty string representing a valid file path.
            - last_modified is a float representing a valid timestamp.

        Side effects:
            - Adds the file path and its last modified timestamp to the codebase state.

        Exceptions:
            None

        Returns:
            None
        """
        assert isinstance(file_path, str) and file_path, "file_path must be a non-empty string"
        assert isinstance(last_modified, float), "last_modified must be a float"
        self.files[file_path] = last_modified

    def remove_file(self, file_path: FilePath):
        """
        Remove a file from the codebase state.

        Args:
            file_path (FilePath): The relative path of the file to remove.

        Preconditions:
            - file_path is a non-empty string representing a valid file path.

        Side effects:
            - Removes the file path and its associated timestamp from the codebase state.

        Exceptions:
            None

        Returns:
            None
        """
        assert isinstance(file_path, str) and file_path, "file_path must be a non-empty string"
        if file_path in self.files:
            del self.files[file_path]

    def __add__(self, other: "CodebaseState") -> "CodebaseState":
        """
        Overload the `+` operator to combine two `CodebaseState` objects.

        Args:
            other (CodebaseState): The other `CodebaseState` object to combine with.

        Preconditions:
            - `other` is a valid `CodebaseState` object.

        Side effects:
            None

        Exceptions:
            None

        Returns:
            CodebaseState: A new `CodebaseState` object containing the combined file paths and timestamps.
            
        Notes:
            - If both `CodebaseState` objects have an entry for the same file path but with different modification dates,
              the modification date from `other` will be used in the combined state.
        """
        assert isinstance(other, CodebaseState), "other must be a CodebaseState object"
        combined_state = CodebaseState()
        combined_state.files = {**self.files, **other.files}
        return combined_state


class CodebaseTransformation:
    def __init__(self):
        self.additions: Set[FilePath] = set()
        self.deletions: Set[FilePath] = set()
        self.updates: Set[FileUpdate] = set()


class ChangedFiles(NamedTuple):
    file_path: FilePath
    content: str


def check_codebase(codebase_location: str, file_extensions: List[str], codebase_state: CodebaseState) -> tuple[CodebaseTransformation, Set[ChangedFiles]]:
    """
    Check the codebase for changes by comparing the current state with the provided codebase state.

    Args:
        codebase_location (str): The location of the codebase.
        file_extensions (List[str]): The file extensions to consider.
        codebase_state (CodebaseState): The current state of the codebase.

    Preconditions:
        - codebase_location is a non-empty string representing a valid directory path.
        - file_extensions is a list of valid file extension strings.
        - codebase_state is a valid CodebaseState object.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        tuple[CodebaseTransformation, Set[ChangedFiles]]: A tuple containing:
            - A CodebaseTransformation object representing the detected changes.
            - A set of ChangedFiles tuples containing the relative paths and contents of added or modified files.
    """
    assert isinstance(codebase_location, str) and codebase_location, "codebase_location must be a non-empty string"
    assert isinstance(file_extensions, list) and all(isinstance(ext, str) for ext in file_extensions), "file_extensions must be a list of strings"
    assert isinstance(codebase_state, CodebaseState), "codebase_state must be a CodebaseState object"

    transformation = CodebaseTransformation()
    changed_files: Set[ChangedFiles] = set()

    for root, _, files in os.walk(codebase_location):
        if "__pycache__" not in root:
            for file_name in files:
                if any(file_name.endswith(f".{ext}") for ext in file_extensions) or not file_extensions:
                    file_path = str(Path(root) / file_name)
                    if file_path not in codebase_state.files:
                        transformation.additions.add(file_path)
                        with open(file_path, "r") as file:
                            changed_files.add(ChangedFiles(file_path, file.read()))
                    else:
                        last_modified = os.path.getmtime(file_path)
                        if last_modified != codebase_state.files[file_path]:
                            transformation.updates.add(FileUpdate(file_path, last_modified))
                            with open(file_path, "r") as file:
                                changed_files.add(ChangedFiles(file_path, file.read()))

    for file_path in codebase_state.files:
        if not os.path.exists(file_path):
            transformation.deletions.add(file_path)

    return transformation, changed_files


def check_codebases(codebase_locations: List[str], codebase_states: List[CodebaseState]) -> tuple[str, str]:
    """
    Check multiple codebases for changes and return the change descriptions and file contents.

    Args:
        codebase_locations (List[str]): A list of codebase locations.
        codebase_states (List[CodebaseState]): A list of corresponding codebase states.

    Preconditions:
        - codebase_locations is a non-empty list of valid directory paths.
        - codebase_states is a list of valid CodebaseState objects.
        - The lengths of codebase_locations and codebase_states are equal.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        tuple[str, str]: A tuple containing:
            - The concatenated change descriptions for all codebases.
            - The concatenated contents of added or modified files from all codebases.
    """
    assert isinstance(codebase_locations, list) and all(isinstance(loc, str) for loc in codebase_locations), "codebase_locations must be a list of strings"
    assert isinstance(codebase_states, list) and all(isinstance(state, CodebaseState) for state in codebase_states), "codebase_states must be a list of CodebaseState objects"
    assert len(codebase_locations) == len(codebase_states), "codebase_locations and codebase_states must have the same length"

    change_descriptions = ""
    file_contents = ""

    for location, state in zip(codebase_locations, codebase_states):
        transformation, changed_files = check_codebase(location, [], state)
        change_descriptions += f"Codebase: {location}\n"
        change_descriptions += format_transformation(transformation)
        change_descriptions += "\n"

        for changed_file in changed_files:
            file_contents += f"Contents of file: {changed_file.file_path}\n\n{changed_file.content}\n\n"

    return change_descriptions.strip(), file_contents.strip()


def format_transformation(transformation: CodebaseTransformation) -> str:
    """
    Generate a human-readable description of the changes in a CodebaseTransformation object.

    Args:
        transformation (CodebaseTransformation): The CodebaseTransformation object representing the changes.

    Preconditions:
        - transformation is a valid CodebaseTransformation object.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The formatted description of the changes.
    """
    assert isinstance(transformation, CodebaseTransformation), "transformation must be a CodebaseTransformation object"

    description = ""

    if transformation.additions:
        description += "Added files:\n"
        for file_path in transformation.additions:
            description += f"- {file_path}\n"
        description += "\n"

    if transformation.deletions:
        description += "Deleted files:\n"
        for file_path in transformation.deletions:
            description += f"- {file_path}\n"
        description += "\n"

    if transformation.updates:
        description += "Updated files:\n"
        for file_update in transformation.updates:
            description += f"- {file_update.file_path}\n"
        description += "\n"

    return description.strip()


def apply_transformation(codebase_state: CodebaseState, transformation: CodebaseTransformation) -> CodebaseState:
    """
    Apply a CodebaseTransformation to a CodebaseState and return the updated state.

    Args:
        codebase_state (CodebaseState): The current state of the codebase.
        transformation (CodebaseTransformation): The transformation to apply.

    Preconditions:
        - codebase_state is a valid CodebaseState object.
        - transformation is a valid CodebaseTransformation object.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        CodebaseState: The updated codebase state after applying the transformation.
    """
    assert isinstance(codebase_state, CodebaseState), "codebase_state must be a CodebaseState object"
    assert isinstance(transformation, CodebaseTransformation), "transformation must be a CodebaseTransformation object"

    updated_state = CodebaseState()
    updated_state.files = codebase_state.files.copy()

    for file_path in transformation.additions:
        updated_state.add_file(file_path, os.path.getmtime(file_path))

    for file_path in transformation.deletions:
        updated_state.remove_file(file_path)

    for file_update in transformation.updates:
        updated_state.add_file(file_update.file_path, file_update.last_modified)

    return updated_state
