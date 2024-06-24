import argparse
import os
import pathlib
import subprocess
import traceback
from logging import INFO, Formatter, StreamHandler, getLogger

import pandas as pd

LOGGER = getLogger(__name__)


def set_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source", help="set directory containing repositories to be analyzed"
    )
    args = parser.parse_args()
    return args


def set_logger(level):
    LOGGER.setLevel(level)
    root_logger = getLogger()
    handler = StreamHandler()
    handler.setLevel(level)
    formatter = Formatter("[%(asctime)s] %(name)s -- %(levelname)s : %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(INFO)
    return root_logger


def filter_data(data):
    LOGGER.info("filter data")
    commits = data.groupby("commit").size()
    commits = commits[commits > 1]
    LOGGER.info(f"total {commits.sum()} renames")
    LOGGER.info(f"pick {len(commits)} commits")
    return data[data["commit"].isin(commits.index)]


def git_archive(root, directory, sha1):
    try:
        LOGGER.info(f"[{os.getpid()}] {directory}: archive commit {sha1}^")
        archive_dir = directory.joinpath(sha1).joinpath("repo")
        os.makedirs(archive_dir, exist_ok=True)

        archive = [
            "git",
            f'--git-dir={root.joinpath("repo").joinpath(".git")}',
            "archive",
            f"{sha1}^",
        ]
        subprocess.run(archive, capture_output=True, check=True)
    except subprocess.CalledProcessError as cpe:
        traceback.print_exc(cpe)
        exit(1)
    return


def do_table(directory: pathlib.Path, sha1: str):
    archiveDir = directory.joinpath(sha1)
    try:
        subprocess.run(
            f"sh renas/table.sh {archiveDir}", shell=True, stdout=subprocess.PIPE
        )
    except subprocess.CalledProcessError as cpe:
        traceback.print_exc(cpe)
        exit(1)


def git_archive_wrapper(arg):
    return git_archive(*arg)


def main(root: pathlib.Path, rename_data: pd.DataFrame):
    try:
        rename_data = filter_data(rename_data)
        commits = rename_data["commit"].unique()
        out_dir = root.joinpath("archives")
        git_archive_args = [(root, out_dir, c) for c in commits]

        LOGGER.info("create archives")
        count = 0
        for i in git_archive_args:
            count += 1
            LOGGER.info(f"{count} / {len(git_archive_args)}")
            git_archive_wrapper(i)
            do_table(i[1], i[2])

        rename_data.to_json(
            root.joinpath("goldset.json.gz"),
            orient="records",
            indent=4,
            compression="gzip",
        )

    except Exception:
        LOGGER.exception("")
        pass


def read_rename_file(root: pathlib.Path):
    json_path = root.joinpath("rename.json.gz")
    if not os.path.isfile(json_path) or not os.path.exists(root.joinpath("repo")):
        LOGGER.error("repo does not exist")
        exit(1)
    rename_data = pd.read_json(json_path, orient="records", compression="gzip")
    if rename_data.empty:
        LOGGER.info("rename.json is empty")
        exit(1)
    return rename_data


if __name__ == "__main__":
    args = set_argument()
    set_logger(INFO)
    root = pathlib.Path(args.source)
    LOGGER.info(f"git archive {root}")
    rename_data = read_rename_file(root)
    main(root, rename_data)
    os.remove(root.joinpath("rename.json.gz"))
