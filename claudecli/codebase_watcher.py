"""
This module is for detecting changes to a codebase and updating the program's representation of the codebase state.
"""
from typing import List, Set, NamedTuple
import os

from claudecli.printing import console

FilePath = str
CodebaseLocation = str # A CodebaseLocation can be either a file or a folder.
ModificationDate = float


class CodebaseState:
    def __init__(self):
        # File paths are always relative to the codebase location.
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
        assert (
            isinstance(file_path, str) and file_path
        ), "file_path must be a non-empty string"
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
        assert (
            isinstance(file_path, str) and file_path
        ), "file_path must be a non-empty string"
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


class Codebase(NamedTuple):
    location: CodebaseLocation
    state: CodebaseState


class FileUpdate(NamedTuple):
    file_path: FilePath  # This path is always relative to the codebase location.
    last_modified: ModificationDate


class CodebaseTransformation:
    """
    Invariant: There must not be any double-ups in the `additions` or `updates` sets.
    """
    def __init__(self):
        self.additions: Set[FileUpdate] = set()
        self.updates: Set[FileUpdate] = set()
        self.deletions: Set[FilePath] = set()

    def compose(self, other: "CodebaseTransformation") -> "CodebaseTransformation":
        """
        Compose two CodebaseTransformation objects.

        Args:
            other (CodebaseTransformation): The other CodebaseTransformation to compose with.

        Preconditions:
            - other is a valid CodebaseTransformation object.

        Side effects:
            None

        Exceptions:
            None

        Returns:
            CodebaseTransformation: A new CodebaseTransformation object representing the composition of the two transformations.
        """
        pass
        return IDENTITY_TRANSFORMATION


IDENTITY_TRANSFORMATION = CodebaseTransformation()


def changed_files(transformation: CodebaseTransformation) -> Set[FilePath]:
    """
    Gives a list of all files affected by the CodebaseTransformation, as paths relative to the codebase location.
    """
    updates: Set[FilePath] = set(f.file_path for f in transformation.updates)
    additions: Set[FilePath] = set(f.file_path for f in transformation.additions)
    return updates.union(additions).union(transformation.deletions)


class CodebaseChangeDescriptive(NamedTuple):
    """
    Describes a change to the codebase/s in full detail, suitable for presenting to the user and to the AI.
    """

    change_descriptions: str  # Description at the level of file names, not contents.
    change_contents: (
        str  # The contents of the changed files, compiled in an XML format.
    )


class CodebaseUpdates(NamedTuple):
    """
    Describes everything that the main loop needs to know about the changes
    that the codebase watcher has discovered.
    """

    codebase_changes: list[CodebaseTransformation]
    change_descriptive: CodebaseChangeDescriptive


def num_affected_files(updates: CodebaseUpdates) -> int:
    """
    Returns the number of files affected by the codebase updates.
    """
    num_affected = sum(
        [
            len(t.additions) + len(t.deletions) + len(t.updates)
            for t in updates.codebase_changes
        ]
    )
    return num_affected


# TODO: THIS IS WRONG. IT SHOULD ACCEPT A LIST OF TRANSFORMATIONS WHICH IS NOT THE SAME LENGTH AS THE LIST OF CODEBASES.
# IT SHOULD EVEN ACCEPT MULTIPLE TRANSFORMATIONS IN A ROW TO THE ONE CODEBASE.
# IT SHOULD ALSO ACCEPT ONE TRANSFORMATION TO ONE CODEBASE, WHEN THERE IS A SECOND CODEBASE IN THE LIST.
def amend_codebase_records(
    codebases: list[Codebase], transformations: list[CodebaseTransformation]
) -> list[Codebase]:
    """
    Apply the given CodebaseTransformations to the corresponding Codebases and return a new list of Codebases.

    Args:
        codebases (list[Codebase]): The list of Codebases to update.
        transformations (list[CodebaseTransformation]): The list of CodebaseTransformations to apply.

    Preconditions:
        - codebases and transformations are non-empty lists of the same length.
        - Each Codebase in codebases has a corresponding CodebaseTransformation in transformations at the same index.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        list[Codebase]: A new list of Codebases with the transformations applied.
        guarantees: The original codebases list is not modified.
    """
    assert len(codebases) == len(
        transformations
    ), "codebases and transformations must have the same length"
    updated_codebases: list[Codebase] = []
    for codebase, transformation in zip(codebases, transformations):
        updated_state = apply_transformation(codebase.state, transformation)
        updated_codebases.append(Codebase(codebase.location, updated_state))
    return updated_codebases


