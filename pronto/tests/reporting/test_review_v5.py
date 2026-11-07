"""RNA clinical classifications are versioned and independent of technical QC."""

import json

import pytest

from pronto.tests.reporting.test_html_review_state import draft_review
from pronto.tests.reporting.test_pronto_output_adapter import build_report
from pronto_report.migration import migrate_review_state_to_v3
from pronto_report.serialization import serialize_review_state
from pronto_report.validation import ContractValidationError, validate_review_state


def test_v5_rna_classification_roundtrip_and_v4_contract_stays_unchanged():
    report = build_report()
    document = json.loads(serialize_review_state(migrate_review_state_to_v3(draft_review(report))))
    document.update(schemaVersion="5.0", manualCnvRows=[])
    document["findingReviews"] = [
        {
            "findingId": "rna-synthetic",
            "reportingDecision": "INCLUDE",
            "reportHighlight": False,
            "clinicalClassification": "ONCOGENIC",
        }
    ]
    validated = validate_review_state(document, report=report)
    assert json.loads(serialize_review_state(validated)) == document
    document["schemaVersion"] = "4.0"
    with pytest.raises(ContractValidationError):
        validate_review_state(document, report=report)
