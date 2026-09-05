import pytest

from app.services import sessions


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    data_dir = tmp_path / "runtime"
    monkeypatch.setenv("FINAL_CHECK_DATA_DIR", str(data_dir))
    sessions.configure(data_dir)
    yield data_dir
    sessions.close_all()
