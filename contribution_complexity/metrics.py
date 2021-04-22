import math
import subprocess
from pathlib import Path
from statistics import mean
from collections import Counter
from pydriller import RepositoryMining, ModificationType
from contribution_complexity.complexity_types import (
    ModificationComplexity,
    CommitComplexity,
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
        HUNK_MODEL,
        METHOD_MODEL,
        FILE_MODEL,
        MODIFICATION_KIND_MODEL,
        MOD_COMPL_WEIGHTS,
        MODIFICATION_MODEL,
    )


# ======================


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


def metrics_per_mod(mod):
    no_lines_added = mod.added
    no_lines_removed = mod.removed
    no_hunks = _compute_hunks(mod)
    # We convert the changed method list into a set since old and new version
    # would otherwise be counted twice
    no_methods_changed = len(set([i.long_name for i in mod.changed_methods]))

    return {
        "no_lines_added": no_lines_added,
        "no_lines_removed": no_lines_removed,
        "no_hunks": no_hunks,
        "no_methods_changed": no_methods_changed,
    }


def to_mod_compl(val, model):
    for idx, (low, up) in enumerate(model):
        if low < val <= up:
            return ModificationComplexity(idx + 1)


def discretize_mod_metrics(metrics):
    """Maps metric absolute metrics values to a discrete value of type
    ModificationComplexity
    """
    lines_add_compl = to_mod_compl(metrics["no_lines_added"], LINE_MODEL)
    lines_del_compl = to_mod_compl(metrics["no_lines_removed"], LINE_MODEL)
    hunk_compl = to_mod_compl(metrics["no_hunks"], HUNK_MODEL)
    method_compl = to_mod_compl(metrics["no_methods_changed"], METHOD_MODEL)

    return {
        "lines_add_compl": lines_add_compl,
        "lines_del_compl": lines_del_compl,
        "hunk_compl": hunk_compl,
        "method_compl": method_compl,
    }


def aggregate_mod_compl_vals(complexities):
    compl_vals = [el.value for el in complexities.values()]
    compl_val = int(round(mean(compl_vals), 0))
    return ModificationComplexity(compl_val)


def overwrite_previous_assessment(mods, compl_per_mods):
    compl_per_mods_new = []
    for mod, compl_per_mod in zip(mods, compl_per_mods):

        if (mod.change_type == ModificationType.DELETE) or (
            mod.change_type == ModificationType.COPY
        ):
            compl_per_mods_new.append(ModificationComplexity.LOW)
        else:
            compl_per_mods_new.append(compl_per_mod)
    return compl_per_mods_new


#  ---- Commit Stuff ----
import hashlib


def hash_str(*args):
    string = "".join(args)
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


def persist(driller_commit, driller_mod, data):
    mod_key = hash_str(
        driller_commit.hash,
        driller_mod.change_type.name,
        driller_mod.new_path,
        driller_mod.source_code,
    )
    out_dict = {mod_key: data}
    print(out_dict)


def map_mods_to_compls(driller_commit):
    driller_mods = driller_commit.modifications
    mod_metrics = [metrics_per_mod(m) for m in driller_mods]
    dis_mod_metrics = [discretize_mod_metrics(m) for m in mod_metrics]
    compl_per_mods = [aggregate_mod_compl_vals(m) for m in dis_mod_metrics]
    # We want to map delete and copy modifications always to complexity low
    compl_per_mods = overwrite_previous_assessment(driller_mods, compl_per_mods)
    # for m, met, dmet, compl in zip(
    #     driller_mods, mod_metrics, dis_mod_metrics, compl_per_mods
    # ):
    #     persist(
    #         driller_commit,
    #         m,
    #         {
    #             "mod_metrics": met,
    #             "dis_mod_metrics": dmet,
    #             "compl_per_mods": compl,
    #         },
    #     )

    return compl_per_mods


def metrics_per_commit(commit):
    no_modified_files = commit.files
    no_lines = commit.lines
    # no_added_per_commit = commit.insertions
    # no_removed_per_commit = commit.deletions
    mod_kinds = [m.change_type for m in commit.modifications]
    mod_compls = map_mods_to_compls(commit)

    return {
        "no_modified_files": no_modified_files,
        "no_lines": no_lines,
        # "no_added_per_commit": no_added_per_commit,
        # "no_removed_per_commit": no_removed_per_commit,
        "mod_kinds": mod_kinds,
        "mod_compls": mod_compls,
    }


