import sys
import inspect
import logging
from typing import TYPE_CHECKING

import loguru

if TYPE_CHECKING:
    pass

logger: "loguru.Logger" = loguru.logger

logger.disable("operagents")


class LoguruHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


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


def setup_logging(log_level: str | int = "INFO") -> int:
    """Setup logging for operagents.

    This function should be called only when operagents is used as an application.
    """
    # remove default loguru handler
    logger.remove()
    # add default operagents handler
    logger_id = logger.add(
        sys.stdout,
        level=log_level.upper() if isinstance(log_level, str) else log_level,
        diagnose=False,
        format=default_formatter,
    )
    # redirect standard logging to loguru
    logging.basicConfig(handlers=[LoguruHandler()], level=0)

    # enable operagents logger
    logger.enable("operagents")
    # disable noisy loggers
    logger.disable("httpcore")
    logger.disable("httpx")
    return logger_id
