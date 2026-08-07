from contestiq_api.judge0_client import _normalized_status


def test_normalized_status_memory_limit_description_is_preserved():
    assert (
        _normalized_status(12, "Memory Limit Exceeded")
        == "memory_limit"
    )


def test_normalized_status_other_runtime_keeps_mapping():
    assert _normalized_status(12, "Runtime Error (Other)") == "runtime_error"


def test_outputs_match_ignores_trailing_newlines_and_crlf():
    from contestiq_api.judge0_client import _outputs_match

    assert _outputs_match("3\n", "3")
    assert _outputs_match("3\r\n", "3\n")
    assert not _outputs_match("1\n", "3\n")
