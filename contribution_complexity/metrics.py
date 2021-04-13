import math
import subprocess
from pathlib import Path
from statistics import mean
from collections import Counter
from pydriller import RepositoryMining, ModificationType
from contribution_complexity.complexity_types import (
    ModificationComplexity,
    ContributionComplexity,
)

VERBOSE = False


def toggle_verbose_output():
    global VERBOSE
    VERBOSE = not VERBOSE


# Load custom models from configuration file in HOME unless it does not exist,
# is erroneous, etc,
try:
    _home = Path.home() / ".contribcomplmodels.py"
    exec(_home.read_text())
    model_names = [
        "LINE_MODEL",
        "CHURN_MODEL",
        "HUNK_MODEL",
        "METHOD_MODEL",
        "FILE_MODEL",
        "MODIFICATION_KIND_MODEL",
        "MOD_COMPL_WEIGHTS",
        "MODIFICATION_MODEL",
    ]
    for model in model_names:
        if model not in globals().keys():
            raise Exception()
    use_default_model = False
except SyntaxError:
    print(f"Syntax error in {_home} using default models...")
    use_default_model = True
except FileNotFoundError:
    print(f"No config file in {_home} using default models...")
    use_default_model = True
except Exception:
    print(f"Not all models seem to be configured in {_home}")
    use_default_model = True
if use_default_model:
    from contribution_complexity.default_models import (
        LINE_MODEL,
        CHURN_MODEL,
        HUNK_MODEL,
        METHOD_MODEL,
        FILE_MODEL,
        MODIFICATION_KIND_MODEL,
        MOD_COMPL_WEIGHTS,
        MODIFICATION_MODEL,
    )


def weigh_modifications(mod_freqs):

    wsum = 0
    for name in ModificationComplexity:
        freq = mod_freqs.get(name, 0)
        w = MOD_COMPL_WEIGHTS[name]
        wsum += freq * w
    return wsum


def discretize_contrib_stats(stats):

    modified_files_compl = to_complexity(stats["no_modified_files"], FILE_MODEL)
    lines_mod_compl = to_complexity(stats["changed_l_per_f"], LINE_MODEL)
    mod_kind_compl = to_complexity(
        stats["no_modificationtypes"], MODIFICATION_KIND_MODEL
    )
    mod_compl = to_complexity(
        weigh_modifications(stats["mods_compl_freq"]), MODIFICATION_MODEL
    )
    return (
        modified_files_compl,
        lines_mod_compl,
        mod_kind_compl,
        mod_compl,
    )


# [weigh_modifications(v["mods_compl_freq"]) for k, v in results_dict.items()]

# for k, v in results_dict.items():
#     if weigh_modifications(v["mods_compl_freq"]) < 40:
#         print(v)

# class ModificationType(Enum):
#     """
#     Type of Modification. Can be ADD, COPY, RENAME, DELETE, MODIFY or UNKNOWN.
#     """

#     ADD = 1
#     COPY = 2
#     RENAME = 3
#     DELETE = 4
#     MODIFY = 5
#     UNKNOWN = 6


def _get_no_files_at_commit(path_to_repo, commit_sha):
    cmd = f"git -C {path_to_repo} ls-tree -r --name-status {commit_sha} | wc -l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    try:
        no_files_at_commit = int(result.stdout.strip())
    except ValueError:
        no_files_at_commit = None

    return no_files_at_commit


def _compute_hunks(mod):
    is_hunk = False
    no_hunks = 0

    for line in mod.diff.splitlines():
        if line.startswith("+") or line.startswith("-"):
            if not is_hunk:
                is_hunk = True
                no_hunks += 1
        else:
            is_hunk = False
    return no_hunks


def to_complexity(val, model):
    for idx, (low, up) in enumerate(model):
        if low < val <= up:
            return ModificationComplexity(idx + 1)


