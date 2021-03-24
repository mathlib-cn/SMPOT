# 2020/12/19 by Typhoon
# encoding: utf-8
# Nodes with one child in the main path must be combined in order to facilitate subsequent processing,
# or the scheduler may report an error.
# Make sure every block on trace has zero or two children.

import sys
import copy
import ast
import shutil
from utility import branches
import pydotplus as pdp

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

def comebine(blocks,trace):
    for blk in blocks:
        if blk.name not in trace:
            continue
        if len(blk.childrenNames) > 1 or len(blk.childrenNames) == 0:
            continue
        for blk2 in blocks:
            if blk2.name == blk.childrenNames[0]:

                blk.childrenNames = blk2.childrenNames
                # children's parent also need to change
                for blk3 in blocks:
                    if blk3.name in blk2.childrenNames:
                        blk3.removePrtName(blk2.name)
                        blk3.addPrtName(blk.name)
                # parents' children also need to change
                for blk3 in blocks:
                    if blk3.name in blk2.parentsNames and blk3.name!=blk.name:
                        blk3.removeChdName(blk2.name)
                        blk3.addChdName(blk.name)

                lastInst = blk.instructions[sorted(blk.instructions)[-1]]
                instSplits = lastInst.replace(',', ' ').split()
                op = instSplits[0]
                if op in branches.sw_unconditional_jump:
                    del blk.instructions[sorted(blk.instructions)[-1]]
                currentLine = len(blk.instructions)
                for key in sorted(blk2.instructions)[1:]:
                    inst = blk2.instructions[key]

                    blk.addInst(currentLine, inst)
                    currentLine = currentLine + 1
                if blk2.name in trace:
                    trace.remove(blk2.name)
                blocks.remove(blk2)
                break

def main():
    # Variables
    blocks = []

    # Make sure everything is in proper format
    if len(sys.argv) != 4:
        print("Improper input format:\n\"python filename outputName\"")
        exit()

    # Read in parameters
    fileName, traceFile, outputName = sys.argv[1:]

    # Open instruction file
    fileIn = open(fileName, 'r')
    rawCodes = copy.deepcopy(fileIn.readlines())
    fileIn.close()

    # find trace
    trace = []
    strTrace = open(traceFile).readlines()[-1]
    for split in strTrace.split(';')[:-1]:
        trace.append(split)
    # print trace

    # Read raw data to restore block chain
    for line in xrange(len(rawCodes)):
        code = rawCodes[line].strip()
        splits = code.split(';')
        blockInstance = block(splits[0])
        blockInstance.parentsNames = ast.literal_eval(splits[1])
        blockInstance.childrenNames = ast.literal_eval(splits[2])
        blockInstance.instructions = ast.literal_eval(splits[3])
        blocks.append(blockInstance)

    flag=True
    while flag:
        flag=False
        for blk in blocks:
            if blk.name not in trace:
                continue
            if len(blk.childrenNames) > 1 or len(blk.childrenNames) == 0:
                continue
            else:
                flag=True
                comebine(blocks, trace)
                break


    # Draw CFG
    outStr = ''
    for blocktmp in blocks:
        if (blocktmp.name == "init"):
            continue
        else:
            for child in blocktmp.childrenNames:
                for blocktmp2 in blocks:
                    if (child == blocktmp2.name):
                        childName = blocktmp2.name
                        outStr = outStr + blocktmp.name + "->" + childName + ";"

    graph = pdp.graph_from_dot_data('digraph demo1{' + outStr + ' }')
    graph.write_jpg('output/6/'+outputName + ".jpg")

    # Save new CFG raw data
    f = open('output/6/'+outputName + ".txt", 'w')
    for blocktmp in blocks:
        f.write(blocktmp.name + ";" + str(blocktmp.parentsNames) + ";" + str(blocktmp.childrenNames) + ";" +
                str(blocktmp.instructions) + "\n")
    f.close()
    shutil.copy('output/6/' + outputName + ".txt", 'output/0/' + outputName + ".txt")

    # Save trace
    f = open('output/6/'+outputName + "_trace.txt", 'w')
    for node in trace:
        f.write(node+";")
    f.close()
    shutil.copy('output/6/' + outputName + "_trace.txt", 'output/0/' + outputName + "_trace.txt")

if __name__ == "__main__":
    main()
