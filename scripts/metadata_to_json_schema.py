import json
import metadata
import pathlib

if __name__ == "__main__":
    print("Step 2. Generating JSON schemas from the metadata models.")
    for model_name in metadata.DATAPOINTS:
        dp = getattr(metadata, model_name)
        dp: metadata.DatapointBase
        p = (
            pathlib.Path(__file__).parent.parent
            / "staticws"
            / "dashboard"
            / "scripts"
            / "schemas"
            / "metadata"
            / f"{model_name}.json"
        )
        with open(p, "w") as f:
            json.dump(dp.model_json_schema(), f, indent=2)
