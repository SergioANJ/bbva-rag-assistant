from bbva_rag.evaluation.metrics import first_hit_rank, hit_rate, mean_reciprocal_rank


def test_first_hit_rank_is_one_based():
    assert first_hit_rank(["a", "b", "c"], {"b"}) == 2


def test_first_hit_rank_is_none_when_missing():
    assert first_hit_rank(["a", "b"], {"z"}) is None


def test_hit_rate_counts_only_ranks_within_k():
    assert hit_rate([1, 3, None, 10], k=3) == 0.5


def test_mrr_example():
    # ranks 1, 2 and missing -> (1 + 0.5 + 0) / 3
    assert mean_reciprocal_rank([1, 2, None]) == 0.5
