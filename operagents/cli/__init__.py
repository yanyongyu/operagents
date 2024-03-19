import sys
import asyncio
import argparse
from pathlib import Path
from typing import Literal

import yaml

from operagents.log import logger
from operagents.opera import Opera
from operagents.config import OperagentsConfig

parser = argparse.ArgumentParser(prog="operagents", description="OperAgents CLI")

subcommands = parser.add_subparsers(title="Commands")


async def handle_run(
    config: str, path: bool = True, log_level: Literal["DEBUG", "INFO"] = "INFO"
):
    if path:
        sys_path = str(Path.cwd().resolve())
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)

    logger.configure(extra={"log_level": log_level})

    logger.info("Loading opera config...", path=config)
    try:
        opera = Opera.from_config(
            OperagentsConfig.model_validate(yaml.safe_load(Path(config).read_text()))
        )
    except Exception:
        logger.exception("Failed to load opera config.", path=config)
        return

    await opera.run()


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
run.add_argument("config", help="The path to the operagents configuration file.")
run.set_defaults(handler=handle_run)


def main():
    args = parser.parse_args()
    args = vars(args)
    handler = args.pop("handler")
    asyncio.run(handler(**args))
