import pr_formatter
import difflib


def test_add():
    assert 2 + 3 == 5


def test_read_file():
    text = pr_formatter.read_file("resources/hello.txt").splitlines()
    assert text == [b"Hello World!"]


def test_unified_diff():
    a = ["a", "b", "c"]
    b = ["a", "bb", "c"]
    diff = list(difflib.unified_diff(a, b, n=0))
    assert diff == ['--- \n', '+++ \n', '@@ -2 +2 @@\n', '-b', '+bb']


def test_parse_range():
    assert pr_formatter.parse_range('@@ -2 +2 @@') == (2, 3)
    assert pr_formatter.parse_range('@@ -25,23 +45,10 @@ something') == (45, 55)

