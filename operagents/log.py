import sys
from typing import TYPE_CHECKING

import loguru

if TYPE_CHECKING:
    pass

logger: "loguru.Logger" = loguru.logger


def default_filter(record: "loguru.Record") -> bool:
    """默认的日志过滤器，根据 `config.log_level` 配置改变日志等级。"""
    log_level = record["extra"].get("log_level", "INFO")
    levelno = logger.level(log_level).no if isinstance(log_level, str) else log_level
    return record["level"].no >= levelno


def default_formatter(record: "loguru.Record") -> str:
    prefix = (
        "<g>{time:MM-DD HH:mm:ss}</g> "
        "[<lvl>{level}</lvl>] "
        "<c><u>{name}</u></c> |"
        # "<c>{function}:{line}</c>|"
    )

    info = []
    if record["extra"].get("scene", None):
        info.append("[Scene {extra[scene].name}] ")
    if record["extra"].get("agent", None):
        info.append("{extra[agent].name}")
    if record["extra"].get("character", None):
        info.append("({extra[character].name})")

    if not info:
        return prefix + " {message}\n{exception}"

    return f"{prefix} <m>" + "".join(info).strip() + "</m> | {message}\n{exception}"


logger.remove()
logger_id = logger.add(
    sys.stdout,
    level=0,
    diagnose=False,
    filter=default_filter,
    format=default_formatter,
)
