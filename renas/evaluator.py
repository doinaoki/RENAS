import argparse

from renas.evaluation.preliminary import research_similarity


def setArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source", help="set directory containing repositories to be analyzed"
    )
    args = parser.parse_args()
    return args


def main(root):
    similarity_list = research_similarity.main(root)


if __name__ == "__main__":
    args = setArgument()
    root = args.source
    main(root)
