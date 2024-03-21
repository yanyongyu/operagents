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

### Start writing a config file

Create a `config.yaml` file with the following basic content:

```yaml
# yaml-language-server: $schema=https://operagents.yyydl.top/schemas/config.schema.json

agents:
opening_scene: ""
scenes:
```

The first line is a comment that tells the YAML Language Server to use the schema from the specified URL. This will enable autocompletion and validation in your editor.  
The schema is related to the version of the operagents framework you are using. The URL is in the format `https://operagents.yyydl.top/schemas/config-<version>.schema.json`, where `<version>` is the version of the framework, e.g. `0.0.1`. If no version is specified, the latest (master) version will be used.

### The Template config

Before writing the agent and scene configs, we need to learn about the template config.

Operagents uses templates to generate the context input for the language model. A template is a string in [jinja](https://jinja.palletsprojects.com/) format. You can use jinja2 syntax with provided context varaibles to control the input to the language model.

A template config can be in the following format:

1. simple string template

   ```yaml
   user_template: |-
     {# some jinja template #}
   ```

2. template with custom functions

   ```yaml
   user_template:
     content: |-
       {# some jinja template #}
     custom_functions:
       function_name: module_name:function_name
   ```

If you want to use custom functions in the template, you need to provide the `custom_functions` key, which is a dictionary of custom function names and their corresponding module paths in dot notation format.

### The Agent config

The `agents` section is a dictionary of agents, where the key is the agent's name and the value is the agent's config.

The agents need to act as a character in the scenes and respond to others' messages. So, the first part of the agent config is the backend config, which is used to communicate with the language model or user. You can use the `backend` key to specify the backend type and its config.

```yaml
agents:
  Mike:
    backend:
      # user as the backend (a.k.a human-agent)
      type: user
  John:
    backend:
      # openai api as the backend
      type: openai
      model: gpt-3.5-turbo-16k-0613
      temperature: 0.5
```

The next part of the agent config is the system/user template used to generate the context input for the language model. You can use the `system_template`/`user_template` key to specify the system/user template. Here is an example of the template config:

```yaml
agents:
  John:
    system_template: |-
      Your name is {{ agent.name }}.
      Current scene is {{ timeline.current_scene.name }}.
      {% if timeline.current_scene.description -%}
      {{ timeline.current_scene.description }}
      {%- endif -%}
      You are acting as {{ timeline.current_character.name }}.
      {% if timeline.current_character.description -%}
      {{ timeline.current_character.description }}
      {%- endif -%}
      Please continue the conversation on behalf of {{ agent.name }}({{ timeline.current_character.name }}) based on your known information and make your answer appear as natural and coherent as possible.
      Please answer directly what you want to say and keep your reply as concise as possible.
    user_template: |-
      {% for event in timeline.past_events(agent) -%}
      {% if event.type_ == "act" -%}
      {{ event.character.agent_name }}({{ event.character.name }}): {{ event.content }}
      {%- endif %}
      {%- endfor %}
```

Another part of the agent config is the scene summary system/user template, which is used to generate the summary of the scene. You can use the `scene_summary_system_template`/`scene_summary_user_template` key to specify the scene summary system/user template. Here is an example of the template config:

```yaml
agents:
  John:
    scene_summary_system_template: |-
      Your name is {{ agent.name }}.
      Your task is to summarize the historical dialogue records according to the current scene, and summarize the most important information.
    scene_summary_user_template: |-
      {% for event in agent.memory.get_memory_for_scene(scene) -%}
      {% if event.type_ == "observe" -%}
      {{ event.content }}
      {%- elif event.type_ == "act" -%}
      {{ agent.name }}({{ event.character.name }}): {{ event.content }}
      {%- endif %}
      {%- endfor %}
      {% for event in timeline.past_events_in_scene(agent, scene) -%}
      {% if event.type_ == "act" -%}
      {{ event.character.agent_name }}({{ event.character.name }}): {{ event.content }}
      {%- endif %}
      {%- endfor %}
```

### Opening scene config

The `opening_scene` key is used to specify the start scene of the opera. The value is the name of the opening scene.

```yaml
opening_scene: "Introduction"
```

### The Scene config

## Examples

### Chatbot

```bash
cd examples/chatbot
env OPENAI_API_KEY=sk-xxx OPENAI_BASE_URL=https://api.openai.com/v1 operagents run --log-level DEBUG config.yaml
```

## Development

Open in Codespaces (Dev Container):

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=master&repo=767939984)

Or install the development environment locally with:

```bash
poetry install && poetry run pre-commit install
```
