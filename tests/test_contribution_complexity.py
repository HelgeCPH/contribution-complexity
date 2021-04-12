import subprocess
from contribution_complexity import __version__
from contribution_complexity.metrics import _get_no_files_at_commit
from contribution_complexity.metrics import _compute_hunks
from contribution_complexity.metrics import stats_per_modification
from contribution_complexity.metrics import compute_contrib_compl
from contribution_complexity.complexity_types import ContributionComplexity


def test_version():
    assert __version__ == "0.1.0"


# TODO Add clone as first step


def test_get_no_files_at_commit():
    path_to_repo = "/tmp/cassandra/"
    commit_sha = "a991b64811f4d6adb6c7b31c0df52288eb06cf19"

    result = _get_no_files_at_commit(path_to_repo, commit_sha)
    assert result == 2045


def test_get_no_files_at_commit2():
    path_to_repo = "/tmp/gaffer/"
    commit_sha = "ee3e2a78e21fcaf206126179f82918e9161054e5"

    result = _get_no_files_at_commit(path_to_repo, commit_sha)
    assert result == 2045


def test_compute_hunks():
    # See https://github.com/apache/cassandra/commit/a991b64811f4d6adb6c7b31c0df52288eb06cf19#diff-18bc10dfa07f8c2c41f2b32a3d5c0e9c304b65b08cd1e80d34ccba6ce54cb2d6
    path_to_repo = "/tmp/cassandra/"
    commit_sha = "a991b64811f4d6adb6c7b31c0df52288eb06cf19"

    rm = RepositoryMining(path_to_repo, only_commits=commit_shas)
    modifications = [m for m in commit.modifications]
    m = modifications[5]

    result = _compute_hunks(m)
    assert result == 6


def test_stats_per_modification():
    path_to_repo = "/tmp/cassandra/"
    commit_sha = "a991b64811f4d6adb6c7b31c0df52288eb06cf19"

    rm = RepositoryMining(path_to_repo, only_commits=commit_shas)
    modifications = [m for m in commit.modifications]
    m = modifications[74]
    result = stats_per_modification(m)


def test_compute_contrib_compl_high():
    path_to_repo = "/tmp/cassandra/"
    commit_shas = ["a991b64811f4d6adb6c7b31c0df52288eb06cf19"]

    result = compute_contrib_compl(path_to_repo, commit_sha)
    assert result == ContributionComplexity.HIGH


def test_compute_contrib_compl_low():
    path_to_repo = "/tmp/cassandra/"
    commit_shas = [
        "021df085074b761f2b3539355ecfc4c237a54a76",
        "2f1d6c7254342af98c2919bd74d37b9944c41a6b",
    ]

    result = compute_contrib_compl(path_to_repo, commit_sha)
    assert result == ContributionComplexity.LOW


def end_to_end():
    cmd = "contribcompl commits /tmp/cassandra a991b64811f4d6adb6c7b31c0df52288eb06cf19"
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.stdout.strip() == "ContributionComplexity.LOW"


def end_to_end2():
    cmd = "contribcompl commits /tmp/cassandra 021df085074b761f2b3539355ecfc4c237a54a76 2f1d6c7254342af98c2919bd74d37b9944c41a6b"
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.stdout.strip() == "ContributionComplexity.LOW"


# For example:
# * a low complex modification (modifications[74]):
#   https://github.com/apache/cassandra/commit/a991b64811f4d6adb6c7b31c0df52288eb06cf19#diff-dc6b08be6e6dcf5a433d53fd96e1c6a6f0e9cb519e45aa3c7af2cd61e3c0c96a
# * a more complex modification (modifications[8]):
#   https://github.com/apache/cassandra/commit/a991b64811f4d6adb6c7b31c0df52288eb06cf19#diff-36b7f71b10b1da61116b8099bb0744e817be08d59f415ddc87c61711c9e24d31
# * a high complex modification (modifications[9])
#   https://github.com/apache/cassandra/commit/a991b64811f4d6adb6c7b31c0df52288eb06cf19#diff-5e9f92fef6740c38afdb7ab92577c6c539f6c65232cc214fa6cd22657531e495
