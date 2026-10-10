import json
from pathlib import Path

import yaml

from store_review.benchmark import run_benchmark
from store_review.cli import main
from store_review.rules import all_rule_ids

CORPUS = Path(__file__).parent.parent / "corpus"


def cases():
    return [yaml.safe_load((d / "case.yaml").read_text()) for d in sorted(CORPUS.iterdir()) if (d / "case.yaml").is_file()]


def test_corpus_shape_meets_spec():
    all_cases = cases()
    positives = [c for c in all_cases if c["expected"]]
    assert len(all_cases) >= 36 and len(positives) >= 24
    assert len([c for c in all_cases if not c["expected"]]) >= 8
    covered = {rid for c in positives for rid in c["expected"]}
    assert covered == set(all_rule_ids()), f"rules without a positive case: {set(all_rule_ids()) - covered}"


def test_benchmark_numbers_and_known_gaps():
    result = run_benchmark(CORPUS)
    assert result["cases"] == len(cases())
    assert result["precision"] >= 0.90 and result["recall"] >= 0.85
    assert {m["case"] for m in result["misses"]} == {"gap-permission-handler-camera", "gap-custom-delete-method"}


def test_counts_are_exact_on_a_tiny_corpus(tmp_path):
    for name, expected, plist in (("hit", ["IOS-ENCRYPTION-FLAG"], ""), ("fp", [], "")):
        d = tmp_path / name / "app"
        (d / "ios/Runner").mkdir(parents=True)
        (d / "pubspec.yaml").write_text("name: x\n")
        (d / "store").mkdir()
        (d / "store/listing.yaml").write_text("privacy_policy_url: https://e.com/p\n")
        (d / "ios/Runner/Info.plist").write_text('<?xml version="1.0"?><plist version="1.0"><dict></dict></plist>')
        (tmp_path / name / "case.yaml").write_text(yaml.safe_dump({"rejection": "r", "expected": expected, "env": {}}))
    r = run_benchmark(tmp_path)
    assert (r["tp"], r["fp"], r["fn"]) == (1, 1, 0)
    assert r["precision"] == 0.5 and r["recall"] == 1.0


def test_cli_thresholds(tmp_path, capsys):
    out = tmp_path / "bench.json"
    assert main(["benchmark", "--corpus", str(CORPUS), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["cases"] >= 36
    assert main(["benchmark", "--corpus", str(CORPUS), "--min-recall", "1.0"]) == 5
    assert "below" in capsys.readouterr().err


def test_scan_embeds_benchmark(make_app, tmp_path):
    bench = tmp_path / "bench.json"
    bench.write_text(json.dumps({"cases": 40, "precision": 0.97, "recall": 0.97, "tp": 33, "fp": 1, "fn": 1, "misses": []}))
    out = tmp_path / "f.json"
    assert main(["scan", "--app", str(make_app({})), "--out", str(out), "--benchmark", str(bench)]) == 0
    assert json.loads(out.read_text())["benchmark"]["recall"] == 0.97
