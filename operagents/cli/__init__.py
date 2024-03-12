import asyncio
import argparse
from pathlib import Path

import yaml

from operagents.log import logger
from operagents.opera import Opera
from operagents.config import OperagentsConfig

parser = argparse.ArgumentParser(prog="operagents", description="OperAgents CLI")

subcommands = parser.add_subparsers()


async def handle_run(config: str):
    await logger.ainfo("Loading opera config...", path=config)
    try:
        opera = Opera.from_config(
            OperagentsConfig.model_validate(yaml.safe_load(Path(config).read_text()))
        )
    except Exception:
        await logger.aexception("Failed to load opera config.", path=config)
        return

    await opera.run()


run = subcommands.add_parser("run", help="Run the opera.")
run.add_argument("config", help="The path to the opera configuration file.")
run.set_defaults(handler=handle_run)


def main():
    args = parser.parse_args()
    args = vars(args)
    handler = args.pop("handler")
    asyncio.run(handler(**args))
