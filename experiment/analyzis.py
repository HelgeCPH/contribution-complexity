import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress


# from contribution_complexity.compute import find_commits_for_issue
# from contribution_complexity.metrics import compute_contrib_compl


# df_w[df_w.contrib_complexity == 1]  # 291
# df_w[df_w.contrib_complexity == 2]  # 363
# df_w[df_w.contrib_complexity == 3]  #  91
# df_w[df_w.contrib_complexity == 4]  #  72
# df_w[df_w.contrib_complexity == 5]  #   3


# df_w.created_at.dt.week

# df_w.created_at.dt.year.astype(str) + df_w.created_at.dt.month.astype(str)


# (
#     df_w.created_at.dt.year.astype(str) + df_w.created_at.dt.month.astype(str)
# ).groupby()


# df_w.created_at.dt.strftime("%M-%Y")


def compute_lin_reg(df, x_col, y_col):
    y = df[y_col]
    x = pd.to_numeric(df[x_col])
    slope, intercept, _, _, _ = linregress(x, y)

    xf = np.linspace(x.min(), x.max(), 2)
    yf = slope * xf + intercept
    xf_dates = pd.to_datetime(xf)

    return slope, intercept, xf_dates, yf


def plot_data_w_lin_reg(df, x_col, y_col, out_file, connect=False, rot=None):
    fig, axs = plt.subplots()

    df.plot.scatter(x=x_col, y=y_col, s=1, ax=axs, rot=rot)

    axs.set_ylabel("Contribution Complexity")
    axs.set_xlabel("Resolved Date")

    slope, intercept, xf_dates, yf = compute_lin_reg(df, x_col, y_col)
    axs.plot(xf_dates, yf, c="orange")

    axs.set_yticks(list(range(1, 6)))
    axs.set_yticklabels(
        ["low", "moderate", "medium", "elevate", "high"], rotation=45
    )

    fig.tight_layout()
    return fig, slope


def main(sys_name):
    if sys_name == "cassandra":
        date_cols = ["created", "resolved", "updated"]
        issue_key_col = "key"
    elif sys_name == "gaffer":
        issue_key_col = "number"
        date_cols = ["created_at", "closed_at", "updated_at"]
    closed_col = date_cols[1]

    # Gaffer Analyzis
    df = pd.read_csv(
        f"data/{sys_name}_contrib_compl.csv", parse_dates=date_cols
    )

    # parse commits again in
    df.commit_shas = [
        eval(h.replace("\n", ",")) if type(h) == str else ""
        for h in df.commit_shas
    ]

    # Filter for only resolved issues
    df = df[~df[closed_col].isnull()]

    # Those contributions wit at least one commit.
    # Empty lists evaluate to False, leaving only non-empty lists for query
    # df_w .. "w" stands for work here
    # 820 issues with commits in Gaffer and 7866 in Cassandra
    df_w = df[df.commit_shas.astype(bool)]

    fig, slope = plot_data_w_lin_reg(
        df_w,
        x_col=closed_col,
        y_col="contrib_complexity",
        out_file="out_file",
        connect=False,
        rot=45,
    )
    fig.savefig(f"paper/images/{sys_name}_iss_compls.png", bbox_inches="tight")

    # df_w["closed_month"] = df_w[closed_col].dt.strftime("%m-%Y")

    # groups = df_w.groupby("closed_month")

    # closed_month_mean = []
    # for name, group in groups:
    #     closed_month_mean.append(
    #         (name, int(group.contrib_complexity.mean().round()))
    #     )
    # closed_month_mean_df = pd.DataFrame(
    #     closed_month_mean, columns=["closed_month", "contrib_complexity"]
    # )
    # closed_month_mean_df["closed_month_date"] = pd.to_datetime(
    #     closed_month_mean_df.closed_month
    # )
    # closed_month_mean_df.sort_values("closed_month_date", inplace=True)

    # fig, slope = plot_data_w_lin_reg(
    #     closed_month_mean_df,
    #     x_col="closed_month_date",
    #     y_col="contrib_complexity",
    #     out_file="out_file",
    #     connect=False,
    #     rot=45,
    # )
    # fig.savefig(
    #     f"paper/images/{sys_name}_iss_compls_m.png", bbox_inches="tight"
    # )


# for name, group in groups:
#     if name == "08-2016":
#         print(name)
#         print(group)
#         print("\n")
#         break


if __name__ == "__main__":
    sys_name = sys.argv[1]
    main(sys_name)
