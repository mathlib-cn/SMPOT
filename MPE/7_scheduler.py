# 2020/12/19 by Typhoon
# encoding: utf-8
# Superblock Scheduler

import sys
import ast
import copy
import shutil
from scheduler import general_scheduler
from scheduler import superblock_scheduler

class block:
    def __init__(self, name):
        self.name = name
        self.newName = "dup0"
        self.startLine = -1
        self.endLine = -1
        self.instructions = {}
        self.children = []
        self.parents = []
        self.childrenNames = []
        self.parentsNames = []
        self.expects= {}

    def addChild(self, child):
        self.children.append(child)

    def addParent(self, parent):
        self.parents.append(parent)

    def addInst(self, line, inst):
        self.instructions[line] = inst

    def addChdName(self, cName):
        self.childrenNames.append(cName)

    def addPrtName(self, pName):
        self.parentsNames.append(pName)

    def removeChdName(self, cName):
        self.childrenNames.remove(cName)

    def removePrtName(self, pName):
        self.parentsNames.remove(pName)


def main():
    # Make sure everything is in proper format
    if len(sys.argv) != 6:
        print("Improper input format:\n\"-(a,b,c) -(a,b,c,x) CRD tracefile outputName\"")
        exit()
    # Read in parameters
    strategy_TS,strategy_GS, filename, tracefile, outputName = sys.argv[1:]

    # find trace
    trace = []
    strTrace = open(tracefile).readlines()[-1]
    for split in strTrace.split(';')[:-1]:
        trace.append(split)
    # print trace

    # Open CRD file
    blocks=[]
    fileIn = open(filename)
    rawCodes = copy.deepcopy(fileIn.readlines())
    # Read raw data to restore block chain
    for line in xrange(len(rawCodes)):
        code = rawCodes[line].strip()
        splits = code.split(';')

        blockInstance = block(splits[0])
        blockInstance.parentsNames = ast.literal_eval(splits[1])
        blockInstance.childrenNames = ast.literal_eval(splits[2])
        blockInstance.instructions = ast.literal_eval(splits[3])
        blocks.append(blockInstance)

    # Main path
    blocks=superblock_scheduler.superblock_scheduling(blocks,trace,strategy_TS,outputName)

    # Side Paths
    if strategy_GS == '-x':
        None
    else:
        None
    '''
        for blocktmp in blocks:
            if blocktmp.name not in trace:
                blocktmp=general_scheduler.basic_block_scheduling(blocktmp,strategy_GS)
    '''

    # Save new CFG raw data
    f = open('output/7/'+outputName + ".txt", 'w')
    for blocktmp in blocks:
        f.write(blocktmp.name + ";" + str(blocktmp.parentsNames) + ";" + str(blocktmp.childrenNames) + ";" +
                str(blocktmp.instructions) + "\n")
    f.close()
    shutil.copy('output/7/' + outputName + ".txt", 'output/0/' + outputName + ".txt")


if __name__ == "__main__":
    main()


