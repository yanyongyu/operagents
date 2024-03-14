# Operagents

## Installation

Install the latest version with:

```bash
pip install operagents
# or use poetry
poetry add operagents
# or use pdm
pdm add operagents
# or use uv
uv pip install operagents
```

## Usage

### Writing a configuration file

Create a `config.yaml` file with the following basic content:

```yaml
# yaml-language-server: $schema=https://operagents.yyydl.top/schemas/config.schema.json

agents:
opening_scene: ""
scenes:
```

The first line is a comment that tells the YAML Language Server to use the schema from the specified URL. This will enable autocompletion and validation in your editor.  
The schema is related to the version of the operagents framework you are using. The URL is in the format `https://operagents.yyydl.top/schemas/config-<version>.schema.json`, where `<version>` is the version of the framework, e.g. `0.0.1`. If no version is specified, the latest (master) version will be used.

## Examples

### Chatbot

```bash
cd examples/chatbot
env OPENAI_API_KEY=sk-xxx OPENAI_BASE_URL=https://api.openai.com/v1 operagents run config.yaml
```

## Development

Open in Codespaces (Dev Container):

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=master&repo=767939984)

Or install the development environment locally with:

```bash
poetry install && poetry run pre-commit install
```
