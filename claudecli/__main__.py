"""
This module provides a command-line interface for interacting with the Anthropic AI model.
It allows users to provide context from local files or directories, set various options,
and engage in a conversational session with the model.
"""

# import atexit
import click
# import datetime
# import json
# import logging
import os
# import pyperclip
# import re
# import requests
import sys
# import yaml
# import anthropic

# from pathlib import Path
from prompt_toolkit import PromptSession #, HTML
from prompt_toolkit.history import FileHistory
# from rich.console import Console
# from rich.logging import RichHandler
# from rich.markdown import Markdown
from typing import Optional, List
# from xdg_base_dirs import xdg_config_home

import pure
from interact import *
import constants
import load

@click.command()
@click.option(
    "-s",
    "--source",
    "sources",
    type=click.Path(exists=True),
    help="Pass an entire codebase to the model as context, from the specified location. "
         "Repeat this option and its argument any number of times.",
    multiple=True,
    required=False
)
@click.option(
    "-e", 
    "--file-extensions", 
    "file_extensions",
    help="File name extensions of files to look at in the codebase, separated by commas without spaces, e.g. py,txt,md "
         "Only use this option once, even for multiple codebases.",
    required=False
)
@click.option(
    "-c",
    "--context",
    "context",
    type=click.File("r"),
    help="Path to a context file",
    multiple=True,
    required=False
)
@click.option(
    "-k", 
    "--key", 
    "api_key", 
    help="Set the API Key",
    required=False
)
@click.option(
    "-m", 
    "--model", 
    "model", 
    help="Set the model",
    required=False
)
@click.option(
    "-ml", 
    "--multiline", 
    "multiline", 
    is_flag=True, 
    help="Use the multiline input mode",
    required=False
)
@click.option(
    "-r",
    "--restore",
    "restore",
    help="Restore a previous chat session (input format: YYYYMMDD-hhmmss or 'last')",
    required=False
)
@click.option(
    "-n",
    "--non-interactive",
    "non_interactive",
    is_flag=True,
    help="Non interactive/command mode for piping",
    required=False
)
@click.option(
    "-j", 
    "--json", 
    "json_mode", 
    is_flag=True, 
    help="Activate json response mode",
    required=False
)
@click.option(
    "-o",
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True),
    help="The output directory for generated files when using the /o command. "
        "Defaults to the current working directory.",
    required=False
)
@click.option(
    "-f",
    "--force",
    "force",
    is_flag=True,
    help="Force overwrite of output files if they already exist.",
    required=False
)
def main(
    sources: List[str], 
    context: List[click.File], 
    api_key: Optional[str], 
    model: Optional[str], 
    multiline: bool, 
    restore: Optional[str], 
    non_interactive: bool, 
    json_mode: bool,
    file_extensions: Optional[str], 
    output_dir: Optional[str], 
    force: bool
) -> None:
    """
    Main entry point for the CLI.

    Args:
        sources (List[str]): Paths to directories containing source code to provide as context.
        context (List[File]): Files containing additional context to provide.
        api_key (str): API key to use for authentication.
        model (str): Name of the AI model to use.
        multiline (bool): Whether to enable multiline input mode.
        restore (str): Identifier for a previous chat session to restore.
        non_interactive (bool): Whether to run in non-interactive mode (for piping).
        json_mode (bool): Whether to enable JSON response mode.
        file_extensions (str): Comma-separated list of file extensions to consider in source directories.
        output_dir (str): The output directory for generated files when using the /o command.
        force (bool): Whether to force overwrite of output files if they already exist.

    Preconditions:
        - The provided source directories and context files must exist and be readable.
        - The API key must be valid and have sufficient permissions.

    Side effects:
        - Prints output to the console.
        - Saves chat history to disk.
        - Copies output to the clipboard (if enabled).
        - Writes generated files to the output directory when using the /o command.

    Exceptions:
        - FileNotFoundError: Raised if a provided source directory or context file does not exist.
        - Other exceptions may be raised by external libraries or the AI model.

    Returns:
        None
    """

    # If non interactive suppress the logging messages
    if non_interactive:
        logger.setLevel("ERROR")

    logger.info("[bold]Claude CLI", extra={"highlighter": None})

    history = FileHistory(str(constants.HISTORY_FILE))

    if multiline:
        session: PromptSession[str] = PromptSession(history=history, multiline=True)
    else:
        session: PromptSession[str] = PromptSession(history=history)

    try:
        config = load.load_config(logger=logger, config_file=str(constants.CONFIG_FILE)) # type: ignore
    except FileNotFoundError:
        logger.error(
            "[red bold]Configuration file not found", extra={"highlighter": None}
        )
        sys.exit(1)

    save.create_save_folder()

    # Check proxy setting
    # if config["use_proxy"]:
    #     proxy = {"http": config["proxy"], "https": config["proxy"]}
    # else:
    #     proxy = None

    # Order of precedence for API Key configuration:
    # Command line option > Environment variable > Configuration file

    # If the environment variable is set, overwrite the configuration
    if os.environ.get(constants.ENV_VAR_ANTHROPIC):
        config["anthropic_api_key"] = os.environ[constants.ENV_VAR_ANTHROPIC].strip()
    
    # If the --key command line argument is used, overwrite the configuration
    if api_key:
        config["anthropic_api_key"] = api_key.strip()

    model_mapping: dict[str,str] = {
        "opus": constants.opus,
        "sonnet": constants.sonnet,
        "haiku": constants.haiku
    }

    config["non_interactive"] = non_interactive

    # Do not emit markdown in non-interactive mode, as ctrl character formatting interferes in several contexts including json output.
    if config["non_interactive"]:
        config["markdown"] = False

    config["json_mode"] = json_mode

    copyable_blocks = {} if config["easy_copy"] else None # type: ignore

    # If the config specifies a model and the command line parameters do not specify a model, then
    # use the one from the config file.
    if model:
        # First check whether the provided model is valid
        if model not in model_mapping:
            logger.error(
                f"[red bold]Invalid model: {model}", extra={"highlighter": None}
            )
            sys.exit(1)
        else:
            model_notnone: str = model_mapping.get(model.lower(), model)
            config["anthropic_model"] = model_notnone
    elif "anthropic_model" not in config:
        config["anthropic_model"] = constants.haiku

    # Run the display expense function when exiting the script
