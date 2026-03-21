"""Tests for the public API surface of azure-functions-scaffold."""

from importlib import import_module
from typing import Protocol, cast


class _PublicAPI(Protocol):
    __all__: list[str]
    __version__: str


azure_functions_scaffold = cast(_PublicAPI, cast(object, import_module("azure_functions_scaffold")))


class TestAPISurface:
    """Verify __all__ matches exactly the declared public names."""

    def test_all_exports(self) -> None:
        assert set(azure_functions_scaffold.__all__) == {"__version__"}

    def test_version_is_0_3_2(self) -> None:
        assert azure_functions_scaffold.__version__ == "0.3.2"

    def test_version_is_string(self) -> None:
        assert isinstance(azure_functions_scaffold.__version__, str)
