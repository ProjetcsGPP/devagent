from devagent_core.core.bootstrap import Bootstrap
import tempfile
from pathlib import Path


def test_run_tool():
    b = Bootstrap()
    b.start()

    file = Path(tempfile.gettempdir()) / "hello.py"
    file.write_text("print('ok')")

    result = b.run_tool.execute(str(file))

    assert result.return_code == 0