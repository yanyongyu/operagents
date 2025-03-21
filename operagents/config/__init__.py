from typing import Annotated, Literal, TypeAlias
from typing_extensions import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .const import (
    AGENT_SESSION_SUMMARY_SYSTEM_TEMPLATE,
    AGENT_SESSION_SUMMARY_USER_TEMPLATE,
    FUNCTION_PROP_EXCEPTION_TEMPLATE,
    OPENAI_BACKEND_PROP_VALIDATION_ERROR_TEMPLATE,
)


class CustomTemplateConfig(BaseModel):
    content: str
    custom_functions: dict[str, str] = Field(default_factory=dict)


TemplateConfig: TypeAlias = str | CustomTemplateConfig


class OpenaiBackendAutoToolChoiceConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["auto"] = Field(alias="type")


class OpenaiBackendFunctionToolChoiceConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(alias="type")
    function: str


OpenaiBackendToolChoiceConfig: TypeAlias = Annotated[
    OpenaiBackendAutoToolChoiceConfig | OpenaiBackendFunctionToolChoiceConfig,
    Field(discriminator="type_"),
]


class OpenaiBackendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["openai"] = Field(alias="type")
    model: str
    temperature: float | None = None
    api_key: str | None = None
    base_url: str | None = None
    max_retries: int = 2
    response_format: Literal["text", "json_object"] = "text"
    tool_choice: OpenaiBackendToolChoiceConfig = OpenaiBackendAutoToolChoiceConfig(
        type="auto"
    )
    prop_validation_error_template: TemplateConfig = (
        OPENAI_BACKEND_PROP_VALIDATION_ERROR_TEMPLATE
    )


class UserBackendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["user"] = Field(alias="type")


class CustomBackendConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


BackendConfig: TypeAlias = Annotated[
    OpenaiBackendConfig | UserBackendConfig | CustomBackendConfig,
    Field(discriminator="type_"),
]


class AgentConfig(BaseModel):
    backend: BackendConfig
    system_template: TemplateConfig
    user_template: TemplateConfig
    session_summary_system_template: TemplateConfig = (
        AGENT_SESSION_SUMMARY_SYSTEM_TEMPLATE
    )
    session_summary_user_template: TemplateConfig = AGENT_SESSION_SUMMARY_USER_TEMPLATE


class PrefaceScenePrepareConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["preface"] = Field(alias="type")
    character_name: str
    content: str


class FunctionScenePrepareConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(alias="type")
    function: str


class CustomScenePrepareConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


ScenePrepareConfig = Annotated[
    PrefaceScenePrepareConfig | FunctionScenePrepareConfig | CustomScenePrepareConfig,
    Field(discriminator="type_"),
]


class FunctionPropConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(alias="type")
    function: str
    exception_template: TemplateConfig = FUNCTION_PROP_EXCEPTION_TEMPLATE


class CustomPropConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


PropConfig: TypeAlias = Annotated[
    FunctionPropConfig | CustomPropConfig, Field(discriminator="type_")
]


class CharacterConfig(BaseModel):
    description: str | None = None
    agent_name: str
    props: list[PropConfig] = Field(default_factory=list)


class OrderFlowConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["order"] = Field(alias="type")
    order: list[str] | None = None


class ModelFlowConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["model"] = Field(alias="type")
    backend: BackendConfig
    system_template: TemplateConfig
    user_template: TemplateConfig
    allowed_characters: list[str] | None = None
    begin_character: str | None = None
    fallback_character: str | None = None


class UserFlowConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["user"] = Field(alias="type")


class CustomFlowConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


FlowConfig: TypeAlias = Annotated[
    OrderFlowConfig | ModelFlowConfig | UserFlowConfig | CustomFlowConfig,
    Field(discriminator="type_"),
]


class ModelDirectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["model"] = Field(alias="type")
    backend: BackendConfig
    system_template: TemplateConfig
    user_template: TemplateConfig
    allowed_scenes: list[str] | None = None
    finish_flag: str | None = None


class UserDirectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["user"] = Field(alias="type")


class NeverDirectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["never"] = Field(alias="type")
    max_act_num: int | None = None


class CustomDirectorConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


