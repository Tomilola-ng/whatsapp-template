"""Helpers for safely validating ORM objects into Pydantic schemas."""

from typing import Any, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def model_validate_orm(model: Any, schema: type[SchemaT]) -> SchemaT:
    """Validate a Tortoise model while ignoring unloaded relation attributes."""
    data = {}
    fields = getattr(schema, "model_fields", {})
    for name in fields:
        try:
            value = getattr(model, name)
        except Exception:
            continue
        data[name] = value
    return schema.model_validate(data)
