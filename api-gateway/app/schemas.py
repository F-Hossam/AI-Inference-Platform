from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, JsonValue, field_validator

PositiveId = Annotated[int, Field(gt=0)]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class SignupRequest(ApiModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name cannot be blank")
        return stripped


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(ApiModel):
    id: int
    email: EmailStr
    name: str
    role: str


class UseCaseResponse(ApiModel):
    id: int
    name: str
    description: str | None
    is_ready: bool


class ModelResponse(ApiModel):
    id: int
    use_case_id: int
    name: str
    version: str
    is_active: bool


class InferenceRequest(ApiModel):
    input: dict[str, JsonValue] = Field(min_length=1)