#    atexit.register(print.display_expense, logger=logger, model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    config["supplier"] = "anthropic"

    logger.info(
        f"Supplier: [green bold]{config['supplier']}", extra={"highlighter": None}
    )
    logger.info(f"Model in use: [green bold]{config['anthropic_model']}", extra={"highlighter": None})

    # Add the system message for code blocks in case markdown is enabled in the config file
    # if config["markdown"]:
        # add_markdown_system_message()

    initial_context = ""
    codebase: str = ""

    # Source code location from command line option
    if sources:
        for source in sources:
            logger.info(
                f"Codebase location: [green bold]{source}\n",
                extra={"highlighter": None},
            )
            logger.info(
                "The entire codebase will be prepended to your first message."
            )

            extensions = []

            if file_extensions is not None and file_extensions != "":
                logger.info(
                    f"Looking only at source files with extensions: [green bold]{file_extensions}\n",
                    extra={"highlighter": None},
                )
                extensions = [ext.strip() for ext in file_extensions.split(",")]

            try:
                codebase: str = load.load_codebase(logger, source, extensions)
                initial_context += codebase
                
                # Show the user how big the entire codebase is, in kb. 
                logger.info(
                    f"Codebase size: [green bold]{pure.get_size(codebase)}\n",
                )
            except FileNotFoundError as e:
                print(f"Error reading codebase: {e}")

    # Context from the command line option
    if context:
        for c in context:
            logger.info(
                f"Context file: [green bold]{c.name}", extra={"highlighter": None}
            )
            initial_context = codebase
    #         messages.append({"role": "user", "content": c.read().strip()})

    # Restore a previous session
    if restore:
        if restore == "last":
            last_session = load.get_last_save_file()
            restore_file = f"chatgpt-session-{last_session}.json"
        else:
            restore_file = f"chatgpt-session-{restore}.json"
        try:

            # If this feature is used --context is cleared
            messages.clear()
            history_data = load.load_history_data(os.path.join(constants.SAVE_FOLDER, restore_file)) # type: ignore
            for message in history_data["messages"]: #  type: ignore
                messages.append(message) # type: ignore

            logger.info(
                f"Restored session: [bold green]{restore}",
                extra={"highlighter": None},
            )
        except FileNotFoundError:
            logger.error(
                f"[red bold]File {restore_file} not found", extra={"highlighter": None}
            )

    if json_mode:
        logger.info(
            "JSON response mode is active. Your message should contain the [bold]'json'[/bold] word.",
            extra={"highlighter": None},
        )

    if not non_interactive:
        console.rule()

    while True:
        try:
            start_prompt(initial_context, session, config, copyable_blocks, None, output_dir, force)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break



if __name__ == "__main__":
    main()