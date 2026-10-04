from bbva_rag.cli import recent_history

HISTORY = [{"role": "user", "content": str(i)} for i in range(10)]


def test_keeps_only_the_last_n_messages():
    assert [m["content"] for m in recent_history(HISTORY, 3)] == ["7", "8", "9"]


def test_zero_means_no_history():
    assert recent_history(HISTORY, 0) == []