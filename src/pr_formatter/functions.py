import difflib
import os
import re
import shutil
import tempfile
import subprocess
import git_filter_repo as fr


def write_file(content, tmpfile):
    with open(tmpfile, "wb") as f:
        f.write(content)


def read_file(tmpfile):
    with open(tmpfile, "rb") as f:
        return f.read()


def parse_range(text):
    regex = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
    match = regex.search(text)
    if match is None:
        raise ValueError(
            "The line looks like a mal formatter unified diff: " + text)
    start = int(match.group(1))
    count = int(match.group(2) or 1)
    return start, start + count


def parse_ranges(diff):
    return [parse_range(line) for line in diff if line[0] == '@']


def insert_new_line_markers(old, new, begin, end):
    diff = difflib.unified_diff(old, new, n=0)
    ranges = parse_ranges(diff)
    n = 0
    lines = []
    for (start_line, end_line) in ranges:
        lines.extend(new[n: start_line - 1])
        lines.append(begin)
        lines.extend(new[start_line - 1: end_line - 1])
        lines.append(end)
        n = end_line - 1
    lines.extend(new[n:])
    return lines


def insert_formatter_statements(old, new):
    formatter_on = "// @formatter:on PULL-REQUEST-FORMATTER"
    formatter_off = "// @formatter:off PULL-REQUEST-FORMATTER"
    return [formatter_off] + insert_new_line_markers(
        old, new, begin=formatter_on, end=formatter_off)


def remove_formatter_statements(lines):
    formatter_on = "// @formatter:on PULL-REQUEST-FORMATTER"
    formatter_off = "// @formatter:off PULL-REQUEST-FORMATTER"
    return [line for line in lines if line not in [formatter_on, formatter_off]]


def format_java(pom, code):
    temp_dir = tempfile.TemporaryDirectory()
    shutil.copy(pom, temp_dir.name + "/pom.xml")
    source_dir = temp_dir.name + "/src/main/java"
    os.makedirs(source_dir, exist_ok=False)
    java_file = source_dir + "/file.java"
    write_file('\n'.join(code).encode('utf8'), java_file)
    subprocess.check_call(["mvn", "formatter:format"], cwd=temp_dir.name)
    formatted_code = read_file(java_file).decode('utf8').split('\n')
    temp_dir.cleanup()
    return formatted_code


def format_changes(pom, a, b):
    text = insert_formatter_statements(a, b)
    text = format_java(pom, text)
    text = remove_formatter_statements(text)
    return text


def format_changes_binary(pom, a, b):
    lines = format_changes(pom,
                           a.decode('utf8').split('\n'),
                           b.decode('utf8').split('\n'))
    return '\n'.join(lines).encode('utf8')


class GitGetBlob:

    def __init__(self):
        self.process = subprocess.Popen(['git', 'cat-file', '--batch'],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE)

    def get_blob_content(self, blob_id):
        self.process.stdin.write(blob_id + b'\n')
        self.process.stdin.flush()
        objhash, objtype, objsize = self.process.stdout.readline().split()
        contents_plus_newline = self.process.stdout.read(
            int(objsize) + 1)
        contents = contents_plus_newline[:-1]
        return contents

    def close(self):
        self.process.stdin.close()
        self.process.wait()


class ReformatChanges:

    def __init__(self, pom):
        self.pom = pom
        self.git = GitGetBlob()

    def run(self, filename, content):
        old_content = self.git.get_blob_content(b'before:' + filename)
        return format_changes_binary(self.pom, old_content, content)


class Lint:

    def __init__(self, base, head):
        args = fr.FilteringOptions.default_options()
        args.force = True
        args.partial = True
        args.refs = [base + '..' + head]
        args.repack = False
        args.replace_refs = 'update-no-add'
        self.args = args
        self.file_filter = ReformatChanges("pom.xml")
        self.blobs_handled = {}
        self.git_get_blob = None
        self.filter = None

    def run(self):
        self.git_get_blob = GitGetBlob()
        self.filter = fr.RepoFilter(self.args,
                                    commit_callback=self.commit_callback)
        self.filter.run()
        self.git_get_blob.close()

    def is_relevant(self, filename):
        return filename.endswith(b'.java')

    def commit_callback(self, commit, metadata):
        for change in commit.file_changes:
            self.handle_file_change(change)

    def handle_file_change(self, change):
        if not self.is_relevant(change.filename):
            return
        if change.type == b'D':
            return
        if change.blob_id in self.blobs_handled:
            change.blob_id = self.blobs_handled[change.blob_id]
        else:
            content = self.git_get_blob.get_blob_content(change.blob_id)
            new_content = self.file_filter.run(change.filename, content)
            new_blob = fr.Blob(new_content)
            self.filter.insert(new_blob)

            # Record our handling of the blob and use it for this change
            self.blobs_handled[change.blob_id] = new_blob.id
            change.blob_id = new_blob.id


def rewrite_pr(repo, base, head):
    cwd = os.getcwd()
    try:
        os.chdir(repo)
        Lint(base, head).run()
    finally:
        os.chdir(cwd)
