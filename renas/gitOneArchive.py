import pathlib
import os
import sys
import glob
import time
import json
import datetime
import traceback
import subprocess
import argparse
from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, log
import re

import pandas as pd
from .util.Name import KgExpanderSplitter
from .util.Rename import Rename

LOGGER = getLogger(__name__)
ENGLISH_DIC = []
WORD_CACHE = {}
# SPLITTER = KgExpanderSplitter()
gitRe = re.compile(r'(?:^commit)\s+(.+)\nAuthor:\s+(.+)\nDate:\s+(.+)\n', re.MULTILINE)
COMMIT = set()

def setArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='set directory containing repositories to be analyzed')
    parser.add_argument('-D', help='dry run (only check how many archives will be created)', action='store_true', default=False)
    parser.add_argument('-f', help='force', action='store_true', default=False)
    parser.add_argument('-n', help='commit filter', action='store_true', default=False)
    args = parser.parse_args()
    return args

def setGitlog(path):
    repoPath = os.path.join(path, "repo")
    cp = subprocess.run(f"cd {repoPath}; git log",shell=True, stdout=subprocess.PIPE)
    gitLog = cp.stdout.decode('utf-8','ignore')
    gitInfo = gitRe.findall(gitLog)
    for info in gitInfo:
        commit = info[0]
        author = info[1]
        data = info[2]
        COMMIT.add(commit)
    return

def setLogger(level):
    LOGGER.setLevel(level)
    root_logger = getLogger()
    handler = StreamHandler()
    handler.setLevel(level)
    formatter = Formatter('[%(asctime)s] %(name)s -- %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(INFO)
    return root_logger

def setDictionary(dicPath):
    LOGGER.info('set dictionary')
    with open(dicPath) as dic:
        [ENGLISH_DIC.append(word.rstrip()) for word in dic if len(word) > 1]

def filterData(data, isN):
    LOGGER.info('filter data')
    filter = map(__containAbbr, data['oldname'], data['newname'])
    filtered = data[pd.Series(filter)]
    commits = filtered.groupby('commit').size()
    if isN:
        commits = commits[commits > 3]
    else:
        commits = commits[commits > 1]
    #LOGGER.info(f'{len(commits)} commits may contain abbreviation rename')
    LOGGER.info(f'total {commits.sum()} renames')
    #commits = commits.sample(frac=0.1, random_state=0)
    LOGGER.info(f'pick {len(commits)} commits')
    LOGGER.info(f'pick {(commits.sum())} renames')
    return data[data['commit'].isin(commits.index)]

def __containAbbr(oldName, newName):
    return True

def gitArchive(root, directory, sha1):
    try:
        LOGGER.info(f'[{os.getpid()}] {directory}: archive commit {sha1}^')
        archiveDir = directory.joinpath(sha1).joinpath('repo')
        os.makedirs(archiveDir, exist_ok=True)

        archive = ["git",
                f'--git-dir={root.joinpath("repo").joinpath(".git")}',
                "archive",
                f'{sha1}^']
        extract = ['tar', '-xf', '-', '-C', archiveDir]
        p1 = subprocess.run(archive, capture_output=True, check=True)
        p2 = subprocess.run(extract, input=p1.stdout, check=True)
    except:
        traceback.print_exc()
        exit(1)
    return

def doTable(root, directory, sha1):
    try:
        archiveDir = directory.joinpath(sha1)
        cp = subprocess.run(f'sh renas/table.sh {archiveDir}', shell=True, stdout=subprocess.PIPE)
    except:
        traceback.print_exc()
        exit(1)

def gitArchiveWrapper(arg):
    return gitArchive(*arg)

if __name__ == "__main__":
    args = setArgument()
    setLogger(INFO)

    englishDicPath = pathlib.Path('AbbrExpansion/code/SemanticExpand/dic/EnglishDic.txt')
    setDictionary(englishDicPath)

    abbrCommits = 0
    root = pathlib.Path(args.source)

    LOGGER.info(f'git archive {root}')
    setGitlog(root)
    jsonPath = root.joinpath('rename.json')
    if not os.path.isfile(jsonPath) or not os.path.exists(root.joinpath('repo')):
        LOGGER.error(f'repo does not exist')
        exit(1)
    # TODO: add filter
    try:
        data = pd.read_json(jsonPath, orient='records')
        if data.empty:
            LOGGER.info('rename.json is empty')
            exit(1)
        data = filterData(data, args.n)
        commits = data['commit'].unique()
        abbrCommits += len(commits)

        outDir = root.joinpath('archives')
        gitArchiveArgs = [(root, outDir, c) for c in commits if c in COMMIT]
        if args.D:
            LOGGER.info('dry run')
        else:
            LOGGER.info('create archives')
            count = 0
            for i in gitArchiveArgs:
                count+=1
                LOGGER.info(f'{count} / {len(gitArchiveArgs)}')
                gitArchiveWrapper(i)
                doTable(i[0], i[1], i[2])

            data.to_json(root.joinpath('goldset.json'), orient='records', indent=4)
    except Exception:
        LOGGER.exception('')
        pass
    # LOGGER.info(f'{abbrCommits} commits may contain abbreviation rename')
