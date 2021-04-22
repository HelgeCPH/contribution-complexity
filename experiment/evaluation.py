import sys
import pandas as pd


def get_issue_url(sys_name, iss_key):
    if sys_name == "cassandra":
        iss_url = f"https://issues.apache.org/jira/browse/{iss_key}"
    elif sys_name == "gaffer":
        iss_url = f"https://github.com/gchq/Gaffer/issues/{iss_key}"
    return iss_url


def get_commit_urls(sys_name, commit_shas):
    if sys_name == "cassandra":
        commit_url = "https://github.com/apache/cassandra/commit/"
    elif sys_name == "gaffer":
        commit_url = "https://github.com/gchq/Gaffer/commit/"

    commit_urls = [commit_url + commit_sha for commit_sha in commit_shas]
    return commit_urls


def sample_data(sys_name):
    df = pd.read_csv(f"data/{sys_name}_contrib_compl.csv")
    df.commit_shas = [
        eval(h.replace("\n", ",")) if type(h) == str else ""
        for h in df.commit_shas
    ]
    df = df[df.commit_shas.astype(bool)]

    df_1 = df[df.contrib_complexity == 1].sample(5)
    df_2 = df[df.contrib_complexity == 2].sample(5)
    df_3 = df[df.contrib_complexity == 3].sample(5)
    df_4 = df[df.contrib_complexity == 4].sample(5)
    if sys_name == "cassandra":
        sample_size = 5
    elif sys_name == "gaffer":
        # For Gaffer there are only 3 of these
        sample_size = 3
    df_5 = df[df.contrib_complexity == 5].sample(sample_size)

    df_i = pd.concat([df_1, df_2, df_3, df_4, df_5])
    df_i = df_i.sample(frac=1)

    df_i.to_csv(f"data/{sys_name}_eval_in.csv", index=False)
    return df_i


def main(sys_name):
    df = sample_data(sys_name)

    pd.set_option("display.max_colwidth", None)

    if sys_name == "cassandra":
        issue_key_col = "key"
    elif sys_name == "gaffer":
        issue_key_col = "number"

    df["iss_url"] = df[issue_key_col].apply(
        lambda x: get_issue_url(sys_name, x)
    )
    df["commit_urls"] = df.commit_shas.apply(
        (lambda x: "<br>".join(get_commit_urls(sys_name, x)))
    )
    df["manual_compl"] = ["_fill_" for i in range(df.shape[0])]

    cols = [issue_key_col, "iss_url", "commit_urls", "manual_compl"]
    print(df[cols].to_markdown(index=False))


if __name__ == "__main__":
    sys_name = sys.argv[1]
    main(sys_name)
