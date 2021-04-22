"""
This program collects issues from a hosted JIRA instance and converts them to
CSV. The fields that are downloaded is currently hard coded, see JIRA_COLUMNS

Usage:
  jira_to_csv <project_name> <jira_project_name>
  jira_to_csv -h | --help
  jira_to_csv --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import argparse
import os
import re
from io import StringIO
from time import sleep

import pandas as pd
import requests
from dateutil.parser import parse
from docopt import docopt


JIRA_API_BASE_URL = "https://issues.apache.org/jira/"
PAGE_LENGTH = 500

JIRA_COLUMNS = (
    "issue_type",
    "issue_component",
    "creator_name",
    "creator_display_name",
    "reporter_name",
    "reporter_display_name",
    "priority",
    "description",
    "labels",
    "created",
    "resolved",
    "updated",
    "status",
    "versions",
    "id",
    "key",
    "resolution",
)


def collect_from_jira(proj_gh_name, proj_jira_id):
    if not proj_jira_id:
        return

    # print(f"Collecting data from {proj_gh_name}...")
    sleep(5)

    rows = []
    start_idx = 0
    url = (
        JIRA_API_BASE_URL
        + f"rest/api/2/search?jql=project={proj_jira_id}+order+by+created"
        + f"&issuetypeNames=Bug&maxResults={PAGE_LENGTH}&"
        + f"startAt={start_idx}&fields=id,key,priority,labels,versions,"
        + "status,components,creator,reporter,issuetype,description,"
        + "summary,resolutiondate,created,updated,resolution"
    )

    # print(f"Getting data from {url}...")
    r = requests.get(url)
    r_dict = r.json()

    while start_idx < r_dict["total"]:
        sleep(2)

        # The above `issuetypeNames=Bug` should limit the response to bugs
        # only but the response for `WW` contains more issue types. So I
        # have to filter later ...
        for idx in range(len(r_dict["issues"])):
            fields = r_dict["issues"][idx]["fields"]

            # fields["issuetype"]["description"]
            issue_type = fields["issuetype"]["name"]

            issue_component = [
                c["name"] for c in fields["issuetype"].get("components", [])
            ]
            creator = fields["creator"]
            if creator:
                creator_name = creator.get("name", None)
                creator_display_name = creator.get("displayName", None)
            else:
                creator_name = None
                creator_display_name = None

            reporter = fields["reporter"]
            if reporter:
                reporter_name = reporter.get("name", None)
                reporter_display_name = reporter.get("displayName", None)
            else:
                reporter_name = None
                reporter_display_name = None

            priority = fields["priority"]
            if priority:
                priority = priority.get("name", None)

            description = fields["description"]
            labels = fields["labels"]

            created = fields["created"]
            if created:
                created = parse(created)
            resolved = fields["resolutiondate"]
            if resolved:
                resolved = parse(resolved)
            updated = fields["updated"]
            if updated:
                updated = parse(updated)
            status = fields["status"]["name"]

            resolution = fields["resolution"]
            if resolution:
                resolution = resolution.get("name", None)

            try:
                version_fields = fields["versions"]
                versions_str = " ".join([v["name"] for v in version_fields])
            except KeyError:
                versions_str = ""

            id_val = r_dict["issues"][idx]["id"]
            key_val = r_dict["issues"][idx]["key"]

            rows.append(
                (
                    issue_type,
                    issue_component,
                    creator_name,
                    creator_display_name,
                    reporter_name,
                    reporter_display_name,
                    priority,
                    description,
                    labels,
                    created,
                    resolved,
                    updated,
                    status,
                    versions_str,
                    id_val,
                    key_val,
                    resolution,
                )
            )

        start_idx += PAGE_LENGTH
        url = re.sub(r"startAt=\d+&", f"startAt={start_idx}&", url)
        inner_idx = start_idx + PAGE_LENGTH
        # print(f"Getting data for index {start_idx} to {inner_idx}...")
        r = requests.get(url)
        r_dict = r.json()

    # print(f"Writing {fname} for {proj_gh_name}...")
    df = pd.DataFrame(rows, columns=JIRA_COLUMNS)
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    print(output.read())


def run():
    arguments = docopt(__doc__, version="0.1")
    proj_gh_name = arguments["<project_name>"]
    proj_jira_id = arguments["<jira_project_name>"]

    collect_from_jira(proj_gh_name, proj_jira_id)


if __name__ == "__main__":
    run()
