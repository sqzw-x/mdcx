import json
from dataclasses import asdict

from mdcx.config.manager import ConfigSchema
from mdcx.config.models import Config

# with open("config_schema.json", "w") as f:
#     json.dump(TypeAdapter(ConfigSchema).json_schema(), f)

with open("../mdcx-webui/src/lib/json-schema/schema.json", "w") as f:
    json.dump(Config.model_json_schema(), f)

with open("../mdcx-webui/src/lib/json-schema/config_default_pydantic.json", "w", encoding="utf-8") as f:
    f.write(Config.from_schema_dict(asdict(ConfigSchema())).model_dump_json())
