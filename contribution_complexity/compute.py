"""
This program computes the complexity of a Git contribution, i.e. one or more commits.

Usage:
  contribcompl commits [-v | --verbose] <repository> <commit_sha>...
  contribcompl issue [-v | --verbose] <repository> <issue_regex>
  contribcompl -h | --help
  contribcompl --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --output=<kind>  Kind of output, either csv or verbose.
"""
import sys
import tempfile
import subprocess
from shutil import which
from docopt import docopt
from contribution_complexity import __version__
from pathlib import Path
from urllib.parse import urlparse
from contribution_complexity.metrics import (
    compute_contrib_compl,
    toggle_verbose_output,
)


TMP = tempfile.gettempdir()
VERBOSE = False


def git_is_available():
    """Check whether `git` is on PATH"""
    if which("git"):
        return True
    else:
        return False


def is_git_url(potential_url):
    result = urlparse(potential_url)
    is_complete_url = all((result.scheme, result.netloc, result.path))
    is_git = result.path.endswith(".git")
    is_git_user = result.path.startswith("git@")
    if is_complete_url:
        return True
    elif is_git_user and is_git:
        return True
    else:
        return False


def is_git_dir(potential_repo_path):
    if not Path(potential_repo_path).is_dir():
        return False
    cmd = f"git -C {potential_repo_path} rev-parse --is-inside-work-tree"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip() == "true"


def clone_to_tmp(url):
    path = Path(urlparse(url).path)
    outdir = path.name.removesuffix(path.suffix)
    git_repo_dir = os.path.join(TMP, outdir + str(uuid.uuid4()))
    cmd = f"git clone {url} {git_repo_dir}"
    subprocess.run(cmd, shell=True)

    return git_repo_dir


def find_commits_for_issue(path_to_repo, issue_re):

    cmd = f"git -C {path_to_repo} log --extended-regexp --grep='{issue_re}' --pretty=format:'%H'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.splitlines()


def main(path_to_repo, is_url=False, commit_shas=[]):
    path_to_repo_url = path_to_repo
    if is_url:
        path_to_repo = clone_to_tmp(path_to_repo)

    print(compute_metrics(path_to_repo, commit_shas))


def run():
    if not git_is_available():
        msg = "contribcompl requires git to be installed and accessible on path"
        print(msg)
        sys.exit(1)

    arguments = docopt(__doc__, version=__version__)

    if arguments["-v"] == True or arguments["--verbose"] == True:
        toggle_verbose_output()

    path_to_repo = arguments["<repository>"]
    if not (is_git_url(path_to_repo) or is_git_dir(path_to_repo)):
        print(__doc__)
        sys.exit(1)

    if is_git_url(path_to_repo):
        path_to_repo = clone_to_tmp(path_to_repo)

    if arguments["commits"]:
        commit_shas = arguments["<commit_sha>"]
    elif arguments["issue"]:
        issue_re = arguments["<issue_regex>"]
        commit_shas = find_commits_for_issue(path_to_repo, issue_re)
        # print(commit_shas)

    contribcompl = compute_contrib_compl(path_to_repo, commit_shas)
    print(contribcompl)


if __name__ == "__main__":
    run()
