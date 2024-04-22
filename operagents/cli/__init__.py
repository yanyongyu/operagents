import sys
import asyncio
import argparse
from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError

from operagents.opera import Opera
from operagents.version import VERSION
from operagents.utils import save_opera_state
from operagents.config import OperagentsConfig
from operagents.log import logger, setup_logging

parser = argparse.ArgumentParser(prog="operagents", description="OperAgents CLI")
parser.add_argument("--version", "-V", action="version", version=VERSION)

subcommands = parser.add_subparsers(title="Commands")


async def handle_run(
    config: str,
    path: bool = True,
    log_level: Literal["DEBUG", "INFO"] = "INFO",
    export: str | None = None,
):
    setup_logging(log_level)

    if path:
        sys_path = str(Path.cwd().resolve())
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)

    logger.info("Loading opera config...", path=config)
    try:
        opera = Opera.from_config(
            OperagentsConfig.model_validate(
                yaml.safe_load(Path(config).read_text(encoding="utf-8"))
            )
        )
    except Exception:
        logger.exception("Failed to load opera config.", path=config)
        return

    result = await opera.run()

    if export is not None:
        save_opera_state(result, Path(export))


run = subcommands.add_parser(
    "run", help="Run the opera.", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
run.add_argument(
    "--path",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="Add current path to sys.path.",
)
run.add_argument(
    "--log-level", default="INFO", choices=["DEBUG", "INFO"], help="The log level."
)
run.add_argument(
    "--export", default=None, help="Export the opera run result to a JSON file."
)
run.add_argument("config", help="The path to the operagents configuration file.")
run.set_defaults(handler=handle_run)


async def handle_validate(
    config: str, path: bool = True, log_level: Literal["DEBUG", "INFO"] = "INFO"
):
    setup_logging(log_level)

    if path:
        sys_path = str(Path.cwd().resolve())
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)

    try:
        opera_config = OperagentsConfig.model_validate(
            yaml.safe_load(Path(config).read_text(encoding="utf-8"))
        )
    except ValidationError as e:
        logger.error(f"Config file is invalid.\n{e}")
        exit(1)
    except Exception:
        logger.opt(exception=True).error("Config file is invalid.")
        exit(1)

    try:
        Opera.from_config(opera_config)
    except Exception:
        logger.opt(exception=True).exception("Failed to load opera config.")
        exit(1)

    logger.info("Config file is valid.")


validate = subcommands.add_parser(
    "validate",
    help="Validate the operagents config.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
validate.add_argument(
    "--path",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="Add current path to sys.path.",
)
validate.add_argument(
    "--log-level", default="INFO", choices=["DEBUG", "INFO"], help="The log level."
)
validate.add_argument("config", help="The path to the operagents configuration file.")
validate.set_defaults(handler=handle_validate)


def main():
    args = parser.parse_args()
    args = vars(args)
    handler = args.pop("handler")
    asyncio.run(handler(**args))
