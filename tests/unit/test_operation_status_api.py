from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.analysis.contracts import AnalysisResult, AnalysisStatus, Explanation, ExplanationStyle
from app.operations.infrastructure.operation_record import OperationRecord
from app.operations.infrastructure.operation_result_record import OperationResultRecord


def _operation(session, status="accepted", failure_code=None):
    operation_id = str(uuid4())
    session.add(
        OperationRecord(
            operation_id=operation_id,
            request_id=str(uuid4()),
            client_document_id="doc-1",
            operation_type="document_analysis",
            status=status,
            created_at=datetime.now(UTC),
            failure_code=failure_code,
        )
    )
    session.commit()
    return operation_id


def _payload():
    return AnalysisResult(
        analysis_status=AnalysisStatus.COMPLETE,
        client_document_id="doc-1",
        explanation=Explanation(
            language="de", style=ExplanationStyle.STANDARD, summary="Kurz", body="Erklärung"
        ),
    ).model_dump(mode="json")


def test_pending_and_failed_status_are_safe(client, app):
    session = app.extensions["doxary_container"].session_factory()
    accepted = _operation(session)
    failed = _operation(session, "failed", "provider_failure")
    session.close()

    assert client.get(f"/api/v1/operations/{accepted}").json == {
        "operation_id": accepted,
        "status": "accepted",
        "result": None,
        "failure": None,
    }
    failed_response = client.get(f"/api/v1/operations/{failed}")
    assert failed_response.status_code == 200
    assert failed_response.json["status"] == "failed"
    assert failed_response.json["failure"] == {"code": "analysis_unavailable"}
    assert "provider" not in str(failed_response.json)


def test_success_is_revalidated_and_repeatable_with_private_no_store(client, app):
    session = app.extensions["doxary_container"].session_factory()
    operation_id = _operation(session, "succeeded")
    session.add(
        OperationResultRecord(
            operation_result_id=str(uuid4()),
            operation_id=operation_id,
            schema_version="analysis_result.v1",
            result_payload=_payload(),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    session.commit()
    session.close()
    first = client.get(f"/api/v1/operations/{operation_id}")
    second = client.get(f"/api/v1/operations/{operation_id}")
    assert first.status_code == second.status_code == 200
    assert first.json == second.json
    assert first.json["result"]["schema_version"] == "analysis_result.v1"
    assert first.headers["Cache-Control"] == "private, no-store"


def test_unknown_expired_missing_and_corrupt_results_fail_closed(client, app):
    assert client.get("/api/v1/operations/does-not-exist").status_code == 404
    session = app.extensions["doxary_container"].session_factory()
    expired = _operation(session, "succeeded")
    session.add(
        OperationResultRecord(
            operation_result_id=str(uuid4()),
            operation_id=expired,
            schema_version="analysis_result.v1",
            result_payload=_payload(),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    missing = _operation(session, "succeeded")
    corrupt = _operation(session, "succeeded")
    session.add(
        OperationResultRecord(
            operation_result_id=str(uuid4()),
            operation_id=corrupt,
            schema_version="analysis_result.v1",
            result_payload={"analysis_status": "complete"},
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    session.commit()
    session.close()
    assert client.get(f"/api/v1/operations/{expired}").status_code == 410
    assert client.get(f"/api/v1/operations/{missing}").status_code == 500
    assert client.get(f"/api/v1/operations/{corrupt}").status_code == 500
