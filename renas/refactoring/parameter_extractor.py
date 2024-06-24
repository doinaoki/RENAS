import re


class parameter_extractor:
    def __init__(self):
        self._type_exp = re.compile(r" : ")
        # id_exp: "identifier" = "variable_name" | "{public, private} method_name(argtype, args...)" | "path.to.class_name"
        # identfier から *_name 部分を取り出すために使う
        # method: re.compile(r"(?<=\s).+(?=\()") # アクセス修飾子ないパターンあったら死ぬかも
        # class, variable: re.compile(r"[^\.\)]+$") \)はmethodとの競合回避用
        self._id_exp = re.compile(r"(?<=\s).+(?=\()|[^\.\)]+$")

    def extract_location(self, data):
        rename_location = {"new": "", "old": ""}
        rename_location["old"] = data["leftSideLocations"][0]["filePath"]
        rename_location["new"] = data["rightSideLocations"][0]["filePath"]
        return rename_location

    def extract_type(self, data):
        return data["type"].split()[-1]

    def extract_rename(self, data):
        old = data["leftSideLocations"][0]["codeElement"]
        new = data["rightSideLocations"][0]["codeElement"]
        rename_str = {"new": new, "old": old}
        return self._modify_string(rename_str)

    def _modify_string(self, raw_str):
        modified_str = {}
        for key, string in raw_str.items():  # key = "old", "new"
            # typeを除外する
            splitted_str = self._type_exp.split(string)[0]
            # identifier部分の抽出
            modified_str[key] = self._id_exp.search(splitted_str).group()
        return modified_str
