from devagent_core.core.bootstrap import Bootstrap


def test_rag_query():
    b = Bootstrap()
    b.start()

    result = b.rag.query("hello")

    assert "answer" in result