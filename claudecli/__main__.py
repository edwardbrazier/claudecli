"""
This module provides a command-line interface for interacting with the Anthropic AI model.
It allows users to provide context from local files or directories, set various options,
and engage in a conversational session with the model.
"""

import click
import os
import sys

from prompt_toolkit import PromptSession
from typing import Optional

from claudecli.ai_functions import setup_client
from claudecli.interact import *
from claudecli import constants
from claudecli.load import load_codebase_state, load_codebase_xml_, load_config, load_file_xml  # type: ignore
from claudecli.codebase_watcher import Codebase, amend_codebase_records


@click.command()
@click.option(
    "-s",
    "--source",
    "sources",
    type=click.Path(exists=True),
    help="Pass files or directories to the model as context. "
    "Repeat this option and its argument any number of times. "
    "The files and directories will only be loaded once. ",
    multiple=True,
    required=False,
)
@click.option(
    "-e",
    "--file-extensions",
    "file_extensions",
    help="File name extensions of files to look at in the codebase, separated by commas without spaces, e.g. py,txt,md "
    "Only use this option once, even for multiple codebases.",
    required=False,
)
@click.option(
    "-m",
    "--model",
    "model",
    help="Set the model. In ascending order of capability, the options are: 'haiku', 'sonnet', 'opus'",
    required=False,
)
@click.option(
    "-ml",
    "--multiline",
    "multiline",
    is_flag=True,
    help="Use the multiline input mode. "
    "To submit a multiline input in Bash on Windows, press Escape and then Enter.",
    required=False,
)
@click.option(
    "-o",
    "--output-dir",
    "output_dir",
    type=click.Path(exists=True),
    help="The output directory for generated files when using the /o command. "
    "Defaults to the current working directory.",
    required=False,
)
@click.option(
    "-f",
    "--force",
    "force",
    is_flag=True,
    help="Force overwrite of output files if they already exist.",
    required=False,
)
@click.option(
    "-csp",
    "--coder-system-prompt",
    "coder_system_prompt_user",
    type=click.Path(exists=True),
    help="""
    Path to the file containing the Coder System Prompt. 
    Defaults to '~/.claudecli_coder_system_prompt.txt'. 
    This is additional to a hardcoded coder system prompt which tells Claude how to format its output in XML when it is asked to write code into some files.""",
    required=False,
)
@click.option(
    "-gsp",
    "--general-system-prompt",
    "general_system_prompt",
    type=click.Path(exists=True),
    help="""
    Path to the file containing the General System Prompt, used when asking for chat-style responses. 
    Defaults to '~/.claudecli_general_system_prompt.txt'.""",
    required=False,
)
@click.version_option(version=constants.VERSION, prog_name='claudecli')
def main(
    sources: list[str],
    model: Optional[str],
    multiline: bool,
    file_extensions: Optional[str],
    output_dir: Optional[str],
    force: bool,
    coder_system_prompt_user: Optional[str],
    general_system_prompt: Optional[str],
) -> None:
    """
    Command-line interface to the Anthropic Claude AI.
    Supports chat conversations.
    Also supports code output from Claude to multiple files at once.

    Write '/q' to end the chat.\n
    Write '/o <instructions>' to ask Claude for code, which the application will output to the selected output directory.
    '<instructions>' represents your instructions to Claude.
    For example:\n
    >>> /o improve the commenting in load.py\n
    Write '/p <instructions>' to render Claude's response as plain text.
    (This is a workaround in case Claude outputs malformed Markdown.)
    Write '/u' to check for changes in the watched codebases and prepend the contents of added or modified files to the next message. 
    (At the moment this only works if there is a single codebase.)
    """

    console.print("[bold]ClaudeCLI[/bold]")

    if multiline:
        session: PromptSession[str] = PromptSession(multiline=True)  # type: ignore
    else:
        session: PromptSession[str] = PromptSession()

    try:
        config = load_config(config_file=str(constants.CONFIG_FILE))  # type: ignore
    except FileNotFoundError:
        console.print("[red bold]Configuration file not found[/red bold]")
        sys.exit(1)

    model_mapping: dict[str, str] = {
        "opus": constants.opus,
        "sonnet": constants.sonnet,
        "haiku": constants.haiku,
    }

    config["non_interactive"] = False

    # Do not emit markdown in non-interactive mode, as ctrl character formatting interferes in several contexts including json output.
    if config["non_interactive"]:
        config["markdown"] = False

    config["json_mode"] = False

    # If the config specifies a model and the command line parameters do not specify a model, then
    # use the one from the config file.
    if model:
        # First check whether the provided model is valid
        if model not in model_mapping:
            console.print(f"[red bold]Invalid model: {model}[/red bold]")
            sys.exit(1)
        else:
            model_notnone: str = model_mapping.get(model.lower(), model)
            config["anthropic_model"] = model_notnone
    elif "anthropic_model" not in config:
        config["anthropic_model"] = constants.haiku

    console.print(f"Model in use: [green bold]{config['anthropic_model']}[/green bold]")

    codebases: list[Codebase] = []
    codebase_initial_contents: str = ""
    extensions: list[str] = []

    # Source code location from command line option
    if sources:

        if file_extensions is not None and file_extensions != "":
            console.line()
            console.print(
                f"Looking only at source files with extensions: [green bold]{file_extensions}[/green bold]"
            )
            extensions = [ext.strip() for ext in file_extensions.split(",")]

        # For each of the sources, determine if it's a file or directory,
        # load the appropriate codebase state, and add it to the list of codebases.
        for source in sources:
            if os.path.isfile(source):
                console.print(f"File location: [green bold]{source}[/green bold]")

                try:
                    codebase_state = load_codebase_state(source, extensions)
                    codebases.append(Codebase(source, codebase_state))
                    console.print("Loaded [green bold]1[/green bold] file.")
                except ValueError as e:
                    console.print(f"Error reading file: {e}")

                codebase_initial_contents += load_file_xml(source)
            elif os.path.isdir(source):
                console.print(f"Codebase location: [green bold]{source}[/green bold]")

                try:
                    codebase_state = load_codebase_state(source, extensions)
                    codebases.append(Codebase(source, codebase_state))
                    num_files = len(codebase_state.files)
                    console.print(
                        "Loaded [green bold]{}[/green bold] files.".format(num_files)
                    )
                except ValueError as e:
                    console.print(f"Error reading codebase: {e}")

                codebase_initial_contents += load_codebase_xml_(codebases, extensions)
            else:
                console.print(f"[red bold]Invalid source: {source}[/red bold]")

    if coder_system_prompt_user is None:
        coder_system_prompt_user = os.path.expanduser(
            "~/.claudecli_coder_system_prompt.txt"
        )
    if general_system_prompt is None:
        general_system_prompt = os.path.expanduser(
            "~/.claudecli_general_system_prompt.txt"
        )

    console.line()

    try:
        with open(coder_system_prompt_user, "r") as f:
            user_system_prompt_code = f.read()

        console.print(
            f"Coder System Prompt loaded from [bold green]{coder_system_prompt_user}[/bold green]"
        )
    except FileNotFoundError:
        console.print("Coder System Prompt file not found. Using default.")
        user_system_prompt_code = ""

    try:
        with open(general_system_prompt, "r") as f:
            system_prompt_general = f.read()
    except FileNotFoundError:
        console.print("General System Prompt file not found. Using default.")
        system_prompt_general = constants.general_system_prompt_default

    conversation_history: ConversationHistory = []

    api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")

    if api_key is None:
        console.print(
            "[bold red]Please set the ANTHROPIC_API_KEY environment variable.[/bold red]"
        )
        sys.exit(1)

    if output_dir is not None:
        output_dir_notnone: str = output_dir
    else:
        output_dir_notnone: str = os.getcwd()

    console.print(
        f"Code files from the AI will be written to this folder: [bold green]{output_dir_notnone}[/bold green]\n"
    )

    client: Client = setup_client(api_key)  # type: ignore
    codebase_updates: Optional[CodebaseUpdates] = None

    while True:
        context: Optional[str] = None

        if conversation_history == [] and codebase_updates is None:
            context = (
                "Here is a codebase. Read it carefully.\n\n"
                "\n\nCodebase:\n" + codebase_initial_contents + "\n\n"
            )
        elif conversation_history != [] and codebase_updates is None:
            context = ""
        elif conversation_history == [] and codebase_updates is not None:
            context = """
                Here is the initial codebase. Read it carefully.\n{}\n
                Changes observed when reloading codebase: \n{}\n
                """.format(
                codebase_initial_contents,
                codebase_updates.change_descriptive.change_contents,
            ) 
            codebases = amend_codebase_records(
                codebases, codebase_updates.codebase_changes
            )
            codebase_updates = None
        elif conversation_history != [] and codebase_updates is not None:
            context = "Changes observed when reloading codebase: \n{}".format(
                codebase_updates.change_descriptive.change_contents
            )
            codebases = amend_codebase_records(
                codebases, codebase_updates.codebase_changes
            )
            codebase_updates = None

        prompt_outcome = prompt_user(
            client,  # type: ignore
            context,
            conversation_history,
            session,
            config,
            output_dir_notnone,
            force,
            user_system_prompt_code,
            system_prompt_general,
            codebases,
            extensions,
        )
        if isinstance(prompt_outcome, UserPromptOutcome):
            if prompt_outcome == UserPromptOutcome.CONTINUE:
                continue
            else:
                break
        if isinstance(prompt_outcome, CodebaseUpdates):
            # TODO: Handle cases where there are multiple updates in a row
            # in between a pair of messages to the AI.
            # Need to get both the contents of the files and the descriptions of the changes to the AI in that case.
            codebase_updates = prompt_outcome
        else:
            conversation_history = prompt_outcome  # type: ignore


if __name__ == "__main__":
    main()
