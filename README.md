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

## Concepts

### Agent

An agent is a human or a language model that can act as [characters](#character) and use [props](#prop) in the opera scenes. The agent can communicate with others by observing and acting. Every agent has a backend (e.g. user, openai api) to generate the response and own memory to store the long-term / short-term information.

### Scene

A scene is a part of the opera that contains a number of [characters](#character). Every scene has a [flow](#flow) and a [director](#director) to control the whole [session](#session) process. The scene can also have a prepare section to do some initialization work before the scene starts.

### Character

A character is a role in the [scene](#scene). Every character has a name, a description, and a list of [props](#prop). When the scene starts, an agent will act as the character and communicate with others.

### Flow

The flow is used to control the order of the characters' acting in the [scene](#scene).

### Director

The director is used to decide whether to end the current scene and which scene to play next.

### Prop

A prop is a tool that can be used by the [agents](#agent) to improve their acting. Agents can get external information by using props.

### Timeline

The timeline is the main runtime component of the opera to manage the [session](#session) process. It runs the current session and switches between sessions. The timeline also records the global information of the opera, and can be shared by all agents.

### Session

A session indicates a single run of the scene. It contains an unique identifier and its corresponding scene.

## Usage

The common way to use operagents is to write a config file and run the opera with the `operagents` command-line tool.

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
      model: gpt-3.5-turbo
      temperature: 0.5
      api_key:
      base_url:
      max_retries: 2
      tool_choice:
        type: auto
      prop_validation_error_template: |-
        {# some jinja template #}
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
      {% if event.type_ == "session_act" -%}
      {{ event.character.agent_name }}({{ event.character.name }}): {{ event.content }}
      {%- endif %}
      {%- endfor %}
```

Another part of the agent config is the session summary system/user template, which is used to generate the summary of the scene session. You can use the `session_summary_system_template`/`session_summary_user_template` key to specify the session summary system/user template. Here is an example of the template config:

```yaml
agents:
  John:
    session_summary_system_template: |-
      Your name is {{ agent.name }}.
      Your task is to summarize the historical dialogue records according to the current scene, and summarize the most important information.
    session_summary_user_template: |-
      {% for event in agent.memory.get_memory_for_session(session_id) -%}
      {% if event.type_ == "observe" -%}
      {{ event.content }}
      {%- elif event.type_ == "act" -%}
      {{ agent.name }}({{ event.character.name }}): {{ event.content }}
      {%- endif %}
      {%- endfor %}
      {% for event in timeline.session_past_events(agent, session_id) -%}
      {% if event.type_ == "session_act" -%}
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
           model: gpt-3.5-turbo
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
           model: gpt-3.5-turbo
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

The `prepare` section of the scene is used to defined the preparation steps before the scene starts. You can do some initialization work here.

1. `preface` type

   You can make the character say something before the scene starts.

   ```yaml
   scenes:
     talking:
       prepare:
         - type: preface
           character_name: ai assistant
           content: |-
             Hello, I am John, your AI assistant. How can I help you today?
   ```

2. `function` type

   The `function` type will call the custom function before the scene starts.

   ```yaml
   scenes:
     talking:
       prepare:
         - type: function
           function: module_name:function_name
   ```

   The custom function will receive one parameter of type `operagents.timeline.Timeline`.

   ```python
   # module_name.py

   from operagents.timeline import Timeline

   async def function_name(timeline: Timeline) -> None:
       pass
   ```

3. `custom` type

   The `custom` type will call the custom prepare class before the scene starts.

   ```yaml
   scenes:
     talking:
       prepare:
         - type: custom
           path: module_name:CustomPrepare
           custom_config: value
   ```

   ```python
   # module_name.py

   from typing import Self

   from operagents.timeline import Timeline
   from operagents.scene.prepare import ScenePrepare
   from operagents.config import CustomScenePrepareConfig

   class CustomScenePrepare(ScenePrepare):
       @classmethod
       def from_config(cls, config: CustomScenePrepareConfig) -> Self:
           return cls()

       async def prepare(self, timeline: Timeline) -> None:
           pass
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
               exception_template: |-
                 {# some jinja template #}
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

   Note that the function's name and docstring will be used as the prop's name and description. You can also provide the description of the args by pydantic's `Field`. The exception template will be used to render response when the function raises an error.

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

### The Hook config

Hooks enables you to run custom code when specific timeline events occur. The `hooks` section is a list of hooks, where each hook is a dictionary with the hook type and the hook config. By default, operagents enables the `summary` hook unless you change the `hooks` section.

1. `summary` Hook

   The `summary` hook will call the agents to summarize the session when the session ends. You can optionally specify the agent names to summarize.

   ```yaml
   hooks:
     - type: summary
       agent_names:
         - Mike
         - John
   ```

2. `custom` Hook

   The `custom` hook will invoke the custom hook class when specific timeline event encounters.

   ```yaml
   hooks:
     - type: custom
       path: module_name:CustomHook
       custom_config: value
   ```

   ```python
   # module_name.py

   from typing import Self

   from operagents.hook import Hook
   from operagents.timeline import Timeline
   from operagents.config import CustomHookConfig
   from operagents.timeline.event import (
       TimelineEventEnd,
       TimelineEventStart,
       TimelineEventSessionAct,
       TimelineEventSessionEnd,
       TimelineEventSessionStart,
   )

   class CustomHook(Hook):
       @classmethod
       def from_config(cls, config: CustomHookConfig) -> Self:
           return cls()

       async def on_timeline_start(
           self, timeline: Timeline, event: TimelineEventStart
       ):
           """Called when the timeline is started."""
           pass

       async def on_timeline_end(
           self, timeline: Timeline, event: TimelineEventEnd
       ):
           """Called when the timeline is ended."""
           pass

       async def on_timeline_session_start(
           self, timeline: Timeline, event: TimelineEventSessionStart
       ):
           """Called when a session is started."""
           pass

       async def on_timeline_session_end(
           self, timeline: Timeline, event: TimelineEventSessionEnd
       ):
           """Called when a session is ended."""
           pass

       async def on_timeline_session_act(
           self, timeline: Timeline, event: TimelineEventSessionAct
       ):
           """Called when a character acts in a session."""
           pass
   ```

   The hook class may contains methods in the format of `on_timeline_<event_type>`, where `<event_type>` is the type of the timeline event.

### Run the opera

operagents provides a command-line tool to easily run the opera. You can run the opera with the following command:

```bash
operagents run config.yaml
```

If you want to see the debug logs, you can set the `--log-level` option:

```bash
operagents run --log-level DEBUG config.yaml
```

More commands and options can be found by running `operagents --help`.

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
