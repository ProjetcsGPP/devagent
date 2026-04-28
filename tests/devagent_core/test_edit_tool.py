from devagent_core.core.bootstrap import Bootstrap
import tempfile
from pathlib import Path


def test_edit_tool_basic():
    b = Bootstrap()
    b.start()

    file = Path(tempfile.gettempdir()) / "devagent_test.py"
    file.write_text("print('hello')")

    result = b.edit_tool.execute(
        file_path=str(file),
        instruction="adicionar comentário no topo"
    )

    assert result.success is True