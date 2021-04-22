# import pandas as pd
# from pydriller import RepositoryMining, ModificationType
# from contribution_complexity.metrics import stats_per_modification


# path_to_repo = "/tmp/gaffer/"
# rm = RepositoryMining(path_to_repo)
# mods = [m for c in rm.traverse_commits() for m in c.modifications]


# stats_per_mod_dicts = [stats_per_modification(m) for m in mods]
# stats_per_mod = [tuple(stats_per_modification(m).values()) for m in mods]
# cols = [
#     "no_lines_added",
#     "no_lines_removed",
#     "no_changes",
#     "churn",
#     "no_hunks",
#     "no_methods_changed",
#     "no_total_methods",
#     "method_change_ratio",
# ]
# mods_df = pd.DataFrame(stats_per_mod, columns=cols)
# mods_df.to_csv("data/model_cal_gaf.csv", index=False)

# .quantile(0.05)
# .quantile(0.35)
# .quantile(0.65)
# .quantile(0.95)


# stats_per_mod = [tuple(s()) for s in stats_per_mod]
515
558
674
1997
560
1962
396
1316
1050
2000
1076
1264


import pickle
import pandas as pd
from contribution_complexity.metrics import compute_metrics


def get_commit_urls(sys_name):
    issues_to_commit_file = f"/Users/ropf/Documents/workspace/Python/is_td_real/data/processing/{sys_name}_issues_to_commits.csv"
    issues_to_commit_df = pd.read_csv(issues_to_commit_file)

    # Filter only those issues where there are commits associated
    q = ~issues_to_commit_df.hashes.isnull()
    issues_to_commit_df = issues_to_commit_df[q]

    issues_to_commit_df.hashes = [
        eval(h.replace("\n", ",")) if type(h) == str else ""
        for h in issues_to_commit_df.hashes
    ]

    return issues_to_commit_df[["key", "hashes"]]


df = get_commit_urls("gaffer")
path_to_repo = "/tmp/gaffer"
results_dict = {}

for idx, (iss_key, hashes) in df[120:].iterrows():
    print(f"https://github.com/gchq/Gaffer/issues/{iss_key}")
    results = compute_metrics(path_to_repo, hashes)
    print(results)
    results_dict[iss_key] = results


with open("data/metrics.pkl", "wb") as fp:
    pickle.dump(results_dict, fp)


with open("data/metrics.pkl", "rb") as fp:
    results_dict = pickle.load(fp)
