# Claude CLI


## Overview

Command line interface to Claude, for chatting and generating code.

## How to get an API Key

TODO

## Installation and essential configuration

TODO

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