def find_changed_files(
    codebase_location: str, file_extensions: List[str], codebase_state: CodebaseState
) -> CodebaseTransformation:
    """
    Check the codebase for changes by comparing the current state with the provided codebase state.
    Provide the list of changes at the level of filenames, not contents.

    Args:
        codebase_location (str): The location of the codebase.
        file_extensions (List[str]): The file extensions to consider. (If this is empty, look at files with any extensions.)
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
        CodebaseTransformation: The transformation representing the changes in the codebase.
    """
    assert (
        isinstance(codebase_location, str) and codebase_location
    ), "codebase_location must be a non-empty string"
    assert isinstance(file_extensions, list) and all(
        isinstance(ext, str) for ext in file_extensions
    ), "file_extensions must be a list of strings"
    assert isinstance(
        codebase_state, CodebaseState
    ), "codebase_state must be a CodebaseState object"

    transformation = CodebaseTransformation()

    for root, _, files in os.walk(codebase_location):
        if "__pycache__" not in root:
            for file_name in files:
                if (
                    any(file_name.endswith(f".{ext}") for ext in file_extensions)
                    or not file_extensions
                ):
                    file_path_relative = os.path.relpath(
                        os.path.join(root, file_name), codebase_location
                    )
                    file_path_absolute = os.path.join(
                        codebase_location, file_path_relative
                    )

                    try:
                        if file_path_relative not in codebase_state.files:
                            last_modified = os.path.getmtime(file_path_absolute)
                            transformation.additions.add(
                                FileUpdate(file_path_relative, last_modified)
                            )
                        else:
                            last_modified = os.path.getmtime(file_path_absolute)
                            if (
                                last_modified
                                != codebase_state.files[file_path_relative]
                            ):
                                transformation.updates.add(
                                    FileUpdate(file_path_relative, last_modified)
                                )
                    except (OSError, IOError) as e:
                        console.print(f"Error accessing file {file_path_absolute}: {e}")

    for file_path_relative in codebase_state.files:
        if not os.path.exists(os.path.join(codebase_location, file_path_relative)):
            transformation.deletions.add(file_path_relative)

    return transformation


def find_codebase_change_contents(
    codebase_locations: List[str],
    file_extensions: List[str],
    codebase_states: List[CodebaseState],
) -> CodebaseUpdates:
    """
    Check multiple codebases for changes and return the change descriptions and file contents.

    Args:
        codebase_locations (List[str]): A list of codebase locations.
        file_extensions (List[str]): A list of file extensions to consider. (If this is empty, look at files with any extensions.)
        codebase_states (List[CodebaseState]): A list of corresponding codebase states.

    Preconditions:
        - codebase_locations is a non-empty list of valid directory paths.
        - file_extensions is a list of valid file extension strings.
        - codebase_states is a list of valid CodebaseState objects.
        - The lengths of codebase_locations and codebase_states are equal.

    Side effects:
        None

    Exceptions:
        None

    Returns:
        CodebaseChangeDescriptive: A CodebaseChangeDescriptive object containing the number of changes, change descriptions, and changed file contents.
    """
    assert isinstance(codebase_locations, list) and all(
        isinstance(loc, str) for loc in codebase_locations
    ), "codebase_locations must be a list of strings"
    assert isinstance(file_extensions, list) and all(
        isinstance(ext, str) for ext in file_extensions
    ), "file_extensions must be a list of strings"
    assert isinstance(codebase_states, list) and all(
        isinstance(state, CodebaseState) for state in codebase_states
    ), "codebase_states must be a list of CodebaseState objects"
    assert len(codebase_locations) == len(
        codebase_states
    ), "codebase_locations and codebase_states must have the same length"

    change_descriptions = ""
    file_contents = ""
    codebase_transformations: list[CodebaseTransformation] = []

    for location, state in zip(codebase_locations, codebase_states):
        transformation = find_changed_files(location, file_extensions, state)
        codebase_transformations.append(transformation)

        change_descriptions += f"Codebase: {location}\n"
        change_descriptions += format_transformation(transformation)
        change_descriptions += "\n"

        for file_addition in transformation.additions:
            try:
                with open(os.path.join(location, file_addition.file_path), "r") as file:
                    file_contents += f"<file>\n<path>{file_addition.file_path}</path><changes>This file has been added since the last codebase check.</changes>\n<content>{file.read()}</content>\n</file>\n\n"
            except (OSError, IOError) as e:
                console.print(
                    f"Error reading added file {file_addition.file_path}: {e}"
                )

        for file_update in transformation.updates:
            try:
                with open(os.path.join(location, file_update.file_path), "r") as file:
                    file_contents += f"<file>\n<path>{file_update.file_path}</path><changes>This file has been modified since the last codebase check.</changes>\n<content>{file.read()}</content>\n</file>\n\n"
            except (OSError, IOError) as e:
                console.print(
                    f"Error reading updated file {file_update.file_path}: {e}"
                )

        for file_delete in transformation.deletions:
            file_contents += f"<file>\n<path>{file_delete}</path><changes>This file has been deleted since the last codebase check.</changes>\n</file>\n\n"

    change_descriptive = CodebaseChangeDescriptive(
        change_descriptions.strip(), file_contents.strip()
    )

    return CodebaseUpdates(codebase_transformations, change_descriptive)


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
    assert isinstance(
        transformation, CodebaseTransformation
    ), "transformation must be a CodebaseTransformation object"

    description = ""

    if transformation.additions:
        description += "Added files:\n"
        for file_addition in transformation.additions:
            description += f"- {file_addition.file_path}\n"
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

    if len(transformation.additions | transformation.deletions | transformation.updates) == 0:
        description = "No changes.\n"

    return description.strip()


def apply_transformation(
    codebase_state: CodebaseState, transformation: CodebaseTransformation
) -> CodebaseState:
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
    assert isinstance(
        codebase_state, CodebaseState
    ), "codebase_state must be a CodebaseState object"
    assert isinstance(
        transformation, CodebaseTransformation
    ), "transformation must be a CodebaseTransformation object"

    updated_state = CodebaseState()
    updated_state.files = codebase_state.files.copy()

    for file_addition in transformation.additions:
        updated_state.add_file(file_addition.file_path, file_addition.last_modified)

    for file_path in transformation.deletions:
        updated_state.remove_file(file_path)

    for file_update in transformation.updates:
        updated_state.add_file(file_update.file_path, file_update.last_modified)
    return updated_state
