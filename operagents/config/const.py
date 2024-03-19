# ruff: noqa: E501

AGENT_SCENE_SUMMARY_SYSTEM_TEMPLATE = """
Your name is {{ agent.name }}.
Your task is to summarize the historical dialogue records according to the current scene, and summarize the most important information.
""".strip()
AGENT_SCENE_SUMMARY_USER_TEMPLATE = """
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
""".strip()
