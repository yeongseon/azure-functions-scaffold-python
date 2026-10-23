import pytest


@pytest.fixture(autouse=True)
def isolate_verification_job_summary(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    if request.node.path.name.startswith("test_verification"):
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