DirectorConfig: TypeAlias = Annotated[
    ModelDirectorConfig
    | UserDirectorConfig
    | NeverDirectorConfig
    | CustomDirectorConfig,
    Field(discriminator="type_"),
]


class SceneConfig(BaseModel):
    description: str | None = None
    prepare: list[ScenePrepareConfig] = Field(default_factory=list)
    characters: dict[str, CharacterConfig]
    flow: FlowConfig
    director: DirectorConfig

    @model_validator(mode="after")
    def check_preface_prepare(self) -> Self:
        for prepare in self.prepare:
            if isinstance(prepare, PrefaceScenePrepareConfig):
                if prepare.character_name not in self.characters:
                    raise ValueError(
                        f"Preface prepare character {prepare.character_name} "
                        "not found in scene characters"
                    )
        return self

    @model_validator(mode="after")
    def check_order_flow(self) -> Self:
        if isinstance(self.flow, OrderFlowConfig) and self.flow.order is not None:
            if set(self.flow.order) - set(self.characters):
                raise ValueError("Order flow order must be subset of scene characters")
        return self

    @model_validator(mode="after")
    def check_model_flow(self) -> Self:
        if isinstance(self.flow, ModelFlowConfig):
            if self.flow.allowed_characters is not None and (
                set(self.flow.allowed_characters) - set(self.characters)
            ):
                raise ValueError(
                    "Model flow allowed characters must be subset of scene characters"
                )
            if (
                self.flow.begin_character is not None
                and self.flow.begin_character not in self.characters
            ):
                raise ValueError(
                    "Model flow begin character must be in scene characters"
                )
            if (
                self.flow.fallback_character is not None
                and self.flow.fallback_character not in self.characters
            ):
                raise ValueError(
                    "Model flow fallback character must be in scene characters"
                )
        return self


class SummaryHookConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["summary"] = Field(alias="type")
    agent_names: list[str] | None = None


class CustomHookConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


HookConfig: TypeAlias = Annotated[
    SummaryHookConfig | CustomHookConfig, Field(discriminator="type_")
]


class OperagentsConfig(BaseModel):
    agents: dict[str, AgentConfig]
    scenes: dict[str, SceneConfig]
    opening_scene: str
    hooks: list[HookConfig] = Field(
        default_factory=lambda: [SummaryHookConfig(type="summary")]
    )

    @field_validator("agents")
    @classmethod
    def check_agents(cls, agents: dict[str, AgentConfig]):
        if not agents:
            raise ValueError("At least one agent must be defined")
        return agents

    @field_validator("scenes")
    @classmethod
    def check_scenes(cls, scenes: dict[str, AgentConfig]):
        if not scenes:
            raise ValueError("At least one scene must be defined")
        return scenes

    @model_validator(mode="after")
    def check_scene_directors(self) -> Self:
        for scene_name, scene in self.scenes.items():
            if (
                isinstance(scene.director, ModelDirectorConfig)
                and scene.director.allowed_scenes is not None
            ):
                if set(scene.director.allowed_scenes) - set(self.scenes):
                    raise ValueError(
                        f"Scene {scene_name} director allowed scenes "
                        "must be subset of scenes"
                    )
        return self

    @model_validator(mode="after")
    def check_scene_character_agents(self) -> Self:
        for scene_name, scene in self.scenes.items():
            for character_name, character in scene.characters.items():
                if character.agent_name not in self.agents:
                    raise ValueError(
                        f"Scene {scene_name} character {character_name} agent "
                        f"{character.agent_name} not found in agents"
                    )
        return self

    @model_validator(mode="after")
    def check_opening_scene(self) -> Self:
        if self.opening_scene not in self.scenes:
            raise ValueError(f"Opening scene {self.opening_scene} not found in scenes")
        return self

    @model_validator(mode="after")
    def check_hooks(self) -> Self:
        for hook in self.hooks:
            if isinstance(hook, SummaryHookConfig) and hook.agent_names is not None:
                if invalid_agents := set(hook.agent_names) - set(self.agents):
                    raise ValueError(
                        "Summary hook agent names must be subset of agents, "
                        f"invalid agents: {invalid_agents}"
                    )
        return self
