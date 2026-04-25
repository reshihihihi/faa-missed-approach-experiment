import argparse
import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.getenv("FAA_B1_B3_ROOT", REPO_ROOT)).expanduser().resolve()
DEFAULT_SCHEMA = ROOT / "schemas/missed_approach_leg.schema.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def iter_json_files(paths):
    files = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate method outputs with the PR #28 JSON schema file."
    )
    parser.add_argument("paths", nargs="+", help="JSON files or directories to validate")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    args = parser.parse_args()

    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency 'jsonschema'. Install it with: python -m pip install jsonschema"
        ) from exc

    schema_path = Path(args.schema)
    schema = read_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)

    failed = False
    for path in iter_json_files(args.paths):
        data = read_json(path)
        errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                json_path = ".".join(str(part) for part in error.path) or "<root>"
                print(f"  - {json_path}: {error.message}")
        else:
            print(f"PASS {path}")

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
