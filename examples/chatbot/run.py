import asyncio
from pathlib import Path

import yaml

from operagents import Opera, OperagentsConfig

config = OperagentsConfig.model_validate(
    yaml.safe_load(Path("config.json").read_text(encoding="utf-8"))
)
opera = Opera.from_config(config)


async def main():
    await opera.run()


if __name__ == "__main__":
    asyncio.run(main())
