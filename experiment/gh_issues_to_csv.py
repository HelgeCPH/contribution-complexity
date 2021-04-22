import os
import sys
import pandas as pd
from io import StringIO
from github import Github


def run():
    g = Github(os.environ["GITHUB_API_KEY"])
    repo = g.get_repo(sys.argv[1])  # "gchq/gaffer"
    issues = [issue for issue in repo.get_issues(state="all")]

    lines = []
    for i in issues:
        line = (
            i.title,
            i.body,
            i.created_at,
            i.updated_at,
            i.closed_at,
            i.state,
            i.labels,
            i.number,
            i.html_url,
            i.milestone,
            i.locked,
            i.assignee,
            i.assignees,
        )
        lines.append(line)

    df = pd.DataFrame(
        lines,
        columns=(
            "title",
            "body",
            "created_at",
            "updated_at",
            "closed_at",
            "state",
            "labels",
            "number",
            "url",
            "milestone",
            "locked",
            "assignee",
            "assignees",
        ),
    )
    df.created_at = pd.to_datetime(df.created_at, utc=True)
    df.updated_at = pd.to_datetime(df.updated_at, utc=True)
    df.closed_at = pd.to_datetime(df.closed_at, utc=True)

    # find the oldest open issue:
    # df[df.state == "open"].sort_values("created_at").url

    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    print(output.read())


if __name__ == "__main__":
    run()
