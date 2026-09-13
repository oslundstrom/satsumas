"""S0's test: the import convention the whole repo depends on.

Every downstream stage assumes ``satsumas`` resolves from an arbitrary working
directory — notebooks, cron jobs on a Pi, a Kubernetes Job. If the editable
install or the src layout breaks, this fails here rather than in a notebook at
S3 or in a decode job at S7.
"""

import subprocess
import sys
from pathlib import Path

import satsumas


def test_version_is_exposed():
    assert isinstance(satsumas.__version__, str)
    assert satsumas.__version__


def test_importable_from_an_unrelated_working_directory(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, "-c", "import satsumas; print(satsumas.__version__)"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == satsumas.__version__
