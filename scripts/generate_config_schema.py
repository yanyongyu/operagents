import sys
import json
from pathlib import Path

from operagents import OperagentsConfig

schema = OperagentsConfig.model_json_schema(by_alias=True)

if __name__ == "__main__":
    Path(sys.argv[1]).write_text(
        json.dumps(schema, ensure_ascii=False), encoding="utf-8"
    )
