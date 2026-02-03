"""Test version information."""

import blogspot_publishing  # type: ignore


def test_version():
    """Test that version is defined."""
    assert hasattr(blogspot_publishing, "__version__")
    assert blogspot_publishing.__version__ == "v1"
