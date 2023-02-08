import pytest
import difflib
import textwrap
import os
import tempfile
import shutil
from pr_formatter import functions


def test_read_file():
    text = functions.read_file("resources/hello.txt").splitlines()
    assert text == [b"Hello World!"]


def test_unified_diff():
    a = ["a", "b", "c"]
    b = ["a", "bb", "c"]
    diff = list(difflib.unified_diff(a, b, n=0))
    assert diff == ['--- \n', '+++ \n', '@@ -2 +2 @@\n', '-b', '+bb']


def test_parse_range():
    assert functions.parse_range('@@ -2 +2 @@') == (2, 3)
    assert functions.parse_range('@@ -25,23 +45,10 @@ something') == (45, 55)


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
    ranges = functions.parse_ranges(diff)
    assert ranges == [(2, 3), (17, 19)]


def test_insert_new_line_markers():
    a = ["a", "b", "c"]
    b = ["a", "bb", "c"]
    r = functions.insert_new_line_markers(
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
    assert functions.insert_formatter_statements(old=a, new=b) == expected


def test_remove_formatter_statements():
    text = textwrap.dedent("""\
        a
        // @formatter:on PULL-REQUEST-FORMATTER
        b
        // @formatter:off PULL-REQUEST-FORMATTER
        c
        """).split('\n')
    expected = ["a", "b", "c", ""]
    assert expected == functions.remove_formatter_statements(text)


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
    assert expected == functions.format_java(pom, text)


def test_format_many_java():
    java_files = {
        "a":b"class A { boolean run() { return true; } }\n",
        "b":b"class B { boolean run() { return false; } }\n"
    }
    expected = {
        'a': b'class A {\n\n\tboolean run() {\n\t\treturn true;\n\t}\n}\n',
        'b': b'class B {\n\n\tboolean run() {\n\t\treturn false;\n\t}\n}\n'
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        pom_xml = os.path.join(tmp_dir, "pom.xml")
        shutil.copyfile("resources/example_pom.xml", pom_xml)
        os.makedirs(os.path.join(tmp_dir, "src/main/java"))
        assert expected == functions.format_many_java(pom_xml, java_files)


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
    assert expected == functions.format_changes(pom, a, b)


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
    assert expected == functions.format_changes_binary(pom, bytes_a, bytes_b)

@pytest.mark.skip(reason="test would fail on any other machine")
def test_git_get_content():
    cwd = os.getcwd()
    try:
        os.chdir("../../../../mastodon")
        git = functions.GitGetBlob()
        git.get_blob_content(
            b"before:src/main/java/org/mastodon/mamut/MainWindow.java")
    finally:
        os.chdir(cwd)
