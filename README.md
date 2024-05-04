# ClaudeCLI


## Overview

Command line interface to Anthropic's Claude, oriented around programming.

This is a developer tool. The distinctive feature of this tool is that it can put codebases into the context for Claude, so that Claude can see all of your code when giving advice, writing new code and writing modifications to the code. It supports both a chat interface and a command for sending Claude's output into multiple source files.

The author of this tool is not affiliated in any way with Anthropic, which owns the Claude model.

## How to get an API Key

As of April 2024: To get an API Key to access Claude, go to the Anthropic website and select the 'API' page, which is titled 'Build with Claude'.

## Installation and essential configuration

Before you run ClaudeCLI, put your Anthropic API key into the environment variable ANTHROPIC_API_KEY. 

There are two ways of running this program:
1. From the Windows exe file ./dist/claudecli.exe, which depends on some other local files.
2. From the source code, using Python. (See [CONTRIBUTING.md](CONTRIBUTING.md))

The supported shells are:
1. Powershell on Windows 11
2. Bash on WSL (Ubuntu)

It is likely that Bash on other Linux flavours will also work.

The Windows Command Prompt is not supported and will not work properly.

### Configuration file

The configuration file *config.yaml* can be found in the default config directory of the user defined by the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).

On a Linux/MacOS system it is defined by the $XDG_CONFIG_HOME variable (check it using `echo $XDG_CONFIG_HOME`). The default, if the variable is not set, should be the `~/.config` folder.

On the first execution of the script, a [template](config.yaml) of the config file is automatically created. If a config file already exists but is missing any fields, default values are used for the missing fields.

## Models

As of May 2024, ClaudeCLI supports all three models in the Claude 3 series: haiku, sonnet and opus.

Haiku is the fastest and cheapest model. Opus is the most capable. Sonnet is in between.

## Basic usage

Here is a usage example on Windows in Powershell.

Start from any folder that you have read/write access to.

```
> git clone https://github.com/edwardbrazier/claudecli.git
> cd claudecli
> mkdir out
> cd dist\claudecli
> # Start with a simple example
> .\claudecli.exe
>>> What is the capital of New Zealand?
The capital of New Zealand is Wellington.
>>> /q
> # Now a more complex example.
> .\claudecli.exe -s ..\..\claudecli -e py,txt -m haiku -o ..\..\out -csp ..\..\claudecli\coder_system_prompt.txt
>>> Summarise.
This codebase provides a command-line interface for interacting with the Anthropic Claude AI model. It allows users to
provide context from local files or directories, set various options, and engage in a conversational session with the
model. The key features of this codebase include:

 1 Loading and processing a codebase as context for the AI model.
 2 Handling user prompts and generating responses from the AI model.
 3 Saving the AI's output to files, including the concatenated output and any generated code files.
 4 Parsing the AI's XML-formatted responses to extract the generated code and file changes.
 5 Providing a system prompt for the AI to follow specific formatting and style guidelines.
 6 Handling exceptions and errors that may occur during the interaction with the AI model.
 7 Providing configuration options and loading/saving session history.

The codebase is structured into several modules, each with its own responsibilities, such as ai_functions, parseaicode,
printing, load, save, and interact. The main entry point is the __main__.py file, which handles the command-line
interface and coordinates the various components.
>>> /q
> ls ..\..\out
```

Sometimes you need to press Enter an extra time to get ClaudeCLI's result.

In the above command, the '-s' parameter specifies the codebase to supply to Claude as context, the '-e' parameter specifies which file extensions to look at in the codebase, '-m' is the AI model to use, '-o' is the output directory and '-csp' is the system prompt for outputting code to files. (A different system prompt is used when outputting code to the shell.)

You can then use the diff / merge function in your IDE to compare Claude's output (in ..\..\out\ai_functions.py) with your existing file (..\..\claudecli\ai_functions.py) and merge the differences.

When you use '/o' to direct ClaudeCLI to output its response to a code file, ClaudeCLI will also produce a file called concatenated_output.txt in the output directory (in this case ..\..\out). This file has the raw output of Claude. If Claude's output is malformed and can't be divided into separate code files by ClaudeCLI's parser, then you can look at concatenated_output.txt to see whether the raw output of Claude is useful to you.

To get more usage instructions, run:
```
> cd dist\claudecli
> .\claudecli.exe --help
```

Here is the output:
```
Usage: python -m claudecli [OPTIONS]

  Command-line interface to the Anthropic Claude AI. Supports chat
  conversations. Also supports code output from Claude to multiple files at
  once.

  Write '/q' to end the chat. Write '/o <instructions>' to ask Claude for
  code, which the application will output to the selected output directory.
  '<instructions>' represents your instructions to Claude. For example:  >>>
  /o improve the commenting in load.py

Options:
  -s, --source PATH               Pass an entire codebase to the model as
                                  context, from the specified location. Repeat
                                  this option and its argument any number of
                                  times. The codebase will only be loaded
                                  once.
  -e, --file-extensions TEXT      File name extensions of files to look at in
                                  the codebase, separated by commas without
                                  spaces, e.g. py,txt,md Only use this option
                                  once, even for multiple codebases.
  -m, --model TEXT                Set the model. In ascending order of
                                  capability, the options are: 'haiku',
                                  'sonnet', 'opus'
  -ml, --multiline                Use the multiline input mode. To submit a
                                  multiline input in Bash on Windows, press
                                  Escape and then Enter.
  -o, --output-dir PATH           The output directory for generated files
                                  when using the /o command. Defaults to the
                                  current working directory.
  -f, --force                     Force overwrite of output files if they
                                  already exist.
  -csp, --coder-system-prompt PATH
                                  Path to the file containing the Coder System
                                  Prompt. Defaults to
                                  '~/.claudecli_coder_system_prompt.txt'.
  -gsp, --general-system-prompt PATH
                                  Path to the file containing the General
                                  System Prompt. Defaults to
                                  '~/.claudecli_general_system_prompt.txt'.
  --help                          Show this message and exit.
```

## Multiline input

Add the `--multiline` (or `-ml`) flag in order to toggle multi-line input mode. In this mode use `Alt+Enter` or `Esc+Enter` to submit messages.

## Context

The distinctive feature of ClaudeCLI is that it allows you to put entire codebases into the context for the AI.

To provide multiple codebases, use the '-s' option multiple times, like this (Powershell):
```
> .\claudecli.exe -s .\codebase1\src -s .\codebase2\src -e py,txt -m haiku -o .\out -csp ..\..\claudecli\coder_system_prompt.txt
```

## Markdown rendering

By default, ClaudeCLI asks Claude for Markdown and renders its output with some formatting.
This can be turned off in the configuration file.

## Contributing to this project

Please read [CONTRIBUTING.md](CONTRIBUTING.md)
