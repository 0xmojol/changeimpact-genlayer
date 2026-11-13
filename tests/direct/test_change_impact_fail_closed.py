import hashlib
import json

import pytest


CASE_ID = "digest-mismatch-case"
COMMITMENT = "Support requests receive a reply within two business days."
BASELINE_URL = "https://example.org/baseline.txt"
REVISED_URL = "https://example.org/revised.txt"
BASELINE_TEXT = "Support requests receive a reply within two business days."
TAMPERED_BASELINE_TEXT = "Support requests receive a reply within ten business days."
REVISED_TEXT = "Support requests receive a reply within five business days."
BASELINE_HASH = hashlib.sha256(BASELINE_TEXT.encode("utf-8")).hexdigest()
REVISED_HASH = hashlib.sha256(REVISED_TEXT.encode("utf-8")).hexdigest()


def test_digest_mismatch_does_not_write_review_state(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/change_impact.py")
    contract.register_case(CASE_ID, COMMITMENT, BASELINE_URL, BASELINE_HASH)

    direct_vm.mock_web(
        r"https://example\.org/baseline\.txt",
        {"status": 200, "body": TAMPERED_BASELINE_TEXT},
    )
    direct_vm.mock_web(
        r"https://example\.org/revised\.txt",
        {"status": 200, "body": REVISED_TEXT},
    )

    with pytest.raises(Exception, match="baseline digest mismatch"):
        contract.review_change(CASE_ID, REVISED_URL, REVISED_HASH)

    case = json.loads(contract.get_case(CASE_ID))
    assert case["status"] == "OPEN"
    assert case["revised_url"] == ""
    assert case["result"] == ""