def compute_commit_metrics(driller_commits):
    no_mod_files = no_lines = no_added = no_removed = 0
    mod_kinds = []
    mod_compls = []
    for commit in driller_commits:
        com_metrics = metrics_per_commit(commit)

        no_mod_files += com_metrics["no_modified_files"]
        no_lines += com_metrics["no_lines"]
        # no_added += com_metrics["no_added_per_commit"]
        # no_removed += com_metrics["no_removed_per_commit"]
        mod_kinds += com_metrics["mod_kinds"]
        mod_compls += com_metrics["mod_compls"]

    if no_mod_files == 0:
        # That should never happen... But it might in case the commits are not
        # reachable, e.g., checked out an earlier version.
        changed_l_per_f = 0
    else:
        changed_l_per_f = no_lines / no_mod_files
    mod_kind_freqs = dict(Counter(mod_kinds))
    no_mod_types = len(mod_kind_freqs.keys())
    mods_compl_freqs = dict(Counter(mod_compls))

    return {
        "no_modified_files": no_mod_files,
        "changed_l_per_f": changed_l_per_f,
        "no_mod_types": no_mod_types,
        "mods_compl_freqs": mods_compl_freqs,
    }


def to_commit_compl(val, model):
    for idx, (low, up) in enumerate(model):
        if low < val <= up:
            return CommitComplexity(idx + 1)


def weigh_modifications(mod_freqs):
    wsum = 0
    for name in ModificationComplexity:
        freq = mod_freqs.get(name, 0)
        w = MOD_COMPL_WEIGHTS[name]
        wsum += freq * w
    return wsum


def discretize_commit_metrics(metrics):
    mod_files_compl = to_commit_compl(metrics["no_modified_files"], FILE_MODEL)
    lines_mod_compl = to_commit_compl(metrics["changed_l_per_f"], LINE_MODEL)
    mod_kind_compl = to_commit_compl(
        metrics["no_mod_types"], MODIFICATION_KIND_MODEL
    )
    mods_compl_freqs_weighed = weigh_modifications(metrics["mods_compl_freqs"])
    mod_compl = to_commit_compl(mods_compl_freqs_weighed, MODIFICATION_MODEL)
    return {
        "mod_files_compl": mod_files_compl,
        "lines_mod_compl": lines_mod_compl,
        "mod_kind_compl": mod_kind_compl,
        "mod_compl": mod_compl,
    }


#  ---- Contribution Stuff ----


def aggregate_final_complexity_vals(complexities):
    compl_vals = [el.value for el in complexities.values()]
    compl_val = int(round(mean(compl_vals), 0))
    return ContributionComplexity(compl_val)


#  ---- Main ----

# path_to_repo = "/tmp/gaffer"
# commit_shas = ["ee3e2a78e21fcaf206126179f82918e9161054e5"]
# data = collect_data(path_to_repo, commit_shas)
# assert len(data) == 1975
def collect_data(path_to_repo, commit_shas):
    rm = RepositoryMining(path_to_repo, only_commits=commit_shas)
    commits = []
    modifications = []
    for commit in rm.traverse_commits():
        commits.append(commit)
        for mod in commit.modifications:
            modifications.append((commit, mod))

    return commits, modifications


def compute_contrib_compl(path_to_repo, commit_shas):
    driller_commits, data = collect_data(path_to_repo, commit_shas)
    # _, driller_mods = zip(*data)

    # mod_metrics = [metrics_per_mod(m) for m in driller_mods]
    # dis_mod_metrics = [discretize_mod_metrics(m) for m in mod_metrics]
    # compl_per_mods = [aggregate_mod_compl_vals(m) for m in dis_mod_metrics]
    # # We want to map delete and copy modifications always to complexity low
    # compl_per_mods = overwrite_previous_assessment(driller_mods, compl_per_mods)

    commit_metrics = compute_commit_metrics(driller_commits)
    dis_commit_metrics = discretize_commit_metrics(commit_metrics)
    contrib_compl = aggregate_final_complexity_vals(dis_commit_metrics)

    return contrib_compl
