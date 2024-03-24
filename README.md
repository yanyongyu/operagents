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
      api_key:
      base_url:
```

You can also customize the backend by providing a object path of the custom backend class that implements the `Backend` abstract class.:

```yaml
agents:
  Mike:
    backend:
      type: custom
      path: module_name:CustomBackend
      custom_config: value
```

```python
# module_name.py

from typing import Self

from operagents.prop import Prop
from operagents.backend import Backend, Message
from operagents.config import CustomBackendConfig


class CustomBackend(Backend):
    @classmethod
    def from_config(cls, config: CustomBackendConfig) -> Self:
        return cls()

    async def generate(
        self, messages: list[Message], props: list[Prop] | None = None
    ) -> str:
        return ""
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

The `scenes` section is a dictionary of scenes, where the key is the scene's name and the value is the scene's config.

The opera is composed of multiple scenes, and each scene has a number of characters. You first need to define the name, description (optional), and characters of the scene.

```yaml
scenes:
  talking:
    description: "The scene is about two people talking."
    characters:
      user:
        agent_name: "Mike"
      ai assistant:
        agent_name: "John"
        description: |-
          You are a helpful assistant.
        props: []
```

The characters in the scene must define the `agent_name` key, which is the name of the agent acting as the character. The `description` key (optional) can be used to describe the character in the agent template. The `props` key (optional) can be used to define the props of the character, see [the Prop config](#the-prop-config) for more details.

The `Flow` of the scene is designed to control the order of the characters' acting. You can specify the type and the parameters of the `Flow`.

1. `order` type

   The `order` type is used to pre-define the order of the characters' acting. The characters will cycle through the order list until the scene ends.

   ```yaml
   scenes:
     talking:
       flow:
         type: order
         order:
           - user
           - ai assistant
   ```

2. `model` type

   The `model` type is used to specify the model to predict the next character to act. The model will predict the next character based on the current context.

   ```yaml
   scenes:
     talking:
       flow:
         type: model
         backend:
           type: openai
           model: gpt-3.5-turbo-16k-0613
           temperature: 0.5
         system_template: ""
         user_template: ""
         allowed_characters: # optional, the characters allowed to act
           - user
           - ai assistant
         begin_character: user # optional, the first character to act
         fallback_character: ai assistant # optional, the fallback character when the model fails to predict
   ```

3. `user` type

   The `user` type allows human to choose the next character to act.

   ```yaml
   scenes:
     talking:
       flow:
         type: user
   ```

4. `custom` type

   The `custom` type allows you to define a custom flow class to control the order of the characters' acting.

   ```yaml
   scenes:
     talking:
       flow:
         type: custom
         path: module_name:CustomFlow
         custom_config: value
   ```

   ```python
   # module_name.py

   from typing import Self

   from operagents.flow import Flow
   from operagents.timeline import Timeline
   from operagents.character import Character
   from operagents.config import CustomFlowConfig


   class CustomFlow(Flow):
       @classmethod
       def from_config(cls, config: CustomFlowConfig) -> Self:
           return cls()

       async def begin(self, timeline: Timeline) -> Character:
           return ""

       async def next(self, timeline: Timeline) -> Character:
           return ""
   ```

The `Director` of the scene is used to control the next scene to play. You can specify the type and the parameters of the Director.

1. `model` type

   The `model` type is used to specify the model to predict the next scene to play. If no finish flag found or no scene name found, the curent scene will continue to play.

   ```yaml
   scenes:
     talking:
       director:
         type: model
         backend:
           type: openai
           model: gpt-3.5-turbo-16k-0613
           temperature: 0.5
         system_template: ""
         user_template: ""
         allowed_scenes: # optional, the next scenes allowed to play
           - walking
           - running
         finish_flag: "finish" # optional, the finish flag to end the opera
   ```

2. `user` type

   The `user` type allows human to choose the next scene to play.

   ```yaml
   scenes:
     talking:
       director:
         type: user
   ```

3. `never` type

   The `never` Director never ends the current scene. Useful when there is a single scene and you want to end the opera by a `Prop`.

   ```yaml
   scenes:
     talking:
       director:
         type: never
   ```

4. `custom` type

   The `custom` type allows you to define a custom director class to control the next scene to play.

   ```yaml
   scenes:
     talking:
       director:
         type: custom
         path: module_name:CustomDirector
         custom_config: value
   ```

   ```python
   # module_name.py

   from typing import Self

   from operagents.scene import Scene
   from operagents.director import Director
   from operagents.timeline import Timeline
   from operagents.config import CustomDirectorConfig

   class CustomDirector(Director):
       @classmethod
       def from_config(cls, config: CustomDirectorConfig) -> Self:
           return cls()

       async def next_scene(self, timeline: Timeline) -> Scene | None:
           return None
   ```

### The Prop config

The characters in the scene can use props to improve there acting. The `props` section is a list of props, where each prop is a dictionary with the prop type and the prop config.

1. `function` Prop

   The `function` prop will call the custom function when the prop is used.

   ```yaml
   scenes:
     talking:
       characters:
         ai assistant:
           props:
             - type: function
               function: module_name:function_name
   ```

   The custom function should has no arguments or one argument of type `pydantic.BaseModel`.

   ```python
   from pydantic import Field, BaseModel
   from datetime import datetime, timezone

   async def current_time() -> str:
       """Get the current real world time."""
       return datetime.now(timezone.utc).astimezone().isoformat()

   class Args(BaseModel):
       name: str = Field(description="The name")

   async def greet(args: Args) -> str:
       """Greet the name."""
       return f"Hello, {args.name}!"
   ```

   Note that the function's name and docstring will be used as the prop's name and description. You can also provide the description of the args by pydantic's `Field`.

2. `custom` Prop

   The `custom` prop will call the custom prop class when the prop is used.

   ```yaml
   scenes:
     talking:
       characters:
         ai assistant:
           props:
             - type: custom
               path: module_name:CustomProp
               custom_config: value
   ```

   ```python
   # module_name.py

   from typing import Any, Self

   from pydantic import BaseModel
   from operagents.prop import Prop
   from operagents.config import CustomPropConfig

   class CustomProp(Prop):
       """The description of the prop"""

       params: BaseModel | None
       """The parameters of the prop"""

       @classmethod
       def from_config(cls, config: CustomPropConfig) -> Self:
           return cls()

       async def call(self, params: BaseModel | None) -> Any:
           return ""
   ```

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
