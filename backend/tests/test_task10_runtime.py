from app.models.schemas import CheckSession, Evidence, FindingStatus, ValidationResult
from app.services import sessions
from app.services.storage import SQLiteRuntimeStore


def finding(result_id: str) -> ValidationResult:
    evidence = Evidence(source="notice", locator="page-001", excerpt="제출 파일을 확인해야 합니다.")
    return ValidationResult(
        id=result_id,
        requirement_id="G001",
        status=FindingStatus.REVIEW,
        title="확인 필요",
        explanation="검증이 완료되지 않았습니다.",
        action="직접 확인하세요.",
        announcement_evidence=evidence,
    )


def test_restart_fails_abandoned_validation_closed_and_preserves_previous_results(tmp_path):
    stamp = sessions.now()
    incomplete = finding("current")
    previous = finding("previous")
    store = SQLiteRuntimeStore(tmp_path)
    store.save_session(CheckSession(
        id="11111111-1111-4111-8111-111111111111",
        created_at=stamp,
        updated_at=stamp,
        mode="custom",
        run_state="RUNNING",
        status="REVIEW_REQUIRED",
        results=[incomplete],
        previous_results=[previous],
    ))

    sessions.configure(tmp_path)

    recovered = SQLiteRuntimeStore(tmp_path).get_session(
        "11111111-1111-4111-8111-111111111111"
    )
    assert recovered.run_state == "FAILED"
    assert recovered.status == "REVIEW_REQUIRED"
    assert recovered.validation_complete is False
    assert recovered.run_error == "PROCESS_RESTART"
    assert recovered.results == []
    assert recovered.previous_results == [previous]
