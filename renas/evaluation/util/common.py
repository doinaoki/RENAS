import gzip
import json
import os


def __is_meaningful(operations):
    meaningful = ["insert", "delete", "replace"]
    for op in operations:
        if op[0] in meaningful:
            return True
        if op[0] == "format" and op[1][0] == "Plural":
            return True
    return False


def create_corename_set(goldset_info):
    corename_sets = {}
    for id, ginfo in goldset_info.items():
        operations = ginfo["operation"]
        if not __is_meaningful(operations):
            continue
        for op in operations:
            key = str(op)
            if key not in corename_sets:
                corename_sets[key] = []
            corename_sets[key].append(id)
    return corename_sets


def set_goldset(path, fileName):
    filePath = os.path.join(path, fileName)
    if not os.path.isfile(filePath):
        print("error: file is not found")
        exit(1)

    with gzip.open(filePath, "r") as f:
        renames = json.load(f)

    goldset_info = {}
    for commit in renames.keys():
        goldset_info[commit] = {}
        for ginfo in renames[commit]["goldset"]:
            if ginfo["id"] != []:
                goldset_info[commit][ginfo["id"]] = ginfo
    return goldset_info
