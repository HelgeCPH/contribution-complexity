import sys
import numpy as np
import pandas as pd
from contribution_complexity.compute import find_commits_for_issue
from contribution_complexity.metrics import compute_contrib_compl


def main(sys_name):

    df = pd.read_csv(f"data/{sys_name}_issues.csv")

    if sys_name == "cassandra":
        closed_col = "resolved"
        issue_key_col = "key"
    elif sys_name == "gaffer":
        closed_col = "closed_at"
        issue_key_col = "number"

    # Filter for only resolved issues: 2300 closed issues for Gaffer and
    # 14158 closed issues for Cassandra
    df = df[~df[closed_col].isnull()]
    df.reset_index(drop=True, inplace=True)

    # df = df.iloc[:10]

    path_to_repo = f"/tmp/{sys_name}"
    contribcompls = []
    commit_shas_per_contrib = []

    for issue_key in df[issue_key_col].values:
        if sys_name == "cassandra":
            issue_re = f"{issue_key}( |$)"
        elif sys_name == "gaffer":
            issue_re = f"(Gh |gh-){issue_key}( |$)"

        commit_shas = find_commits_for_issue(path_to_repo, issue_re)
        commit_shas_per_contrib.append(commit_shas)
        print(issue_re, commit_shas, flush=True)

        if commit_shas:
            try:
                contribcompl = compute_contrib_compl(path_to_repo, commit_shas)
            except:
                print(
                    f"Skipping {issue_key}",
                    issue_re,
                    commit_shas,
                    type(commit_shas),
                    flush=True,
                )
                contribcompl = None
            contribcompl = contribcompl.value
        else:
            contribcompl = None
        contribcompls.append(contribcompl)

    df["commit_shas"] = commit_shas_per_contrib
    df["contrib_complexity"] = contribcompls

    # Prevent sha lists from being truncated
    np.set_printoptions(threshold=sys.maxsize)
    df.to_csv(f"data/{sys_name}_contrib_compl.csv", index=False)


if __name__ == "__main__":
    sys_name = sys.argv[1]
    main(sys_name)
