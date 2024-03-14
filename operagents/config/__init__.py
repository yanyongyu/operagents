from typing_extensions import Self
from typing import Literal, Annotated, TypeAlias

from pydantic import Field, BaseModel, ConfigDict, field_validator, model_validator


class OpenaiBackendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["openai"] = Field(alias="type")
    model: str
    temperature: float | None = None


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


class CustomTemplateConfig(BaseModel):
    content: str
    custom_functions: dict[str, str] = Field(default_factory=dict)


TemplateConfig: TypeAlias = str | CustomTemplateConfig


class AgentConfig(BaseModel):
    backend: BackendConfig
    system_template: TemplateConfig
    user_template: TemplateConfig
    scene_summary_system_template: TemplateConfig
    scene_summary_user_template: TemplateConfig


class FunctionPropConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(alias="type")
    function: str


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


class CustomFlowConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


FlowConfig: TypeAlias = Annotated[
    OrderFlowConfig | CustomFlowConfig, Field(discriminator="type_")
]


class ModelDirectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["model"] = Field(alias="type")
    backend: BackendConfig
    system_template: TemplateConfig
    user_template: TemplateConfig
    allowed_scenes: list[str] | None = None
    finish_flag: str = "finish"


class UserDirectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["user"] = Field(alias="type")


class CustomDirectorConfig(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type_: Literal["custom"] = Field(alias="type")
    path: str


DirectorConfig: TypeAlias = Annotated[
    ModelDirectorConfig | UserDirectorConfig | CustomDirectorConfig,
    Field(discriminator="type_"),
]


class SceneConfig(BaseModel):
    description: str | None = None
    characters: dict[str, CharacterConfig]
    flow: FlowConfig
    director: DirectorConfig


class OperagentsConfig(BaseModel):
    agents: dict[str, AgentConfig]
    scenes: dict[str, SceneConfig]
    opening_scene: str

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
    def check_opening_scene(self) -> Self:
        if self.opening_scene not in self.scenes:
            raise ValueError(f"Opening scene {self.opening_scene} not found in scenes")
        return self
