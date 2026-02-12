"""Test version information."""

import blogger  # type: ignore


def test_version():
    """Test that version is defined."""
    assert hasattr(blogger, "__version__")
    assert blogger.__version__ == "v1.3"
