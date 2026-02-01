"""Test version information."""

import blogspot_publishing


def test_version():
    """Test that version is defined."""
    assert hasattr(blogspot_publishing, "__version__")
    assert blogspot_publishing.__version__ == "0.1.0"
