from vectoreels.processing.mining import cluster_captions


def test_cluster_captions_counts_exact_duplicates_meeting_threshold() -> None:
    captions = ["Follow for more!"] * 10
    assert cluster_captions(captions, min_count=10) == [("Follow for more!", 10)]


def test_cluster_captions_ignores_clusters_below_min_count() -> None:
    captions = ["Follow for more!"] * 9
    assert cluster_captions(captions, min_count=10) == []


def test_cluster_captions_treats_case_and_punctuation_as_equivalent() -> None:
    captions = ["Follow for more!"] * 5 + ["follow for more"] * 5
    assert cluster_captions(captions, min_count=10) == [("Follow for more!", 10)]


def test_cluster_captions_merges_truncated_variant_into_longer_original() -> None:
    full = "Follow for more content like this and never miss an update"
    truncated = "Follow for more content like this"
    captions = [full] * 6 + [truncated] * 5
    result = cluster_captions(captions, min_count=10)
    assert result == [(full, 11)]


def test_cluster_captions_reports_standalone_truncation_with_no_longer_variant() -> None:
    captions = ["Follow for more content"] * 10
    assert cluster_captions(captions, min_count=10) == [("Follow for more content", 10)]


def test_cluster_captions_skips_empty_captions() -> None:
    captions = ["", None, ""] * 10  # type: ignore[list-item]
    assert cluster_captions(captions, min_count=1) == []


def test_cluster_captions_does_not_merge_unrelated_captions() -> None:
    captions = ["A totally different caption about cats"] * 10 + ["Another unrelated one"] * 10
    result = cluster_captions(captions, min_count=10)
    assert set(result) == {
        ("A totally different caption about cats", 10),
        ("Another unrelated one", 10),
    }
