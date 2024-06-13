import pathlib
import os
import sys
import glob
import time
import json
import re
import traceback
import csv
import subprocess
import argparse
from multiprocessing import Pool
from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, log
import operator
from copy import deepcopy

from .util.ExTable import ExTable
from datetime import datetime, date, timedelta
import pandas as pd
from .util.Name import KgExpanderSplitter
from .util.Rename import Rename
import statistics
from .showRQFigure import showRQFigure

_logger = getLogger(__name__)

devideNumber = 20
thresholdNumber = 100.0
researchFileNames = {
                    "recommend_none.json": "None",
                    "recommend_relation_normalize.json": "Normalize",
                    "recommend_relation.json": "Relation",
                    "recommend_all_normalize.json": "All"}
detail_info = [['triggerCommit', 'file', 'line', 'triggeroldname', 'triggernewname', 'op',
                'commitPool', 'researchCommit', 'file', 'line', 'oldname' ,'truename', 'recommendname']]

result_info = []
allPrecision = {op: [] for op in researchFileNames.values()}
allRecall = {op: [] for op in researchFileNames.values()}
allFscore = {op: [] for op in researchFileNames.values()}
TOPN = 40
RANK = 50
rankTrueRecommend = [[0, 0] for _ in range(RANK)]

gitRe = re.compile(r'(?:^commit)\s+(.+)\nAuthor:\s+(.+)\nDate:\s+(.+)\n', re.MULTILINE)
numberToCommit = {}
dateToCommit = {}
commitToNumber = {}
commitToDate = {}
motivationExample = {"Normalize":{}, "All":{}, "Relation":{}, "None":{}}


missOperation = {op: {"insert": [0, 0, 0], "delete": [0, 0, 0], "replace": [0, 0, 0], "order": [0, 0, 0], "format": [0, 0, 0], "changeCase": [0, 0, 0], "changePattern": [0, 0, 0]} for op in researchFileNames.values()}
_showRQFigure = showRQFigure(TOPN, RANK)

def setArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='set directory containing repositories to be analyzed')
    parser.add_argument('-D', help='dry run (only check how many archives will be created)', action='store_true', default=False)
    args = parser.parse_args()
    return args


