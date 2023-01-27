import argparse
import os
import subprocess

from pr_formatter.functions import rewrite_pr

def git_merge_base(branchA, branchB):
    output = subprocess.check_output(["git", "merge-base", branchA, branchB])
    hash = output.decode("utf8").split("\n")[0]
    return hash

def main():
    repo = os.getcwd()
    base = git_merge_base("master", "HEAD")
    rewrite_pr(repo, base, "HEAD")


if __name__=="__main__":
    main()
