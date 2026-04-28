from devagent_core.core.bootstrap import Bootstrap


def test_bootstrap_start():
    b = Bootstrap()
    b.start()

    assert b.storage is not None
    assert b.llm is not None
    assert b.rag is not None
    assert b.edit_tool is not None
    assert b.run_tool is not None