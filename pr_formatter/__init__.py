import re


def write_file(content, tmpfile):
    with open(tmpfile, "wb") as f:
        f.write(content)


def read_file(tmpfile):
    with open(tmpfile, "rb") as f:
        return f.read()


def parse_range(text):
    regex = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
    match = regex.search(text)
    start = int(match.group(1))
    count = int(match.group(2) or 1)
    return start, start + count
