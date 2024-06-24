import argparse
import os
import pathlib

import pandas as pd

from renas.refactoring import refactoringminer, rename_extractor
from renas.relationship import analyzer


def set_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source", help="set directory containing repositories to be analyzed"
    )
    args = parser.parse_args()
    return args


def main(root):
    refactoring_dict = refactoringminer.main(root)
    refactoring_data = pd.DataFrame.from_records(refactoring_dict["commits"])
    print(refactoring_data)
    rename_data = rename_extractor.main(root, refactoring_data)
    print(rename_data)
    dump(root, rename_data)
    analyzer.main(root, rename_data)


def dump(root, data: pd.DataFrame):
    out_file_path = os.path.join(root, "temp.json")
    data.to_json(out_file_path, orient="records", indent=4)


if __name__ == "__main__":
    args = set_argument()
    root = pathlib.Path(args.source)
    main(root)
