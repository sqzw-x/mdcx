import sys
from pathlib import Path

import pytest

from mdcx.utils.path import is_descendant


@pytest.mark.skipif(sys.platform == "win32", reason="This test is not applicable on Windows")
@pytest.mark.parametrize(
    "p, parent, expected",
    [
        # Basic cases
        ("/a/b/c", "/a/b", True),
        ("/a/b/c", "/a/b/./", True),
        ("/a/b", "/a/b", True),
        ("/a/b", "/a/b/", True),
        ("/a/b", "/a/b/.", True),
        ("/a/c", "/a/b", False),
        ("/a/b", "/a/b/c", False),
        ("/a/b/../c", "/a", True),
        ("/a/b/../c", "/a/c", True),
        ("/a/b/.", "/a/b", True),
        # Relative paths
        ("a/b/c", "a/b", True),
        ("a/b", "a/b", True),
        ("a/c", "a/b", False),
        ("a/c", "a/b/..", True),
        # Path objects
        (Path("/a/b/c"), Path("/a/b"), True),
        (Path("a/b/c"), Path("a/b"), True),
        # Edge cases
        ("/a/barbar", "/a/bar", False),
        ("/a/bar", "/a/barbar", False),
        ("/", "/", True),
        ("/..", "/", True),
        ("/a", "/", True),
        # Mixed types
        (Path("/a/b/c"), "/a/b", True),
        ("/a/b/c", Path("/a/b"), True),
    ],
)
def test_is_descendant_posix(p, parent, expected):
    assert is_descendant(p, parent) == expected


@pytest.mark.skipif(sys.platform != "win32", reason="This is a test about Windows paths.")
@pytest.mark.parametrize(
    "p, parent, expected",
    [
        ("C:\\Users\\Test", "C:\\Users", True),
        ("C:\\Users\\Test", "C:\\", True),
        ("C:\\Users\\Test", "D:\\Users", False),
        ("C:\\Users\\Test\\", "C:\\Users", True),
        ("C:\\Users\\Test", "C:\\Users\\", True),
        ("C:/Users/Test", "C:/Users", True),
        (Path("C:/Users/Test"), Path("C:/Users"), True),
        (Path("C:/Users/Test"), "C:/Users", True),
        ("C:/Users/Test", Path("C:/Users"), True),
    ],
)
def test_is_descendant_windows(p, parent, expected):
    assert is_descendant(p, parent) == expected
