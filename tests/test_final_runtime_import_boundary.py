import subprocess
import sys


def test_fastapi_import_does_not_load_legacy_prediction_service():
    code = "import sys; from app.main import app; assert 'app.services.prediction' not in sys.modules; print(app.title)"
    result = subprocess.run([sys.executable, "-c", code], env={"PYTHONPATH": ".:backend", "DL_PRELOAD_ON_STARTUP": "false", "AI_ADVISOR_PROVIDER": "local"}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
