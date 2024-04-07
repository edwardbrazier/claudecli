"""
This module provides a command-line interface for interacting with the Anthropic AI model.
It allows users to provide context from local files or directories, set various options,
and engage in a conversational session with the model.
"""

# import atexit
# from anthropic import Client
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
# from prompt_toolkit.history import FileHistory
# from rich.console import Console
# from rich.logging import RichHandler
# from rich.markdown import Markdown
from typing import Optional, List
# from xdg_base_dirs import xdg_config_home

from ai_functions import setup_client
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
         "Repeat this option and its argument any number of times. "
         "The codebase will only be loaded once. ",
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
# @click.option(
#     "-c",
#     "--context",
#     "context_files",
#     type=click.File("r"),
#     help="Path to a context file",
#     multiple=True,
#     required=False
# )
@click.option(
    "-m", 
    "--model", 
    "model", 
    help="Set the model. In ascending order of capability, the options are: 'haiku', 'sonnet', 'opus'",
    required=False
)
@click.option(
    "-ml", 
    "--multiline", 
    "multiline", 
    is_flag=True, 
    help="Use the multiline input mode. "
         "To submit a multiline input in Bash on Windows, press Escape and then Enter.",
    required=False
)
# @click.option(
#     "-r",
#     "--restore",
#     "restore",
#     help="Restore a previous chat session (input format: YYYYMMDD-hhmmss or 'last')",
#     required=False
# )
# @click.option(
#     "-n",
#     "--non-interactive",
#     "non_interactive",
#     is_flag=True,
#     help="Non interactive/command mode for piping",
#     required=False
# )
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
@click.option(
    "-csp",
    "--coder-system-prompt",
    "coder_system_prompt",
    type=click.Path(exists=True),
    help="Path to the file containing the Coder System Prompt. Defaults to '~/.claudecli_coder_system_prompt.txt'.",
    required=False
)
@click.option(
    "-gsp",
    "--general-system-prompt",
    "general_system_prompt",
    type=click.Path(exists=True),
    help="Path to the file containing the General System Prompt. Defaults to '~/.claudecli_general_system_prompt.txt'.",
    required=False
)
def main(
    sources: List[str], 
    # context_files: List[click.File], 
    model: Optional[str], 
    multiline: bool, 
    # restore: Optional[str], 
    # non_interactive: bool, 
    file_extensions: Optional[str], 
    output_dir: Optional[str], 
    force: bool,
    coder_system_prompt: Optional[str],
    general_system_prompt: Optional[str]
) -> None:
    """
    Command-line interface to the Anthropic Claude AI.
    Supports chat conversations.
    Also supports code output from Claude to multiple files at once.

    Write '/q' to end the chat.
    Write '/o <instructions>' to ask Claude for code, which the application will output to the selected output directory.
    '<instructions>' represents your instructions to Claude.
    """

    # If non interactive suppress the logging message
    # if non_interactive:
        # console.print("[red bold]Error[/red bold]")

    console.print("[bold]ClaudeCLI[/bold]")

    # history = FileHistory(str(constants.HISTORY_FILE))

    if multiline:
        session: PromptSession[str] = PromptSession(multiline=True)
    else:
        session: PromptSession[str] = PromptSession()

    try:
        config = load.load_config(logger=logger, config_file=str(constants.CONFIG_FILE)) # type: ignore
    except FileNotFoundError:
        console.print("[red bold]Configuration file not found[/red bold]")
        sys.exit(1)

    # save.create_save_folder()

    # Check proxy setting
    # if config["use_proxy"]:
    #     proxy = {"http": config["proxy"], "https": config["proxy"]}
    # else:
    #     proxy = None

    # Order of precedence for API Key configuration:
    # Command line option > Environment variable > Configuration file
    
    # If the --key command line argument is used, overwrite the configuration
    # if api_key:
        # config["anthropic_api_key"] = api_key.strip()

    model_mapping: dict[str,str] = {
        "opus": constants.opus,
        "sonnet": constants.sonnet,
        "haiku": constants.haiku
    }

    config["non_interactive"] = False

    # Do not emit markdown in non-interactive mode, as ctrl character formatting interferes in several contexts including json output.
    if config["non_interactive"]:
        config["markdown"] = False

    config["json_mode"] = False

    # copyable_blocks = {} if config["easy_copy"] else None # type: ignore

    # If the config specifies a model and the command line parameters do not specify a model, then
    # use the one from the config file.
    if model:
        # First check whether the provided model is valid
        if model not in model_mapping:
            console.print(
                f"[red bold]Invalid model: {model}[/red bold]"
            )
            sys.exit(1)
        else:
            model_notnone: str = model_mapping.get(model.lower(), model)
            config["anthropic_model"] = model_notnone
    elif "anthropic_model" not in config:
        config["anthropic_model"] = constants.haiku

    # Run the display expense function when exiting the script
