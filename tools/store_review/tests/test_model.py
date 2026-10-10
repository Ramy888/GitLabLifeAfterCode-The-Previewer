import pytest

from store_review.model import Evidence, Finding, Fix, SchemaError, finding_from_dict, finding_to_dict


def valid_dict(**overrides):
    d = {
        "id": "AND-TARGETSDK",
        "store": "android",
        "layer": "automated",
        "guideline": "Play: Target API level requirement",
        "title": "targetSdk 34 is below the required 36",
        "severity": "blocker",
        "weight": 0,
        "source": "deterministic",
        "confidence": 1.0,
        "evidence": [{"path": "android/app/build.gradle", "line": 31, "detail": "targetSdk = 34"}],
        "fix": {"kind": "auto", "recipe": "set targetSdk = 36"},
    }
    d.update(overrides)
    return d


def test_round_trip():
    f = finding_from_dict(valid_dict())
    assert f.evidence == (Evidence("android/app/build.gradle", 31, "targetSdk = 34"),)
    assert f.fix == Fix("auto", "set targetSdk = 36")
    assert finding_to_dict(f) == valid_dict()


def test_missing_evidence_rejected():
    with pytest.raises(SchemaError, match="evidence"):
        finding_from_dict(valid_dict(evidence=[]))


@pytest.mark.parametrize(
    "field,value",
    [("store", "huawei"), ("severity", "fatal"), ("layer", "x"), ("source", "guess"), ("confidence", 1.5), ("weight", -1)],
)
def test_invalid_enum_or_range_rejected(field, value):
    with pytest.raises(SchemaError, match=field):
        finding_from_dict(valid_dict(**{field: value}))


def test_shared_store_allowed():
    assert finding_from_dict(valid_dict(store="shared")).store == "shared"


def test_missing_required_key_rejected():
    d = valid_dict()
    del d["guideline"]
    with pytest.raises(SchemaError, match="guideline"):
        finding_from_dict(d)
