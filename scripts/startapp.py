#!/usr/bin/env python3
"""
Django-style app generator for FastAPI projects.
Usage: python startapp.py <app_name> [--extended]
"""

import argparse
from pathlib import Path


SERVICE_INIT_TEMPLATE = '''"""Public {module_name} service API."""

from app.{app_name}.services.core import example_service_function

__all__ = ["example_service_function"]
'''

SERVICE_CORE_TEMPLATE = '''"""{} service orchestration."""

from fastapi import HTTPException, status


async def example_service_function(resource_id: str) -> dict:
    """Example service function."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Service not implemented.",
    )
'''

MODELS_TEMPLATE = '''"""{} models"""

from tortoise import fields, models

from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default


class ExampleModel(models.Model):
    """Table: {table_name}"""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCOUNT),
    )
    name = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "{table_name}"
        indexes = [("name",)]

    def __str__(self):
        return self.name
'''

SCHEMAS_TEMPLATE = '''"""{} schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from tortoise.contrib.pydantic import pydantic_model_creator

from app.{}.models import ExampleModel


ExampleModelFullPydantic = pydantic_model_creator(
    ExampleModel, name="ExampleModelFull"
)
ExampleModelCreatePydantic = pydantic_model_creator(
    ExampleModel,
    name="ExampleModelCreate",
    exclude_readonly=True,
)


class ExampleModelRead(BaseModel):
    """Example model read schema."""

    id: str
    name: str
    updated_at: datetime

    class Config:
        from_attributes = True


class ExampleModelUpdate(BaseModel):
    """Schema for updating example model."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
'''

VIEWS_TEMPLATE = '''"""{} class-based views.

Plain CRUD lives here; anything complex belongs in ``services/`` and is called
from a hook (``validate``, ``perform_create``, ...) or an ``@action`` method.
Schemas are generated from the model until you declare ``create_schema`` /
``update_schema`` / ``out_schema``. See docs/CBV_GUIDE.md.
"""

from app.{app_name}.models import ExampleModel
from app.base.views import ModelView


class ExampleModelView(ModelView):
    model = ExampleModel
    prefix = "/{routes_prefix}"
    tags = ["{module_name}"]
    permission_module = "{app_name}"  # register actions in permissions.py
    search_fields = ("name",)
    ordering_fields = ("name", "created_at")
'''

ROUTES_TEMPLATE = '''"""{} routes (mount this router in app/config/routes.py)."""

from app.{}.views import ExampleModelView

router = ExampleModelView.as_router()
'''

EMAILS_TEMPLATE = '''"""{} email templates."""

import html
from typing import Dict

from app.base.email_template import base_email_template


def example_email(context: Dict) -> str:
    """Build an example transactional email."""
    name = html.escape(str(context.get("name", "User")))
    content = f"""
        <h1>Example Email</h1>
        <p>Hello {{name}},</p>
        <p>This is an example email template.</p>
        """
    return base_email_template("Example Email", content)
'''

UTILS_TEMPLATE = '''"""{} pure helpers."""


def normalize_example_name(value: str) -> str:
    """Normalize a user-provided example name."""
    return value.strip()
'''

ENUMS_TEMPLATE = '''"""{} enums"""

from enum import Enum


class ExampleEnum(str, Enum):
    """Example enum."""

    OPTION_ONE = "option_one"
    OPTION_TWO = "option_two"
'''

PERMISSIONS_TEMPLATE = '''"""{} permission registrations."""

from app.access.permission_registry import register_module

register_module(
    "{app_name}",
    actions=["create", "read", "update", "delete"],
)
'''

HANDOFF_TEMPLATE = """# {module_name} Client Handoff

Document client-facing HTTP contracts here after routes are implemented.

Include method, path, auth requirements, request fields, response fields, status codes, and error shapes. Do not include migrations, SQL, or internal filesystem paths.
"""

TEST_RUN_TEMPLATE = '''#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
ENV_FILE="${{1:-.env.e2e}}"
source app/base/tests/lib/bootstrap.sh
api_bootstrap_load_env "${{ENV_FILE}}"
trap api_bootstrap_stop_server EXIT
api_bootstrap_ensure_server "${{ENV_FILE}}"
source app/base/tests/lib/common.sh
api_test_init_logging
bash "${{SCRIPT_DIR}}/{app_name}.sh"
api_print_summary
'''

TEST_MODULE_TEMPLATE = '''#!/usr/bin/env bash
set -euo pipefail

api_record_pass "{app_name} has no E2E checks yet"
'''

INIT_TEMPLATE = '''"""{} module."""
'''


def generate_app(app_name: str, extended: bool = False):
    """Generate a new FastAPI app with boilerplate files."""
    if not app_name.islower() or not app_name.replace("_", "").isalnum():
        print(
            f"Error: App name '{app_name}' must be lowercase and contain only letters, numbers, and underscores."
        )
        return

    base_dir = Path(__file__).resolve().parent.parent
    app_dir = base_dir / "app" / app_name
    if app_dir.exists():
        print(f"Error: App '{app_name}' already exists at {app_dir}")
        return

    module_name = " ".join(word.capitalize() for word in app_name.split("_"))
    table_name = app_name
    files_to_create = [
        ("__init__.py", INIT_TEMPLATE.format(module_name)),
        ("services/__init__.py", SERVICE_INIT_TEMPLATE.format(module_name=module_name, app_name=app_name)),
        ("services/core.py", SERVICE_CORE_TEMPLATE.format(module_name)),
        ("models.py", MODELS_TEMPLATE.format(module_name, table_name=table_name)),
        ("schemas.py", SCHEMAS_TEMPLATE.format(module_name, app_name)),
        (
            "views.py",
            VIEWS_TEMPLATE.format(
                module_name,
                app_name=app_name,
                module_name=module_name,
                routes_prefix=app_name.replace("_", "-"),
            ),
        ),
        ("handoff/CLIENT_HANDOFF.md", HANDOFF_TEMPLATE.format(module_name=module_name)),
        ("tests/run.sh", TEST_RUN_TEMPLATE.format(app_name=app_name)),
        ("tests/{}.sh".format(app_name), TEST_MODULE_TEMPLATE.format(app_name=app_name)),
    ]

    if extended:
        files_to_create.extend(
            [
                ("routes.py", ROUTES_TEMPLATE.format(module_name, app_name)),
                ("emails.py", EMAILS_TEMPLATE.format(module_name)),
                ("utils.py", UTILS_TEMPLATE.format(module_name)),
                ("enums.py", ENUMS_TEMPLATE.format(module_name)),
                ("permissions.py", PERMISSIONS_TEMPLATE.format(module_name, app_name=app_name)),
            ]
        )

    app_dir.mkdir(parents=True, exist_ok=False)
    print(f"Created directory: {app_dir}")
    for filename, content in files_to_create:
        file_path = app_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        if filename.startswith("tests/") and filename.endswith(".sh"):
            file_path.chmod(0o755)
        print(f"Created file: {file_path}")

    print(f"\nSuccessfully created app '{app_name}'")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate a new FastAPI app with boilerplate files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("app_name")
    parser.add_argument("-e", "--extended", action="store_true")
    args = parser.parse_args()
    generate_app(args.app_name, args.extended)


if __name__ == "__main__":
    main()