#    atexit.register(print.display_expense, logger=logger, model=model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    # config["supplier"] = "anthropic"

    # logger.info(
        # f"Supplier: [green bold]{config['supplier']}", extra={"highlighter": None}
    # )
    console.print(f"Model in use: [green bold]{config['anthropic_model']}[/green bold]")
    console.line()

    # Add the system message for code blocks in case markdown is enabled in the config file
    # if config["markdown"]:
        # add_markdown_system_message()

    # initial_context: Optional[str] = None
    codebase: Optional[load.Codebase] = None
    extensions: list[str] = []

    # Source code location from command line option
    if sources:        
        if file_extensions is not None and file_extensions != "":
            console.print(
                f"Looking only at source files with extensions: [green bold]{file_extensions}[/green bold]"
            )
            extensions = [ext.strip() for ext in file_extensions.split(",")]

        for source in sources:
            console.print(
                f"Codebase location: [green bold]{source}[/green bold]"
            )

            extensions = []

            try:
                new_codebase = load.load_codebase(source, extensions)

                if codebase is None:
                    codebase = new_codebase
                else:
                    codebase += new_codebase

                console.line()
            except FileNotFoundError as e:
                console.print(f"Error reading codebase: {e}")

        if codebase is None:
            console.print(
                "[red bold]Codebase could not be loaded. Please check the source code location and try again.[/red bold]")
        else:
            # TODO: move this bit to load.py
            codebase.concatenated_contents = \
                f"\n<codebase>\n{codebase.concatenated_contents}\n</codebase>\n"

            # Show the user how big the entire codebase is, in kb. 
            console.print(
                f"Codebase size: [green bold]{pure.get_size(codebase.concatenated_contents)}[/green bold]\n"
            )


        # initial_context = codebase.concatenated_contents

    if coder_system_prompt is None:
        coder_system_prompt = os.path.expanduser("~/.claudecli_coder_system_prompt.txt")
    if general_system_prompt is None:  
        general_system_prompt = os.path.expanduser("~/.claudecli_general_system_prompt.txt")

    try:
        with open(coder_system_prompt, "r") as f:
            system_prompt_code = f.read()
    except FileNotFoundError:
        console.print("[bold yellow]Coder System Prompt file not found. Using empty prompt.[/bold yellow]")
        system_prompt_code = ""

    try:  
        with open(general_system_prompt, "r") as f:
            system_prompt_general = f.read()
    except FileNotFoundError:
        console.print("[bold yellow]General System Prompt file not found. Using default prompt.[/bold yellow]")

        system_prompt_general =    "You are a helpful AI assistant which answers questions about programming. " \
                                        "Always use code blocks with the appropriate language tags. " \
                                        "If asked for a table, always format it using Markdown syntax."
        console.print("[bold yellow]Default General System Prompt:[/bold yellow]")
        console.print(system_prompt_general)

    # # Context from the command line option
    # if context_files:
    #     for c in context_files:
    #         logger.info(
    #             f"Context file: [green bold]{c.name}", extra={"highlighter": None}
    #         )
    #         initial_context = codebase
    #         messages.append({"role": "user", "content": c.read().strip()})

    # Restore a previous session
    # if restore:
    #     if restore == "last":
    #         last_session = load.get_last_save_file()
    #         restore_file = f"claudecli-session-{last_session}.json"
    #     else:
    #         restore_file = f"claudecli-session-{restore}.json"
    #     try:
    #         history_data = load.load_history_data(os.path.join(constants.SAVE_FOLDER, restore_file)) # type: ignore
    #         for message in history_data["messages"]: #  type: ignore
    #             messages.append(message) # type: ignore

    #         logger.info(
    #             f"Restored session: [bold green]{restore}",
    #             extra={"highlighter": None},
    #         )
    #     except FileNotFoundError:
    #         logger.error(
    #             f"[red bold]File {restore_file} not found", extra={"highlighter": None}
    #         )

    # if not non_interactive:
        # console.rule()

    conversation_history: Optional[ConversationHistory] = []

    api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")

    if api_key is None:
        console.print("[bold red]Please set the ANTHROPIC_API_KEY environment variable.[/bold red]")
        sys.exit(1)

    if output_dir is not None:
        output_dir_notnone: str = output_dir
    else:
        output_dir_notnone: str = os.getcwd()

    console.line()
    console.print(f"Output files will be written to: [bold green]{output_dir_notnone}[/bold green]\n")

    client: Client = setup_client(api_key) # type: ignore

    while True:
        context: Optional[str]

        if codebase is not None and conversation_history == []:
            context = codebase.concatenated_contents
        else:
            context = None

        prompt_outcome = \
            prompt_user(client, # type: ignore
                        context,
                        conversation_history, 
                        session, 
                        config, 
                        output_dir_notnone, 
                        force,
                        system_prompt_code,
                        system_prompt_general
                        )
        if isinstance(prompt_outcome, UserPromptOutcome):
            if prompt_outcome == UserPromptOutcome.CONTINUE:
                continue
            else:
                break
        else:
            conversation_history = prompt_outcome

if __name__ == "__main__":
    main()