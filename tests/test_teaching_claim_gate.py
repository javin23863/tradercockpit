import copy
import hashlib
import json

import pytest

from tools.teaching_claim_gate import validate


SCRIPT = (
    "=== SLOT scene-a -> a.wav ===\n\n"
    "# receipt: C1\nThe run kept 12 of 20 strategies.\n\n"
    "# receipt: C2\nNow let me show you why.\n"
)


def _write(tmp_path, script=SCRIPT):
    tmp_path.mkdir(parents=True, exist_ok=True)
    script_path = tmp_path / "vo.txt"
    script_path.write_text(script, encoding="utf-8")
    evidence_path = tmp_path / "evidence" / "run.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text('{"survivors": 12, "tested": 20}', encoding="utf-8")
    ontology = {
        "schema": "teaching-claims/v1",
        "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
        "sources": {
            "RUN1": {
                "citation": "runtime/validation/run.json",
                "locator": "$.summary",
                "supports": "12 of 20 strategies survived.",
                "limitations": "One asset class and one run.",
                "path": "evidence/run.json",
                "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            }
        },
        "claims": {
            "C1": {"kind": "run_receipt", "source_ids": ["RUN1"]},
            "C2": {
                "kind": "delivery",
                "source_ids": [],
                "why_non_claim": "Transition only.",
            },
        },
    }
    ontology_path = tmp_path / "claims.json"
    ontology_path.write_text(json.dumps(ontology), encoding="utf-8")
    return script_path, ontology_path, ontology


def test_valid_receipts_pass_and_adversarial_bypasses_block(tmp_path):
    script, ontology_path, ontology = _write(tmp_path)
    assert validate(script, ontology_path) == (2, 1)

    attacks = []

    changed = tmp_path / "changed.txt"
    changed.write_text(SCRIPT.replace("12", "13"), encoding="utf-8")
    attacks.append((changed, ontology_path, "script_sha256 does not match"))

    unbound, unbound_ontology, _ = _write(
        tmp_path / "unbound",
        SCRIPT.replace("# receipt: C2\n", ""),
    )
    attacks.append((unbound, unbound_ontology, "no '# receipt:' marker"))

    duplicate, duplicate_ontology, _ = _write(
        tmp_path / "duplicate",
        SCRIPT.replace("# receipt: C2", "# receipt: C1"),
    )
    attacks.append((duplicate, duplicate_ontology, "exactly one spoken paragraph"))

    no_limit = copy.deepcopy(ontology)
    no_limit["sources"]["RUN1"]["limitations"] = ""
    no_limit_path = tmp_path / "no-limit.json"
    no_limit_path.write_text(json.dumps(no_limit), encoding="utf-8")
    attacks.append((script, no_limit_path, "limitations"))

    string_ids = copy.deepcopy(ontology)
    string_ids["claims"]["C1"]["source_ids"] = "RUN1"
    string_ids_path = tmp_path / "string-ids.json"
    string_ids_path.write_text(json.dumps(string_ids), encoding="utf-8")
    attacks.append((script, string_ids_path, "source_ids must be a list"))

    factual_delivery = copy.deepcopy(ontology)
    factual_delivery["claims"]["C1"] = {
        "kind": "delivery",
        "source_ids": [],
        "why_non_claim": "Pretend this is only a transition.",
    }
    factual_delivery_path = tmp_path / "factual-delivery.json"
    factual_delivery_path.write_text(json.dumps(factual_delivery), encoding="utf-8")
    attacks.append((script, factual_delivery_path, "not an allowed delivery-only line"))

    for attacked_script, attacked_ontology, expected in attacks:
        with pytest.raises(ValueError, match=expected):
            validate(attacked_script, attacked_ontology)
