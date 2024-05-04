## How to contribute to ClaudeCLI

Contributions to this project are welcome! 

### Philosophy

The philosophy behind this tool is to provide a way for Claude to write code for you and provide advice, even if you don't know your way around the codebase well enough to provide the right files as context.

Some elements of the code style are specified (for Claude's benefit) in coder_system_prompt.txt. This project uses Black (https://github.com/psf/black) as a code formatter (Most IDE have an extension that makes straightforward to use it). Please format the code using this tool before submitting a PR.

### Development

Check out the repository:
```
git clone https://github.com/edwardbrazier/claudecli.git
cd claudecli
```

Create and activate a Virtual Environment:

`python3 -m venv venv` or `python -m venv venv`

`source venv/bin/activate` (Linux/MacOS) or `.\venv\Scripts\activate` (Windows)

Install the requirements:

`pip install -r requirements.txt`

Run the code during development:

`python3 -m claudecli`

After the changes are done don't forget to:

- update `requirements.txt` and `setup.cfg` if necessary
- update `README.md` if necessary
- update `pyproject.toml` with a new version number
- test if the installation as a package still works as expected using `pip install .` and running `claudecli`

