from __future__ import annotations

import pytest

from azure_functions_scaffold.errors import ScaffoldError


def test_scaffold_error_preserves_message_when_raised() -> None:
    # Given
    message = "destination already exists"

    # When
    with pytest.raises(ScaffoldError) as exc_info:
        raise ScaffoldError(message)

    # Then
    assert str(exc_info.value) == message


def test_scaffold_error_is_a_runtime_error() -> None:
    # Given
    error = ScaffoldError("generation failed")

    # When
    caught_by_runtime_error_handler = isinstance(error, RuntimeError)

    # Then
    assert caught_by_runtime_error_handler is True
