
import os
from typing import List, Tuple
from claudecli.load import load_codebase_xml_
from claudecli.codebase_watcher import Codebase, CodebaseState

def convert_codebase_to_single_file(codebase_locations: List[str], extensions: List[str]) -> Tuple[str, CodebaseState]:
    """
    Convert the given codebase locations into a single file, preserving the original file structure.

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
        Tuple[str, CodebaseState]: A tuple containing the XML representation of the codebase and the CodebaseState object.
        guarantees: The returned XML string will be a valid representation of the codebase.
    """
    codebase_xml = load_codebase_xml_(codebase_locations, extensions)
    codebase_state = load_codebase_state(codebase_locations[0], extensions)
    return codebase_xml, codebase_state

def main():
    codebase_locations = ["src", "tests"]
    extensions = ["py"]
    codebase_xml, codebase_state = convert_codebase_to_single_file(codebase_locations, extensions)

    print(f"Codebase XML:\n{codebase_xml}")
    print(f"Codebase State:\n{codebase_state}")

if __name__ == "__main__":
    main()
