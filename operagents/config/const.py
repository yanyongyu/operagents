# ruff: noqa: E501

# backend config

OPENAI_BACKEND_PROP_VALIDATION_ERROR_TEMPLATE = """
Function parameters validation failed:
{% for err in exc.errors() -%}
Field name: {{ err["loc"] | join(".") }}
Error message: {{ err["msg"] }}
{%- endfor %}
""".strip()

# agent config

AGENT_SESSION_SUMMARY_SYSTEM_TEMPLATE = """
Your name is {{ agent.name }}.
Your task is to summarize the historical dialogue records according to the current scene, and summarize the most important information.
""".strip()
AGENT_SESSION_SUMMARY_USER_TEMPLATE = """
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
""".strip()

# prop config

FUNCTION_PROP_EXCEPTION_TEMPLATE = """
Function returned an error:
{{ exc.__class__.__name__ }}: {{ exc }}
""".strip()
