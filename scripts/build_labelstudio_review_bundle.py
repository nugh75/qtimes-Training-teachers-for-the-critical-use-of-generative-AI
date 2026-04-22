#!/usr/bin/env python3
"""Build a Label Studio review bundle from double-coding item agreement CSV.

Output bundle includes:
- tasks.json: one task per item
- label_config.xml: project interface
- create_project_payload.json: API payload for project creation
- import_tasks_payload.json: API payload for task import

Optionally, if --api-url and --api-token are provided, it can:
- create the project via API
- import tasks into that project
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[1] / "Praxis-ql"
DEFAULT_CSV = ROOT_DIR / "04-label" / "labels" / "double-coding-item-agreement.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Item agreement CSV path")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT_DIR / "04-label" / "labelstudio" / f"review-bundle-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        help="Output bundle directory",
    )
    parser.add_argument(
        "--title",
        default=f"PRAXIS Human Review {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        help="Label Studio project title",
    )
    parser.add_argument("--api-url", help="Label Studio URL, example: http://localhost:8082")
    parser.add_argument("--api-token", help="Label Studio personal access token")
    return parser.parse_args()


def split_codes(raw: str) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split("|") if item.strip()]


def build_label_config(codes: list[str], model_names: list[str]) -> str:
    model_a = model_names[0] if len(model_names) > 0 else "model_a"
    model_b = model_names[1] if len(model_names) > 1 else "model_b"

    choices_xml = "\n".join([f'      <Choice value="{code}" />' for code in codes])

    return f"""<View>
  <Header value="PRAXIS double-coding human review" />
  <Text name="context" value="$context" />

  <Header value="Model outputs" />
  <Text name="m1" value="{model_a}: $model_a_codes" />
  <Text name="m2" value="{model_b}: $model_b_codes" />
  <Text name="metrics" value="Exact match: $exact_match | Jaccard: $jaccard" />

  <Header value="Human final coding" />
  <Choices name="human_codes" toName="context" choice="multiple" showInLine="true">
{choices_xml}
  </Choices>
</View>
"""


def api_request(base_url: str, token: str, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url.rstrip('/')}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    if not args.csv.exists():
        raise FileNotFoundError(f"CSV non trovato: {args.csv}")

    with args.csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        code_fields = [name for name in fields if name.startswith("codes_")]
        if len(code_fields) < 2:
            raise RuntimeError("CSV non valido: servono almeno due colonne codes_<model>")

        model_names = [name.replace("codes_", "", 1) for name in code_fields[:2]]

        tasks: list[dict[str, Any]] = []
        code_set: set[str] = set()

        for row in reader:
            stem = (row.get("raw_stem") or "").strip()
            item_index = (row.get("item_index") or "").strip()
            question = (row.get("question") or "").strip()
            answer = (row.get("answer") or "").strip()

            model_a_codes_list = split_codes(row.get(code_fields[0], ""))
            model_b_codes_list = split_codes(row.get(code_fields[1], ""))

            for c in model_a_codes_list + model_b_codes_list:
                code_set.add(c)

            context = (
                f"Raw stem: {stem}\n"
                f"Item index: {item_index}\n\n"
                f"Question:\n{question}\n\n"
                f"Answer:\n{answer}"
            )

            tasks.append(
                {
                    "data": {
                        "raw_stem": stem,
                        "item_index": item_index,
                        "question": question,
                        "answer": answer,
                        "context": context,
                        "model_a_codes": " | ".join(model_a_codes_list),
                        "model_b_codes": " | ".join(model_b_codes_list),
                        "exact_match": str(row.get("exact_match", "")),
                        "jaccard": str(row.get("jaccard", "")),
                    }
                }
            )

    sorted_codes = sorted(code_set)
    label_config = build_label_config(sorted_codes, model_names)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks_path = out_dir / "tasks.json"
    config_path = out_dir / "label_config.xml"
    create_payload_path = out_dir / "create_project_payload.json"
    import_payload_path = out_dir / "import_tasks_payload.json"

    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    config_path.write_text(label_config, encoding="utf-8")

    create_payload = {
        "title": args.title,
        "label_config": label_config,
        "description": "Human review of PRAXIS item-level double coding",
    }
    create_payload_path.write_text(
        json.dumps(create_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    import_payload = {"tasks": tasks}
    import_payload_path.write_text(
        json.dumps(import_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"tasks={len(tasks)}")
    print(f"codes={len(sorted_codes)}")
    print(f"models={model_names[0]} vs {model_names[1]}")
    print(f"bundle_dir={out_dir}")
    print(f"tasks_json={tasks_path}")
    print(f"label_config={config_path}")

    if args.api_url and args.api_token:
        try:
            project = api_request(args.api_url, args.api_token, "POST", "/api/projects", create_payload)
            project_id = project.get("id")
            if not project_id:
                raise RuntimeError("Project creato senza id")

            imported = api_request(
                args.api_url,
                args.api_token,
                "POST",
                f"/api/projects/{project_id}/import",
                {"tasks": tasks},
            )
            print(f"project_id={project_id}")
            print(f"import_result={json.dumps(imported, ensure_ascii=False)}")
        except error.HTTPError as http_err:
            body = http_err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Errore API {http_err.code}: {body}") from http_err

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
