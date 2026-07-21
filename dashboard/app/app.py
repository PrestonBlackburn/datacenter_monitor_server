from __future__ import annotations

from asyncio import sleep
from typing import Any, Dict
from pathlib import Path
from litestar import Litestar, get, Router
from litestar.response import Template
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.static_files import StaticFilesConfig

@get("/health")
async def health_check() -> dict[str,str]:
    return {"status": "ok"}

@get("/")
async def dashboard() -> Template:  # noqa: UP006
    context = {}
    return Template(template_name="pages/dashboard.html", context = context)

app = Litestar(
    route_handlers=[health_check, dashboard],
    template_config=TemplateConfig(
        directory=Path("app/templates"),
        engine=JinjaTemplateEngine,
    ),
    static_files_config=[
        StaticFilesConfig(
            directories=["app/static"],
            path="/static",
        )
    ],
)