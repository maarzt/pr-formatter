import pytest
import textwrap
import os
import tempfile
import shutil
from pr_formatter import functions


def test_read_file():
    text = functions.read_file("resources/hello.txt").splitlines()
    assert text == [b"Hello World!"]


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


def test_split_diff():
    diff = textwrap.dedent("""\
        +++ b/a.java
        @@ -3 +4,2 @@
        +++ b/b.java
        @@ -8 +8,9 @@
        """).encode("utf8")
    assert {'a.java': ['@@ -3 +4,2 @@'], 'b.java': ['@@ -8 +8,9 @@']} == functions.split_diff(diff)


def test_insert_formatter_statements():
    a = textwrap.dedent("""\
        class Example {
            boolean getBoolean() {
                return true;
            }
        }
        """).encode("utf8")
    b = ["@@ -3 +3 @@"]
    expected = textwrap.dedent("""\
        // @formatter:off PULL-REQUEST-FORMATTER
        class Example {
            boolean getBoolean() {
        // @formatter:on PULL-REQUEST-FORMATTER
                return true;
        // @formatter:off PULL-REQUEST-FORMATTER
            }
        }
        """).encode("utf8")
    assert functions.insert_formatter_statements_binary(content=a, diff=b) == expected


def test_remove_formatter_statements():
    text = textwrap.dedent("""\
        a
        // @formatter:on PULL-REQUEST-FORMATTER
        b
        // @formatter:off PULL-REQUEST-FORMATTER
        c
        """).encode("utf8")
    assert functions.remove_formatter_statements_binary(text) == b"a\nb\nc\n"


def test_format_many_java():
    java_files = {
        b'a': b'class A { boolean run() { return true; } }\n',
        b'b': b'class B { boolean run() { return false; } }\n'
    }
    expected = {
        b'a': b'class A {\n\n\tboolean run() {\n\t\treturn true;\n\t}\n}\n',
        b'b': b'class B {\n\n\tboolean run() {\n\t\treturn false;\n\t}\n}\n'
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        pom_xml = os.path.join(tmp_dir, "pom.xml")
        shutil.copyfile("resources/example_pom.xml", pom_xml)
        os.makedirs(os.path.join(tmp_dir, "src/main/java"))
        assert expected == functions.format_many_java(pom_xml, java_files)


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