def discretize_stats(stats):
    # for lines added, removed, changes
    # LINE_MODEL = ((-1, 15), (15, 30), (30, 60), (60, 90), (90, math.inf))
    # CHURN_MODEL = (
    #     (-math.inf, -30),
    #     (-30, -15),
    #     (-15, 15),
    #     (15, 30),
    #     (30, math.inf),
    # )
    # HUNK_MODEL = ((-1, 2), (2, 5), (5, 7), (7, 9), (9, math.inf))
    # METHOD_MODEL = ((-1, 2), (2, 5), (5, 7), (7, 9), (9, math.inf))

    lines_add_compl = to_complexity(stats["no_lines_added"], LINE_MODEL)
    lines_del_compl = to_complexity(stats["no_lines_removed"], LINE_MODEL)
    changes_compl = to_complexity(stats["no_changes"], LINE_MODEL)
    churn_compl = to_complexity(stats["churn"], CHURN_MODEL)
    hunk_compl = to_complexity(stats["no_hunks"], HUNK_MODEL)
    method_compl = to_complexity(stats["no_methods_changed"], METHOD_MODEL)
    # stats["churn"]
    # stats["no_hunks"]
    # stats["no_methods_changed"]
    # TODO: Shall I map them to complexities too?
    # stats["no_total_methods"]
    # stats["method_change_ratio"]
    return (
        lines_add_compl,
        lines_del_compl,
        changes_compl,
        churn_compl,
        hunk_compl,
        method_compl,
    )


def aggregate_complexity_vals(complexities):
    compl_vals = [el.value for el in complexities]
    compl_val = int(round(mean(compl_vals), 0))
    return ModificationComplexity(compl_val)


def aggregate_final_complexity_vals(complexities):
    compl_vals = [el.value for el in complexities]
    compl_val = int(round(mean(compl_vals), 0))
    return ContributionComplexity(compl_val)


def discrete_complexity_mod(mod):
    if (mod.change_type == ModificationType.DELETE) or (
        mod.change_type == ModificationType.COPY
    ):
        return ModificationComplexity.LOW
    else:
        stats = stats_per_modification(mod)
        dstats = discretize_stats(stats)
        return aggregate_complexity_vals(dstats)


def discrete_complexity_commit(commit):
    # if (mod.change_type == ModificationType.DELETE) or (
    #     mod.change_type == ModificationType.COPY
    # ):
    #     return ModificationComplexity.LOW
    # else:
    stats = stats_per_commit(commit)
    # dstats = discretize_stats_commit(stats)
    # return aggregate_complexity_vals(dstats)
    return None


def stats_per_modification(mod):
    # mod.change_type

    no_lines_added = mod.added
    no_lines_removed = mod.removed
    no_changes = no_lines_added + no_lines_removed
    churn = mod.added - mod.removed
    no_hunks = _compute_hunks(mod)

    # no_total_lines = len(m.source_code.splitlines())
    # no_loc = m.nloc
    # no_tokens = m.token_count

    # mod.changed_methods

    method_sigs = set([i.long_name for i in mod.methods])
    method_sigs_before = set([i.long_name for i in mod.methods_before])
    # We convert the changed method list into a set since old and new version
    # would otherwise be counted twice
    no_methods_changed = len(set([i.long_name for i in mod.changed_methods]))
    no_total_methods = len(method_sigs_before.union(method_sigs))
    if no_total_methods != 0:
        method_change_ratio = no_methods_changed / no_total_methods
    else:
        method_change_ratio = 0  # None

    return {
        "no_lines_added": no_lines_added,
        "no_lines_removed": no_lines_removed,
        "no_changes": no_changes,
        "churn": churn,
        "no_hunks": no_hunks,
        "no_methods_changed": no_methods_changed,
        "no_total_methods": no_total_methods,
        "method_change_ratio": method_change_ratio,
    }


# git -C /tmp/gaffer log --extended-regexp --grep='gh-2228( |$)' --pretty=format:'%H %s%m'


