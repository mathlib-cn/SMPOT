# 2020/12/19 by Typhoon
# encoding: utf-8
# Restore CRD to an Assembler
# NOTATION:
# 1.A block end with an conditional branch has two children,a block end with a unconditional jump has one child
# 2.In an assembler,blocks are in linear order.If block B is next to block A in the sequence,we define B is a
#   direct branch of A.If block C is reached by a jump in block A,we define C is a indirect branch of A.
# 3.to process .The fisrt element of a list is a indirect branch'name and The latter is the direct branch
#   if the former.


import sys
import copy
import ast
from utility import branches
import shutil


class block:
    def __init__(self, name):
        self.name = name
        self.newName = "dup0"
        self.childrenNames = []
        self.parentsNames = []
        self.instructions = {}

    def addChdName(self, cName):
        self.childrenNames.append(cName)

    def addPrtName(self, pName):
        self.parentsNames.append(pName)

    def removeChdName(self, cName):
        self.childrenNames.remove(cName)

    def removePrtName(self, pName):
        self.parentsNames.remove(pName)


def findBranch(blocktmp):
        block=copy.deepcopy(blocktmp)
        returnCode=-1
        directBranch=''
        indirectBranch=''
        branchInst = block.instructions[sorted(block.instructions)[-1]]
        whiteSpace_ind = branchInst.find(' ')
        op = ''
        if whiteSpace_ind != -1 and branchInst != 'ret':
            op = branchInst.strip().split(' ')[0]
            regs = branchInst.strip().split(' ')[1].split(',')
        if whiteSpace_ind == -1 and branchInst != 'ret':
            if branchInst == 'unop':
                op = 'unop'
            else:
                op = branchInst.strip().split('\t')[0]
                regs = branchInst.strip().split('\t')[1].split(',')

        if op in branches.sw_unconditional_jump:  # one indirect child
            indirectBranch=block.childrenNames[0]
            returnCode=0

        elif op in branches.sw_conditional_branch: # two children
            jmpName = regs[int(branches.sw_conditional_branch[op])]
            block.removeChdName(jmpName)
            directBranch=block.childrenNames[0]
            indirectBranch=jmpName
            returnCode=1

        elif branchInst == 'ret' :
            returnCode=2

        else:
            if block.childrenNames==[]:  # block ends without a 'ret'
                returnCode=4
            else:   # block with one child and has no brach instruction
                directBranch=block.childrenNames[0]
                returnCode=3

        return returnCode,directBranch,indirectBranch


def main():
    # Variables
    blocks = []

    # Make sure everything is in proper format
    if len(sys.argv) != 2:
        print("Improper input format:\n\"python filename outputName\"")
        exit()

    # Read in parameters
    fileName = 'output/0/'+sys.argv[1]+'_scheduled.txt'
    outputName = 'output/8/'+sys.argv[1]+'_scheduled'

    # Open instruction file
    fileIn = open(fileName, 'r')
    rawCodes = copy.deepcopy(fileIn.readlines())
    fileIn.close()

    # Read raw data to restore block chain
    for line in xrange(len(rawCodes)):
        code = rawCodes[line].strip()
        splits = code.split(';')
        blockInstance = block(splits[0])
        blockInstance.parentsNames = ast.literal_eval(splits[1])
        blockInstance.childrenNames = ast.literal_eval(splits[2])
        blockInstance.instructions = ast.literal_eval(splits[3])
        blocks.append(blockInstance)

    f = open(outputName + ".S", 'w')

    outlistSet=[]
    outlistSet.append([blocks[0].name])


    for blocktmp in blocks:
        code,directBranch,indirectBranch=findBranch(blocktmp)
        if code == 0:
            inListFlag=False
            for list in outlistSet:
                if indirectBranch in list:
                    inListFlag=True
                    break
            if not inListFlag:
                outlistSet.append([indirectBranch])

        elif code == 1: # two children
            for list in outlistSet:
                if blocktmp.name in list:
                    list.append(directBranch)
            inListFlag = False
            for list in outlistSet:
                if indirectBranch in list:
                    inListFlag = True
                    break
            if not inListFlag:
                outlistSet.append([indirectBranch])

        elif code ==2 : #ret
            None

        elif code ==3:
            for list in outlistSet:
                if blocktmp.name in list:
                    list.append(directBranch)

        else: #code==4
            None


    loop=True
    while(loop):
        raw_outlistSet = copy.deepcopy(outlistSet)
        for list in outlistSet:
            for list2 in outlistSet:
                if list!=[] and list2!=[] and list!=list2 and list[-1]==list2[0]:
                    index1=outlistSet.index(list)
                    index2=outlistSet.index(list2)
                    outlistSet[index1]=list+list2[1:]
                    outlistSet[index2]=[]
        if outlistSet==raw_outlistSet:
           loop=False

    removeList = []
    for outlist in outlistSet:
        for outlist2 in outlistSet:
            if set(outlist) < set(outlist2):
                removeList.append(outlist)
                break
    for element in removeList:
        outlistSet.remove(element)

    outputList=[]
    for list in outlistSet:
        for segName in list:
            if segName not in outputList:
                outputList.append(segName)


    for name in outputList:
        if name== 'seg7':
            None
        for blocktmp in blocks:
            if name == blocktmp.name:
                for inst in sorted(blocktmp.instructions):
                    if blocktmp.instructions[inst] == blocktmp.name + ':':
                        f.write(blocktmp.name + ':\n')
                    else:
                        f.write('\t' + blocktmp.instructions[inst].strip() + '\n')




    f.close()

    shutil.copy( outputName+ ".S" , 'output/0/'+sys.argv[1]+'_scheduled.S')

if __name__ == "__main__":
    main()