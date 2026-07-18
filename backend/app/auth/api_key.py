from secrets import compare_digest


def is_valid_api_key(candidate: str | None, expected: str) -> bool:
    if not candidate:
        return False
    return compare_digest(candidate, expected)
