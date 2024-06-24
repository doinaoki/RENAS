import argparse
from logging import INFO, Formatter, StreamHandler, getLogger

from renas.evaluation.util.common import create_corename_set, set_goldset

_logger = getLogger(__name__)

similarity_list = []


def setArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source", help="set directory containing repositories to be analyzed"
    )
    args = parser.parse_args()
    return args


def setLogger(level):
    _logger.setLevel(level)
    root_logger = getLogger()
    handler = StreamHandler()
    handler.setLevel(level)
    formatter = Formatter("[%(asctime)s] %(name)s -- %(levelname)s : %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(INFO)
    return root_logger


def __set_similarity(goldset_info, id_list):
    for num1 in range(len(id_list)):
        for num2 in range(num1 + 1, len(id_list)):
            name1 = goldset_info[id_list[num1]]["normalized"]
            name2 = goldset_info[id_list[num2]]["normalized"]
            similarity = __calc_similarity(name1, name2)
            similarity_list.append(similarity)


def __calc_similarity(aNormalize, bNormalize):
    similarity = (
        len(set(aNormalize) & set(bNormalize)) * 2 / (len(aNormalize) + len(bNormalize))
    )
    return similarity


def __research(goldset_info):
    corename_sets = create_corename_set(goldset_info)
    for id_list in corename_sets.values():
        __set_similarity(goldset_info, id_list)
    return


def main(root):
    goldset_info = set_goldset(root, "recommend.json.gz")
    for commit in goldset_info.keys():
        __research(goldset_info[commit])

    return similarity_list


if __name__ == "__main__":
    args = setArgument()
    setLogger(INFO)
    main(args.source)
