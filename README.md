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
