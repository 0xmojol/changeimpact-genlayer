import hashlib
import json

import pytest


CASE_ID = "terms-service-v1"
COMMITMENT = "Support requests receive a response within a stated period."
BASELINE_URL = "https://example.org/terms-v1.txt"
BASELINE_TEXT = (
    "Support replies within two business days. Requests must be sent by account holders. "
    "No exceptions apply. This term starts on January 1, 2025. The monthly limit is 10 requests."
)
REVISED_URL = "https://example.org/terms-v2.txt"
REVISED_TEXT = (
    "Support replies within five business days. Requests must be sent by account holders. "
    "No exceptions apply. This term starts on January 1, 2025. The monthly limit is 10 requests."
)
BASELINE_HASH = hashlib.sha256(BASELINE_TEXT.encode("utf-8")).hexdigest()
REVISED_HASH = hashlib.sha256(REVISED_TEXT.encode("utf-8")).hexdigest()


def test_register_and_read_case(direct_deploy):
    contract = direct_deploy("contracts/change_impact.py")

    result = contract.register_case(
        CASE_ID,
        COMMITMENT,
        BASELINE_URL,
        BASELINE_HASH,
    )

    assert result == CASE_ID
    case = json.loads(contract.get_case(CASE_ID))
    assert case["case_id"] == CASE_ID
    assert case["commitment"] == COMMITMENT
    assert case["baseline_url"] == BASELINE_URL
    assert case["baseline_sha256"] == BASELINE_HASH
    assert case["status"] == "OPEN"
    assert case["result"] == ""


def test_duplicate_case_id_is_rejected(direct_deploy):
    contract = direct_deploy("contracts/change_impact.py")
    contract.register_case(CASE_ID, COMMITMENT, BASELINE_URL, BASELINE_HASH)

    with pytest.raises(Exception, match="case_id already exists"):
        contract.register_case(CASE_ID, COMMITMENT, BASELINE_URL, BASELINE_HASH)


def test_invalid_digest_is_rejected_without_registration(direct_deploy):
    contract = direct_deploy("contracts/change_impact.py")

    with pytest.raises(Exception, match="64 hexadecimal"):
        contract.register_case(CASE_ID, COMMITMENT, BASELINE_URL, "not-a-digest")

    with pytest.raises(Exception, match="case_id not found"):
        contract.get_case(CASE_ID)


def test_review_requires_existing_case_and_valid_digest(direct_deploy):
    contract = direct_deploy("contracts/change_impact.py")

    with pytest.raises(Exception, match="case_id not found"):
        contract.review_change(CASE_ID, REVISED_URL, REVISED_HASH)

    contract.register_case(CASE_ID, COMMITMENT, BASELINE_URL, BASELINE_HASH)
    with pytest.raises(Exception, match="64 hexadecimal"):
        contract.review_change(CASE_ID, REVISED_URL, "invalid")

    case = json.loads(contract.get_case(CASE_ID))
    assert case["status"] == "OPEN"
    assert case["result"] == ""


def test_review_compares_snapshots_and_stores_consensus_result(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/change_impact.py")
    contract.register_case(CASE_ID, COMMITMENT, BASELINE_URL, BASELINE_HASH)

    direct_vm.mock_web(
        r"https://example\.org/terms-v1\.txt",
        {"status": 200, "body": BASELINE_TEXT},
    )
    direct_vm.mock_web(
        r"https://example\.org/terms-v2\.txt",
        {"status": 200, "body": REVISED_TEXT},
    )
    findings = {
        "scope": {
            "status": "MATCH",
            "baseline_quote": "Requests must be sent by account holders.",
            "revised_quote": "Requests must be sent by account holders.",
        },
        "action": {
            "status": "MATCH",
            "baseline_quote": "Support replies",
            "revised_quote": "Support replies",
        },
        "conditions": {
            "status": "MATCH",
            "baseline_quote": "No exceptions apply.",
            "revised_quote": "No exceptions apply.",
        },
        "time": {
            "status": "CHANGED",
            "baseline_quote": "Support replies within two business days.",
            "revised_quote": "Support replies within five business days.",
        },
        "threshold": {
            "status": "MATCH",
            "baseline_quote": "The monthly limit is 10 requests.",
            "revised_quote": "The monthly limit is 10 requests.",
        },
    }
    direct_vm.mock_llm(r".*", json.dumps({"findings": findings}))

    result = json.loads(contract.review_change(CASE_ID, REVISED_URL, REVISED_HASH))

    assert result["outcome"] == "MATERIAL_CHANGE"
    assert result["findings"]["time"]["status"] == "CHANGED"
    case = json.loads(contract.get_case(CASE_ID))
    assert case["status"] == "REVIEWED"
    assert case["revised_sha256"] == REVISED_HASH
    assert json.loads(case["result"])["outcome"] == "MATERIAL_CHANGE"

    with pytest.raises(Exception, match="already been reviewed"):
        contract.review_change(CASE_ID, REVISED_URL, REVISED_HASH)
