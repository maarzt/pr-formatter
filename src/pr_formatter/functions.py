import os
import re
import tempfile
import subprocess
import git_filter_repo as fr


def write_file(file, content):
    """Writes to content (given as bytes), into the given file."""
    with open(file, "wb") as f:
        f.write(content)


def read_file(file):
    """Returns the content of the text file as bytes."""
    with open(file, "rb") as f:
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


def split_diff(diff):
    lines = diff.decode("utf8").splitlines()
    result = {}
    file = None
    for line in lines:
        match = re.search(r'^\+\+\+ b/(.+)', line)
        if match:
            file = match.group(1)
            result[file] = []
        elif re.match(r'^@@', line):
            result[file].append(line)
    return result


def insert_line_markers(new, diff, begin, end):
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


def format_many_java(pom, code):
    repo = os.path.dirname(pom)
    src_dir = os.path.join(repo, "src/main/java")
    with tempfile.TemporaryDirectory(prefix="pr_formatter_tmp_dir", dir=src_dir) as tmp_dir:
        write_java_files(tmp_dir, code)
        tmp_basename = os.path.basename(tmp_dir)
        param = "-Dformatter.includes=" + tmp_basename + "/"
        subprocess.check_call(["mvn", "formatter:format", param], cwd=repo)
        return read_java_files(tmp_dir, code.keys())


def read_java_files(directory, filenames):
    """Reads the given java files from the directory."""
    return dict([(blob_id, read_file(os.path.join(directory, blob_id.decode("utf8") + ".java"))) for blob_id in filenames])


def write_java_files(directory, names_and_contents):
    """Writes a given dictionary of java files into the give directory."""
    for filename, content in names_and_contents.items():
        write_file(os.path.join(directory, filename.decode("utf8") + ".java"), content)


def insert_formatter_statements_binary(content, diff):
    formatter_on = b"// @formatter:on PULL-REQUEST-FORMATTER\n"
    formatter_off = b"// @formatter:off PULL-REQUEST-FORMATTER\n"
    lines = content.splitlines(keepends=True)
    lines_with_markers = insert_line_markers(lines, diff, begin=formatter_on, end=formatter_off)
    return b''.join([formatter_off] + lines_with_markers)


def remove_formatter_statements_binary(content):
    formatter_on = b"@formatter:on PULL-REQUEST-FORMATTER"
    formatter_off = b"@formatter:off PULL-REQUEST-FORMATTER"
    lines_with_markers = content.splitlines(keepends=True)
    lines = [line for line in lines_with_markers if not (formatter_off in line or formatter_on in line)]
    return b''.join(lines)


def get_file_diffs(base, commit_hash):
    diff = subprocess.check_output(["git", "diff", "--unified=0", base, commit_hash])
    file_diffs = split_diff(diff)
    return file_diffs


class GitGetBlob:

    def __init__(self):
        self.process = subprocess.Popen(['git', 'cat-file', '--batch'],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE)

    def get_blob_content(self, blob_id):
        self.process.stdin.write(blob_id + b'\n')
        self.process.stdin.flush()
        object_hash, object_type, object_size = self.process.stdout.readline().split()
        contents_plus_newline = self.process.stdout.read(
            int(object_size) + 1)
        contents = contents_plus_newline[:-1]
        return contents

    def close(self):
        self.process.stdin.close()
        self.process.wait()


class Lint:

    def __init__(self, base, head):
        args = fr.FilteringOptions.default_options()
        args.force = True
        args.partial = True
        args.refs = [base + '..' + head]
        args.repack = False
        args.replace_refs = 'update-no-add'
        self.args = args
        self.base = base
        self.blobs_handled = {}
        self.git_get_blob = None
        self.filter = None

    def run(self):
        self.git_get_blob = GitGetBlob()
        self.filter = fr.RepoFilter(self.args,
                                    commit_callback=self.commit_callback)
        self.filter.run()
        self.git_get_blob.close()

    def commit_callback(self, commit, metadata):
        file_diffs = get_file_diffs(self.base, commit.original_id)
        file_names = {change.blob_id: change.filename.decode("utf8") for change in commit.file_changes if self.change_is_relevant(change)}
        file_contents = {blob_id: self.git_get_blob.get_blob_content(blob_id) for blob_id in file_names.keys()}
        file_with_statements = {blob_id: insert_formatter_statements_binary(file_contents[blob_id], file_diffs[filename]) for blob_id, filename in file_names.items()}
        file_formatted = format_many_java("./pom.xml", file_with_statements)
        file_new_content = {blob_id: remove_formatter_statements_binary(content) for blob_id, content in file_formatted.items()}

        for change in commit.file_changes:
            self.handle_file_change(change, file_new_content)

    def change_is_relevant(self, change):
        return change.type != b'D' and self.filename_is_relevant(change.filename)

    def filename_is_relevant(self, filename):
        return filename.endswith(b'.java')

    def handle_file_change(self, change, file_new_content):
        if change.blob_id in self.blobs_handled:
            change.blob_id = self.blobs_handled[change.blob_id]
        elif change.blob_id in file_new_content:
            new_content = file_new_content.get(change.blob_id)
            new_blob = fr.Blob(new_content)
            self.filter.insert(new_blob)
            self.blobs_handled[change.blob_id] = new_blob.id
            change.blob_id = new_blob.id


def rewrite_pr(repo, base, head):
    cwd = os.getcwd()
    try:
        os.chdir(repo)
        Lint(base, head).run()
    finally:
        os.chdir(cwd)
