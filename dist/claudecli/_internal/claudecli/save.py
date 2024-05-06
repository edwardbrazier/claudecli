"""
Utility functions for managing conversation history with an AI model.

This module provides functions to:
1. Save the AI's output to files.
2. Write file data to disk.

Functions:
    save_ai_output(response_content, output_dir, force_overwrite)
    write_files(output_dir, file_data, force_overwrite)
"""

import os
import xml.sax.saxutils

from rich.console import Console

from claudecli.ai_functions import CodeResponse
from claudecli.parseaicode import FileData

console = Console()


def save_ai_output(
    response_content: CodeResponse, output_dir: str, force_overwrite: bool
) -> None:
    """
    Save the AI's output to files.

    Args:
        response_content (ResponseContent): The response content from the AI, including the concatenated output string and file data list.
        output_dir (str): The output directory for generated files.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.

    Preconditions:
        - response_content is a valid ResponseContent object.
        - output_dir is a valid directory path.

    Side effects:
        - Writes the concatenated AI output to a file.
        - Writes generated files to the output directory.

    Exceptions:
        None.

    Returns:
        None
    """
    assert isinstance(
        response_content, CodeResponse
    ), "response_content must be a ResponseContent object"
    assert isinstance(output_dir, str), "output_dir must be a string"
    assert isinstance(force_overwrite, bool), "force_overwrite must be a bool"

    # Write concatenated output to an xml file in output_dir
    concat_file_path = os.path.join(output_dir, "concatenated_output.txt")

    console.print(
        f"[bold green]Writing raw AI output to {concat_file_path}[/bold green]"
    )

    with open(concat_file_path, "w") as f:
        f.write(response_content.content_string)
        f.close()

    file_data_list: list[FileData] = response_content.file_data_list

    console.print("[bold green]Files included in the result:[/bold green]")

    if len(file_data_list) == 0:
        console.print("Nil.")
    else:
        for relative_path, _, changes in file_data_list:
            console.print(f"[bold magenta]- {relative_path}[/bold magenta]")
            console.print(f"[bold green]Changes:[/bold green] {changes}")

        write_files(output_dir, file_data_list, force_overwrite)


def write_files(
    output_dir: str, file_data: list[FileData], force_overwrite: bool = False
) -> None:
    """
    Write the given file data to disk in the specified output directory, regardless of
    its original location.

    Args:
        output_dir (str): The directory to write the files to.
        file_data (list[FileData]): A list of FileData objects containing the file path, contents, and changes.
        force_overwrite (bool): Whether to force overwriting existing files.

    Preconditions:
        - output_dir is a valid directory path.
        - file_data is a list of valid FileData objects.

    Side effects:
        - Creates new files or overwrites existing files on disk.
        - Creates new folders as required.

    Exceptions:
        None

    Returns:
        None
        guarantees: The specified files are written to disk.
    """
    assert isinstance(output_dir, str), "output_dir must be a string"
    assert isinstance(file_data, list), "file_data must be a list"
    assert all(
        isinstance(fd, tuple) and len(fd) == 3 for fd in file_data
    ), "file_data must be a list of tuples with 3 elements"
    assert isinstance(force_overwrite, bool), "force_overwrite must be a bool"

    for relative_path, contents, _ in file_data:
        file_name = os.path.basename(relative_path)
        output_file = os.path.join(output_dir, file_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not force_overwrite and os.path.exists(output_file):
            console.print(
                f"[bold yellow]{output_file} already exists. Skipping...[/bold yellow]"
            )
        else:
            console.print(f"[bold green]Writing to {output_file}...[/bold green]")

            # Unescape special characters in the contents before writing to file
            unescaped_contents = xml.sax.saxutils.unescape(contents)

            with open(output_file, "w") as f:
                f.write(unescaped_contents)
                f.close()
