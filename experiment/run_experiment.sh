#!/usr/bin/env bash

# Download the issue tracker data to CSV files
# Dataset created on Apr. 14th 2021
python experiment/gh_issues_to_csv.py "gchq/gaffer" > data/gaffer_issues.csv
# Dataset created on Apr. 16th 2021
python experiment/jira_to_csv.py cassandra CASSANDRA > data/cassandra_issues.csv

# git clone git@github.com:gchq/Gaffer.git /tmp/gaffer
# git clone git@github.com:apache/cassandra.git /tmp/cassandra

git clone https://github.com/gchq/Gaffer.git /tmp/gaffer
git clone https://github.com/apache/cassandra.git /tmp/cassandra

# That takes a bit of time. On my computer it takes ca. 50min for Gaffer and
# ca. 12h for Cassandra
# Stores a file in data/(gaffer|cassandra)_contrib_compl.csv
python experiment/compute_contrib_compls.py gaffer > /tmp/gaf_contrib_compl.log
python experiment/compute_contrib_compls.py cassandra > /tmp/cas_contrib_compl.log

python experiment/evaluation.py gaffer > data/evaluation_tab.md
python experiment/evaluation.py cassandra > data/cas_evaluation_tab.md