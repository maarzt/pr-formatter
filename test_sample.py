import pytest
import pr_formatter
import difflib
import textwrap
import os


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


def test_parse_ranges():
    diff = ["--- something",
            "+++ else",
            "@@ -2 +2 @@ foo",
            "- hello",
            "+ world",
            "@@ -17 +17,2 @@",
            "- foo bar",
            "+ foo",
            "+ bar"]
    ranges = pr_formatter.parse_ranges(diff)
    assert ranges == [(2, 3), (17, 19)]


def test_insert_new_line_markers():
    a = ["a", "b", "c"]
    b = ["a", "bb", "c"]
    r = pr_formatter.insert_new_line_markers(
        a, b, begin="_begin_", end="_end_")
    assert r == ["a", "_begin_", "bb", "_end_", "c"]


def test_insert_formatter_statements():
    a = textwrap.dedent("""\
        class Example {
            boolean getBoolean() {
                return false;
            }
        }
        """).split('\n')
    b = [line.replace("false", "true") for line in a]
    expected = textwrap.dedent("""\
        // @formatter:off PULL-REQUEST-FORMATTER
        class Example {
            boolean getBoolean() {
        // @formatter:on PULL-REQUEST-FORMATTER
                return true;
        // @formatter:off PULL-REQUEST-FORMATTER
            }
        }
        """).split('\n')
    assert pr_formatter.insert_formatter_statements(old=a, new=b) == expected


def test_remove_formatter_statements():
    text = textwrap.dedent("""\
        a
        // @formatter:on PULL-REQUEST-FORMATTER
        b
        // @formatter:off PULL-REQUEST-FORMATTER
        c
        """).split('\n')
    expected = ["a", "b", "c", ""]
    assert expected == pr_formatter.remove_formatter_statements(text)


def test_format_java():
    text = textwrap.dedent("""\
        class Example {
            boolean getBoolean() {
                return     true;
            }
        }
        """).split('\n')
    pom = "resources/example_pom.xml"
    expected = textwrap.dedent("""\
        class Example {
        
        \tboolean getBoolean() {
        \t\treturn true;
        \t}
        }
        """).split('\n')
    assert expected == pr_formatter.format_java(pom, text)


def test_format_changes():
    pom = "resources/example_pom.xml"
    a = textwrap.dedent("""\
        class Example {
        
        \tboolean    getBoolean() {
        \t\treturn    false;
        \t}
        }
        """).split('\n')
    b = [line.replace("false", "true") for line in a]
    expected = [line.replace("   false", "true") for line in a]
    assert expected == pr_formatter.format_changes(pom, a, b)


def test_format_changes_binary():
    pom = "resources/example_pom.xml"
    a = textwrap.dedent("""\
        class Example {
        
        \tboolean    getBoolean() {
        \t\treturn    false;
        \t}
        }
        """)
    bytes_a = a.encode('utf8')
    bytes_b = a.replace('false', 'true').encode('utf8')
    expected = a.replace("   false", "true").encode('utf8')
    assert expected == pr_formatter.format_changes_binary(pom, bytes_a, bytes_b)

@pytest.mark.skip(reason="test would fail on any other machine")
def test_git_get_content():
    cwd = os.getcwd()
    try:
        os.chdir("../mastodon")
        git = pr_formatter.GitGetBlob()
        git.get_blob_content(
            b"before:src/main/java/org/mastodon/mamut/MainWindow.java")
    finally:
        os.chdir(cwd)
