import argparse
import json
import re
from pathlib import Path


def extract_json_text(text):
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in raw LLM output")
    return text[start : end + 1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_output", help="Raw LLM output text file")
    parser.add_argument("--out", required=True, help="Output JSON file")
    args = parser.parse_args()

    raw_path = Path(args.raw_output)
    out_path = Path(args.out)
    text = raw_path.read_text(encoding="utf-8-sig")
    json_text = extract_json_text(text)
    data = json.loads(json_text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
