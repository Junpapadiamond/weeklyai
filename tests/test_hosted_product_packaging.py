"""Exercise the shared identity import without the checkout on PYTHONPATH."""
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_crawler_image_layout_can_import_the_single_shared_implementation(tmp_path):
    app = tmp_path / 'app'
    backend = tmp_path / 'backend'
    (app / 'utils').mkdir(parents=True)
    backend.mkdir()
    shutil.copy2(ROOT / 'crawler/utils/product_identity.py', app / 'utils/product_identity.py')
    shutil.copy2(ROOT / 'backend/product_identity.py', backend / 'product_identity.py')
    result = subprocess.run(
        [sys.executable, '-c',
         'from pathlib import Path; from utils.product_identity import hosted_project_key; '
         'import product_identity; '
         "assert hosted_project_key('https://github.com/RLinf/RPent') == 'github.com/rlinf/rpent'; "
         "assert Path(product_identity.__file__).resolve() == Path('../backend/product_identity.py').resolve()"],
        cwd=app, env={**os.environ, 'PYTHONPATH': ''}, capture_output=True, text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_backend_image_layout_does_not_require_the_crawler(tmp_path):
    shutil.copy2(ROOT / 'backend/product_identity.py', tmp_path / 'product_identity.py')
    result = subprocess.run(
        [sys.executable, '-c',
         'from product_identity import hosted_project_key; '
         "assert hosted_project_key('https://github.com/RLinf/RPent') == 'github.com/rlinf/rpent'"],
        cwd=tmp_path, env={**os.environ, 'PYTHONPATH': ''}, capture_output=True, text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
