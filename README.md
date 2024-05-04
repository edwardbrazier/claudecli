# Claude CLI


## Overview

Command line interface to Anthropic's Claude, for chatting and generating code.
This is a developer tool.
The distinctive feature of this tool is that it can put codebases into the context for Claude, so that Claude can see all of your code when giving advice, writing new code and writing modifications to the code.

The author of this tool is not affiliated in any way with Anthropic, which owns the Claude model.

## How to get an API Key

As of April 2024: To get an API Key to access Claude, go to the Anthropic website and select the 'API' page, which is titled 'Build with Claude'.

## Installation and essential configuration

There are two ways of running this program:
1. From the Windows exe file ./dist/claudecli.exe, which depends on some other local files.
2. From the source code, using Python.

The supported shells are:
1. Powershell on Windows
2. Bash

The Windows Command Prompt is not supported and will not work properly.

Here is a usage example on Windows in Powershell:
```
> cd dist/claudecli
> .\claudecli.exe -s ..\..\claudecli -e py,txt -m haiku -o out -csp ..\..\claudecli\coder_system_prompt.txt
>>> Summarise.
>>> /o Rewrite ai_functions.py to force the model to opus.
>>> /q
```

### Configuration file

The configuration file *config.yaml* can be found in the default config directory of the user defined by the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).

On a Linux/MacOS system it is defined by the $XDG_CONFIG_HOME variable (check it using `echo $XDG_CONFIG_HOME`). The default, if the variable is not set, should be the `~/.config` folder.

On the first execution of the script, a [template](config.yaml) of the config file is automatically created. If a config file already exists but is missing any fields, default values are used for the missing fields.


## Models

TODO

## Basic usage

TODO

## Multiline input

Add the `--multiline` (or `-ml`) flag in order to toggle multi-line input mode. In this mode use `Alt+Enter` or `Esc+Enter` to submit messages.

## Context

TODO

## Markdown rendering

TODO

## Restoring previous sessions

TODO

## Piping

TODO

## Contributing to this project

Please read [CONTRIBUTING.md](CONTRIBUTING.md)
