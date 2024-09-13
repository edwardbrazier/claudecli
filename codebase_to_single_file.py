
import argparse
import os
from typing import List, Tuple
from claudecli.load import load_codebase_xml_, load_codebase_state
from claudecli.codebase_watcher import Codebase, CodebaseState

def convert_codebase_to_single_file(codebase_locations: List[str], extensions: List[str]) -> Tuple[str, CodebaseState]:    
    """
    Convert the given codebase locations into a single file, preserving the original file structure.

    Args:
        codebase_locations (List[str]): A list of directory paths to search for files.
        extensions (List[str]): A list of file extension strings to include (e.g., ['py', 'txt']).

    Returns:
        Tuple[str, CodebaseState]: A tuple containing the XML representation of the codebase and the CodebaseStat
object.
    """
    codebases = [Codebase(location, load_codebase_state(location, extensions)) for location in codebase_locations]
    codebase_xml = load_codebase_xml_(codebases, extensions)
    codebase_state = codebases[0].state if codebases else CodebaseState()
    return codebase_xml, codebase_state

def main():
    parser = argparse.ArgumentParser(description="Convert codebase to a single XML file.")
    parser.add_argument("locations", nargs="+", help="List of codebase locations (directories)")
    parser.add_argument("-e", "--extensions", nargs="+", default=["py"], help="List of file extensions to include (default: py)")
    parser.add_argument("-o", "--output", default="codebase_output.xml", help="Output XML file name (default: codebase_output.xml)")

    args = parser.parse_args()

    codebase_xml, codebase_state = convert_codebase_to_single_file(args.locations, args.extensions)

    with open(args.output, "w", encoding='utf-8') as f:
        f.write(codebase_xml)

    print(f"Codebase XML written to: {args.output}")
    print(f"Codebase State:\n{codebase_state}")

if __name__ == "__main__":
    main()