def setLogger(level):
    _logger.setLevel(level)
    root_logger = getLogger()
    handler = StreamHandler()
    handler.setLevel(level)
    formatter = Formatter('[%(asctime)s] %(name)s -- %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(INFO)
    return root_logger


def setGitlog(path):
    repoPath = os.path.join(path, "repo")
    cp = subprocess.run(f"cd {repoPath}; git log",shell=True, stdout=subprocess.PIPE)
    gitLog = cp.stdout.decode('utf-8','ignore')
    gitInfo = gitRe.findall(gitLog)
    num = len(gitInfo)-1
    for info in gitInfo:
        commit = info[0]
        author = info[1]
        dateInfo = datetime.strptime(info[2], '%a %b %d %H:%M:%S %Y %z')
        commitToDate[commit] = dateInfo
        dateToCommit[dateInfo]= commit

        numberToCommit[num] = commit
        commitToNumber[commit] = num
        num -= 1
    
    return True


def setRename(path, fileName):
    filePath = os.path.join(path, fileName)
    if not os.path.isfile(filePath):
        return False

    with open(filePath, 'r') as f:
        renames = json.load(f)

    recommendName = {}
    renameInfo = {}
    for commit in renames.keys():
        renameInfo[commit] = renames[commit]["goldset"]
        for i in range(len(renames[commit]["goldset"])):
            recs = renames[commit][str(i)]
            trigger = renames[commit]["goldset"][i]
            triggerKey = getKey(trigger)
            recommendName[triggerKey] = recs

    return recommendName, renameInfo


def setOperations(path, op):
    filePath = os.path.join(path, "operations.json")
    operations = {}
    with open(filePath, 'r') as f:
        ops = json.load(f)[op]
    for commit, gold in ops.items():
        operations[commit] = {}
        for k, o in gold.items():
            key = re.sub(r'MethodName$|ClassName$|ParameterName$|VariableName$|FieldName$', '', k)
            operations[commit][key] = o
    return operations


def getCommitsInfo(commit):
    researchCommits = []
    researchCommits.append(commit)
    return researchCommits

def getKey(dic):
    return dic["commit"] + dic["files"] + str(dic["line"]) + dic["oldname"]

def checkMeaningful(operations):
    meaningful = ["insert", "delete", "replace"]
    for op in operations:
        if op[0] in meaningful:
            return False
        if op[0] == "format":
            if op[1][0] == "Plural":
                return False
    print(operations)
    return True

def recommendCommit(commit, tableData, operations, recommendName, renameInfo, opIds):
    #調査体操となる複数コミットを取得
    researchCommits = getCommitsInfo(commit)
    opGroup = {}
    detail_info.append(["start"])

    #operationごとにdicを作成する
    for c in researchCommits:
        if c not in renameInfo:
            continue
        #print(commit)
        goldset = renameInfo[c]
        for rDic in goldset:
            key = getKey(rDic)
            #Todo: fix extracting parameter or variable using AST
            if key not in operations[c]:
                print(f"something wrong with {key}")
                exit(1)
                continue
            ops = operations[c][key]
            for op in ops:
                #must change
                if str(op) not in opGroup:
                    opGroup[str(op)] = []
                opGroup[str(op)].append(rDic)
    
    allRenames = 0
    allRecommend = 0
    allTrueRec = 0

    #調査するcommitからtriggerを選ぶ
    for trigger in renameInfo[commit]:
        # triggerを元にoperaion dicからrename情報を得る
        triggerKey = getKey(trigger)
        if triggerKey not in operations[commit]:
            print(f"something wrong {triggerKey}")

            continue
        triggerOp = operations[commit][triggerKey]
        triggerRec = recommendName[triggerKey]
        if checkMeaningful(triggerOp):
            continue
        renames = []
        rKeys = []
        for op in triggerOp:
            if str(op) not in opGroup:
                continue
            for rDic in opGroup[str(op)]:
                if getKey(rDic) == triggerKey:
                    continue
                if getKey(rDic) in rKeys:
                    continue
                rKeys.append(getKey(rDic))
                renames.append(rDic)
        if opIds == "All" :
            triggerRec = deepcopy(triggerRec)
            for tr in triggerRec:
                relationshipCost = (1.0 / tr["relationship"])
                similarityCost = 1.0 - tr["similarity"]
                tr["rank"] = (0.5 * similarityCost + (1.0 - 0.5) * relationshipCost) * thresholdNumber
            triggerRec = sorted(triggerRec, key=operator.itemgetter('rank', 'id'), reverse=True)
        if opIds == "Normalize":
            triggerRec = sorted(triggerRec, key=operator.itemgetter('rank', 'id'))
        if len(renames) < 1:
            #print(triggerOp)
            print("one rename is conducted")
            trueRecommendIndex = []
            precision = 0
            recall = 0
            exacts = 0
            fscore = 0
            continue
        elif len(triggerRec) == 0:
            print("No recommend")
            trueRecommendIndex = []
            precision = 0
            recall = 0
            exacts = 0
            fscore = 0
        else:
            #rename情報とrecommend情報を基に評価
            #print(len(renames), len(triggerRec))
            trueRecommendIndex = evaluate(renames, triggerRec, tableData, opIds)
            trueRecommendCount = len(trueRecommendIndex)
            exactMatch = getExactMatch(renames, triggerRec, trueRecommendIndex)
            exactMatchCount = len(exactMatch)
            recommendationCount = len(triggerRec)
            renameCount = len(renames)

            precision = trueRecommendCount / recommendationCount 
            recall = trueRecommendCount / renameCount
            exacts = exactMatchCount / trueRecommendCount if trueRecommendCount != 0 else 0
            fscore = calcFScore(precision, recall)

        allRenames += len(renames)
        allRecommend += len(triggerRec)
        allTrueRec += len(trueRecommendIndex)
        allPrecision[opIds].append(precision)
        allRecall[opIds].append(recall)
        allFscore[opIds].append(fscore)
        #addRankRecommend(triggerRec, opIds)
        if opIds == "All" or opIds == "Normalize":
            setMissOperation(opIds, triggerOp, len(renames), len(triggerRec), len(trueRecommendIndex))
            setDetail(commit, trigger, triggerOp, triggerRec, renames, tableData, opIds)
        print(f"operation chunk = {triggerOp}")
        print(f"precision = {precision},  recall = {recall},\
               exact = {exacts}, fscore = {fscore} ")
        _showRQFigure.update(trigger, triggerRec, renames, trueRecommendIndex, opIds)
    
    if opIds in motivationExample:
        motivationExample[opIds][commit] = allTrueRec
    detail_info.append([commit, "allRenames", allRenames, "allRecommend", allRecommend,
                        "allTrueRecommend", allTrueRec, "precision", allTrueRec/allRecommend if allRecommend != 0 else 0,
                         "recall", allTrueRec/allRenames if allRenames != 0 else 0])
    result_info.append([commit, "allRenames", allRenames, "allRecommend", allRecommend,
                        "allTrueRecommend", allTrueRec, "precision", allTrueRec/allRecommend if allRecommend != 0 else 0,
                         "recall", allTrueRec/allRenames if allRenames != 0 else 0])
    return allRenames, allRecommend, allTrueRec

def setMissOperation(opId, setOp, reNum, trigNum, trueNum):

    for op in setOp:
        operation = op[0]
        a, b, c = missOperation[opId][operation]
        missOperation[opId][operation] = [a + reNum, b + trigNum, c + trueNum]

def addRankRecommend(recommendations, op):
    for rec in recommendations:
        if op == "All":
            rankTrueRecommend[rec["rank"]-1][1] += 1


def setDetail(commit, trigger, triggerOp, triggerRec, renames, tableData, op):
    commitPool = [commit]
    for r in renames:
        if r["commit"] not in commitPool:
            commitPool.append(r["commit"])

    trueRecommendIndex = []
    for i in range(len(renames)):
        r = renames[i]
        key = str([r["line"], r["typeOfIdentifier"], r["oldname"], r["files"]])
        flag = False
        for k in range(len(triggerRec)):
            rec = triggerRec[k]
            recKey = str([rec["line"], rec["typeOfIdentifier"], rec["name"], rec["files"]])
            if key == recKey:
                trueRecommendIndex.append([i, k])
                flag = True
                break

    for t in trueRecommendIndex:
        detail = [commit, trigger["files"], trigger["line"], trigger["typeOfIdentifier"], trigger["oldname"], trigger["newname"],
                    str(triggerOp), commitPool, renames[t[0]]["commit"], renames[t[0]]["files"], str(renames[t[0]]["line"]), 
                    renames[t[0]]["typeOfIdentifier"], renames[t[0]]["oldname"], renames[t[0]]["newname"], triggerRec[t[1]]["join"], triggerRec[t[1]]["rank"]]
        detail_info.append(detail)

    for t in range(len(renames)):
        flag = True
        for v in trueRecommendIndex:
            if t == v[0]:
                flag = False
        if flag:
            detail = [commit, trigger["files"], trigger["line"], trigger["typeOfIdentifier"], trigger["oldname"], trigger["newname"],
                str(triggerOp), commitPool, renames[t]["commit"], renames[t]["files"], str(renames[t]["line"]), 
                renames[t]["typeOfIdentifier"], renames[t]["oldname"], renames[t]["newname"], "NaN", "NaN"]
            detail_info.append(detail)

    for t in range(len(triggerRec)):
        flag = True
        for v in trueRecommendIndex:
            if t == v[1]:
                flag = False
        if flag:
            detail = [commit, trigger["files"], trigger["line"], trigger["typeOfIdentifier"], trigger["oldname"], trigger["newname"],
                str(triggerOp), commitPool, commit, triggerRec[t]["files"], str(triggerRec[t]["line"]), 
                triggerRec[t]["typeOfIdentifier"],triggerRec[t]["name"], "NaN", triggerRec[t]["join"] , triggerRec[t]["rank"]]
            detail_info.append(detail)


def calcFScore(precision, recall):
    if precision == 0 or recall == 0:
        return 0
    else:
        return 2 * precision * recall / (precision + recall)

def getExactMatch(renames, recommendation, indexes):
    result = []
    for idx in indexes:
        trueNewName = renames[idx[0]]['newname']
        recommendNewName = recommendation[idx[1]]['join']
        if trueNewName == recommendNewName:
            result.append(idx)
    #_logger.debug(f'exact matches: {result}')
    return result

def getRelationData(renameData, relation):
    if not isinstance(renameData[relation], str):
        return []
    return renameData[relation].split(" - ")


def evaluate(renames, recommendation, tableData, op):
    if len(recommendation) == 0:
        return []
    
    trueRecommendIndex = []
    for i in range(len(renames)):
        r = renames[i]
        key = str([r["line"], r["typeOfIdentifier"], r["oldname"], r["files"]])
        #flag = False
        for k in range(len(recommendation)):
            rec = recommendation[k]
            recKey = str([rec["line"], rec["typeOfIdentifier"], rec["name"], rec["files"]])
            if key == recKey:
                trueRecommendIndex.append([i, k])
                break

    return trueRecommendIndex

def writeMissOperation(missCSV):
    with open(missCSV, 'w') as wCSV:
        w = csv.writer(wCSV)
        for op, missDic in missOperation.items():
            w.writerow([op])
            for operation, nums in missDic.items():
                w.writerow([operation]+nums)



if __name__ ==  "__main__":
    args = setArgument()
    setLogger(INFO)
    setGitlog(args.source)
    detailCSV = os.path.join(args.source,'integrateDetail.csv')  ##
    resultCSV = os.path.join(args.source,'integrateResult.csv') 
    missCSV = os.path.join(args.source,'missOperation.csv') 
    mecCSV = os.path.join(args.source,'motivationExampleCandidate.csv') 
    allCSV = os.path.join(args.source,'all.csv') 

    #すべてのjson Fileを読み込む(recommend_relation_normalize.json)
    for fileName, op in researchFileNames.items():
        operations = setOperations(args.source, "all")
        _showRQFigure.setOperations(operations)
        recommendName, renameInfo = setRename(args.source, fileName)
        result_info.append([fileName])

        _logger.debug(f"start researching {fileName}")
        allRename = 0
        allRec = 0
        allTrue = 0
        for commit in renameInfo.keys():
            if commit not in commitToDate:
                continue
            #print(commit)
            tablePath = os.path.join(args.source, "archives", commit, "exTable.csv.gz")
            #tableData = ExTable(tablePath)
            tableData = None
            if fileName == "recommend_none.json":
                countRename, countRec, countTrue = recommendCommit(commit, tableData, operations, recommendName, renameInfo, op)
            else:
                countRename, countRec, countTrue = recommendCommit(commit, tableData, operations, recommendName, renameInfo, op)
            allRename += countRename
            allRec += countRec
            allTrue += countTrue
        
        result_info.append(["allRenames", allRename, "allRecommend", allRec,
                    "allTrueRecommend", allTrue, "precision", allTrue/allRec if allRec != 0 else 0,
                        "recall", allTrue/allRename if allRename != 0 else 0])
        result_info.append([""])
    
    writeMissOperation(missCSV)
    _showRQFigure.calculateData()
    #_showRQFigure.showConsole()
    _showRQFigure.showFigure(args.source)

    with open(detailCSV, 'w') as dCSV:
        w = csv.writer(dCSV)
        w.writerows(detail_info)
    
    with open(resultCSV, 'w') as dCSV:
        w = csv.writer(dCSV)
        w.writerows(result_info)

    with open(allCSV, 'w') as dCSV:
        w = csv.writer(dCSV)
        for i, k in allPrecision.items():
            if k != []:
                w.writerow([i])
                w.writerow([statistics.mean(k)])
            else:
                w.writerow([i])
                w.writerow([0])
        for i, k in allRecall.items():
            if k != []:
                w.writerow([i])
                w.writerow([statistics.mean(k)])
            else:
                w.writerow([i])
                w.writerow([0])
        for i, k in allFscore.items():
            if k != []:
                w.writerow([i])
                w.writerow([statistics.mean(k)])
            else:
                w.writerow([i])
                w.writerow([0])

        