def stats_per_commit(path_to_repo, commit):
    no_modified_files = commit.files
    # no_files_at_commit = _get_no_files_at_commit(path_to_repo, commit.hash)
    # I think it is impossible that no_files_at_commit ever becomes 0, therefore
    # no check for it
    # file_change_ratio = no_modified_files / no_files_at_commit

    no_lines = commit.lines
    no_added_per_commit = commit.insertions
    no_removed_per_commit = commit.deletions

    # changed_l_per_f = no_lines / no_modified_files  # map to LINE_MODEL

    # modifications = [m for m in commit.modifications]

    # aggregate_complexity_vals([discrete_complexity(m) for m in modifications])
    # Counter({1: 204, 3: 96, 2: 149, 5: 29, 4: 167})

    mod_kinds = [m.change_type for m in commit.modifications]

    # # ####
    # mod_kinds.index(ModificationType.RENAME)  # 74
    # # ####

    # mod_kind_freqs = dict(Counter(mod_kinds))
    # {'DELETE': 125, 'MODIFY': 378, 'ADD': 125, 'RENAME': 17}
    # no_modificationtypes = len(mod_kind_freqs.keys())

    discr_compl_mods = [
        discrete_complexity_mod(m) for m in commit.modifications
    ]

    result = {
        "no_modified_files": no_modified_files,
        # "no_files_at_commit": no_files_at_commit,
        # "file_change_ratio": file_change_ratio,
        "no_lines": no_lines,
        "no_added_per_commit": no_added_per_commit,
        "no_removed_per_commit": no_removed_per_commit,
        # "changed_l_per_f": changed_l_per_f,
        "mod_kinds": mod_kinds,
        # "mod_kind_freqs": mod_kind_freqs,
        # "no_modificationtypes": no_modificationtypes,
        "discr_compl_mods": discr_compl_mods,
    }

    if VERBOSE:
        if commit.modifications:
            print("+", commit.hash)
        else:
            print("-", commit.hash)

        print(result)
    return result


def compute_metrics(path_to_repo, commit_shas):
    # path_to_repo = "/tmp/cassandra"
    # commit_shas = ["a991b64811f4d6adb6c7b31c0df52288eb06cf19"]

    no_modified_files = 0  # no_files_at_commit = 0
    no_lines = no_added = no_removed = 0
    mod_kinds = []
    discr_compl_mods = []

    rm = RepositoryMining(path_to_repo, only_commits=commit_shas)
    for commit in rm.traverse_commits():
        stats = stats_per_commit(path_to_repo, commit)

        no_modified_files += stats["no_modified_files"]
        no_lines += stats["no_lines"]
        no_added += stats["no_added_per_commit"]
        no_removed += stats["no_removed_per_commit"]

        mod_kinds += stats["mod_kinds"]
        discr_compl_mods += stats["discr_compl_mods"]

    if no_modified_files == 0:
        # That should never happen... But it might in case the commits are not
        # reachable, e.g., checked out an earlier version.
        changed_l_per_f = 0
    else:
        changed_l_per_f = no_lines / no_modified_files
    mod_kind_freqs = dict(Counter(mod_kinds))

    no_modificationtypes = len(mod_kind_freqs.keys())

    mods_compl_freq = dict(Counter(discr_compl_mods))

    result = {
        "no_modified_files": no_modified_files,
        "no_lines": no_lines,
        "no_added": no_added,
        "no_removed": no_removed,
        "changed_l_per_f": changed_l_per_f,
        # "mod_kinds": mod_kinds,
        "mod_kind_freqs": mod_kind_freqs,
        "no_modificationtypes": no_modificationtypes,
        "mods_compl_freq": mods_compl_freq,
    }

    if VERBOSE:
        print(result)

    return result


def compute_contrib_compl(path_to_repo, commit_shas):
    stats = compute_metrics(path_to_repo, commit_shas)
    dstats = discretize_contrib_stats(stats)
    if VERBOSE:
        print(dstats)
    return aggregate_final_complexity_vals(dstats)


# def discretize_stats(stats):
#     no_modified_files_compl = to_complexity(
#         stats["no_modified_files"], FILE_MODEL
#     )
#     lines_del_compl = to_complexity(stats["no_lines"], LINE_MODEL)
#     changes_compl = to_complexity(stats["no_changes"], LINE_MODEL)
#     churn_compl = to_complexity(stats["churn"], CHURN_MODEL)
#     hunk_compl = to_complexity(stats["no_hunks"], HUNK_MODEL)
#     method_compl = to_complexity(stats["no_methods_changed"], METHOD_MODEL)
#     # stats["churn"]
#     # stats["no_hunks"]
#     # stats["no_methods_changed"]
#     # TODO: Shall I map them to complexities too?
#     # stats["no_total_methods"]
#     # stats["method_change_ratio"]
#     return (
#         lines_add_compl,
#         lines_del_compl,
#         changes_compl,
#         churn_compl,
#         hunk_compl,
#         method_compl,
#     )

#     # TODO: Aggregate stats

#     cf = [c.files for c in rm_all.traverse_commits()]
#     cf = pd.Series(cf)

#     cf_df[(cf_df.cf > 15) & (cf_df.cf <= 30)]
#     return stats
