from contestiq_api.judge0_client import _normalized_status


def test_memory_limit_description_is_preserved_as_a_user_code_verdict():
    assert (
        _normalized_status(12, "Memory Limit Exceeded")
        == "memory_limit"
    )


def test_other_runtime_statuses_keep_the_existing_mapping():
    assert _normalized_status(12, "Runtime Error (Other)") == "runtime_error"
