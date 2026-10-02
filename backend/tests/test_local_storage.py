import base64
from pathlib import Path
from app.core.config import settings
from app.infrastructure.storage_service import StorageService, get_storage_service


def test_local_storage_backend(tmp_path, monkeypatch):
  monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")

  svc = StorageService(
    backend="local",
    endpoint="",
    access_key="",
    secret_key="",
    bucket="",
    public_url="",
  )
  svc._local_dir = tmp_path

  # 1x1 white pixel PNG
  sample_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

  url = svc.save_step_screenshot(sample_b64, [])

  assert url.startswith("/evidence/screenshots/")
  filename = url.split("/")[-1]
  saved_file = tmp_path / filename
  assert saved_file.exists()
  assert saved_file.stat().st_size > 0
