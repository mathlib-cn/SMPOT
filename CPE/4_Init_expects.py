# 2020/12/19 by Typhoon
# encoding: utf-8
# Set main path
# 1.Hot path is the most frequently executed path of the assembler.
# 2.Expect is the possibility of a branch.
#   Set the except like this:
#   ----------------------
#   main;bbn1,0.8;bbn2,0.2
#   bbn1;bbn3,0.6;bbn4,0,4
#   ----------------------
#   'main' has two children,0.8 means the execution possibility of bbn1 is 80%.
#   If its not set,0.5 is a default value.
#   That also means the main path is main->bbn1->bbn3.
#   If the block in main path has no child or one child,it doesn't need be marked.


import sys
import copy
import ast
import os
import shutil
import pydotplus as pdp
from IPython.display import display, Image


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
        self.expects = {}

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

    def addExpect(self, child, expect):
        self.expects[child] = expect


def main():
    # Variables
    blocks = []
    expects = {}

    # Make sure everything is in proper format
    if len(sys.argv) != 4:
        print("Improper input format:\n\"python filename expectsfile outputName\"")
        exit()

    # Read in parameters
    fileName, expectsfile,outputName = sys.argv[1:]

    # Open instruction file
    fileIn = open(fileName, 'r')
    rawCodes = copy.deepcopy(fileIn.readlines())
    fileIn.close()

    # Open expects file
    if os.path.exists(expectsfile):
        fileExpects = open(expectsfile,'r')
        rawCodes2 = copy.deepcopy(fileExpects.readlines())
        for line in xrange(len(rawCodes2)):
            childExpects={}
            code = rawCodes2[line].strip()
            splits = code.split(';')
            prtName=splits[0]
            childExpects[splits[1].split(',')[0]]=splits[1].split(',')[1]
            childExpects[splits[2].split(',')[0]]=splits[2].split(',')[1]
            expects[splits[0]]=childExpects
        fileExpects.close()
    else:
        None


    # Create auxiliary to save block names
    for line in xrange(len(rawCodes)):
        code = rawCodes[line].strip()
        splits = code.split(';')
        blockInstance = block(splits[0])
        blockInstance.parentsNames = ast.literal_eval(splits[1])
        blockInstance.childrenNames = ast.literal_eval(splits[2])
        blockInstance.instructions = ast.literal_eval(splits[3])
        blocks.append(blockInstance)
    # print blockInstance.instructions

    initExpects(blocks,expects)

    # Save new CFG raw data
    f = open('output/4/'+outputName + ".txt", 'w')
    for blocktmp in blocks:
        f.write(blocktmp.name + ";" + str(blocktmp.startLine) + ";" + str(blocktmp.endLine) + ";" + str(
            blocktmp.parents) + ";" + str(blocktmp.children) + ";" + str(blocktmp.parentsNames) + ";" + str(
            blocktmp.childrenNames) + ";" + str(blocktmp.instructions) + ";"+ str(blocktmp.expects) +"\n")
    f.close()
    shutil.copy('output/4/' + outputName + ".txt", 'output/0/' + outputName + ".txt")
    shutil.copy('input/'+outputName+'_expects.txt' , 'done/' + outputName+'_expects.txt')

# Init Expects
def initExpects(blocks,expects):
    for blocktmp in blocks:
        if len(blocktmp.childrenNames) > 1:
            for child in blocktmp.childrenNames:
                if blocktmp.name in expects:
                    blocktmp.addExpect(child,float(expects[blocktmp.name][child]))
                else:
                    blocktmp.addExpect(child, 0.5)
        elif len(blocktmp.childrenNames) == 1:
            blocktmp.addExpect(blocktmp.childrenNames[0], 1)


if __name__ == "__main__":
    main()
