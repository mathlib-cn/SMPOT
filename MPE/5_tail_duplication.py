# 2020/12/19 by Typhoon
# encoding: utf-8
# Remove redundant entrances in the main path.
# It is a basic enlarging technology in superblock scheduling.
# After tail duplication,only one entrance is left in trace and code size will be expanded.
# Back arc of a loop in the main path will be handled with Cut and Sew Algorithm(CS Algorithm).

import sys
import copy
import ast
from utility import branches
import collections
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

def findTrace(blocks):
    trace=[]
    nextChild=blocks[0].name
    for block in blocks:
        if block.name == nextChild:
            trace.append(nextChild)
            Max=-1
            for segName,expect in block.expects.items():
                if expect==max(block.expects.values()):
                    nextChild=segName
    return trace



def main():
    blocks = []

    # Make sure everything is in proper format
    if len(sys.argv) != 3:
        print("Improper input format:\n\"python filename outputName\"")
        exit()

    # Read in parameters
    fileName, outputName = sys.argv[1:]

    # Open instruction file
    fileIn = open(fileName, 'r')
    rawCodes = copy.deepcopy(fileIn.readlines())
    fileIn.close()

    # Read raw data to restore block chain
    for line in xrange(len(rawCodes)):
        code = rawCodes[line].strip()
        splits = code.split(';')
        blockInstance = block(splits[0])
        blockInstance.startLine = splits[1]
        blockInstance.endLine = splits[2]
        blockInstance.parents = ast.literal_eval(splits[3])
        blockInstance.children = ast.literal_eval(splits[4])
        blockInstance.parentsNames = ast.literal_eval(splits[5])
        blockInstance.childrenNames = ast.literal_eval(splits[6])
        blockInstance.instructions = ast.literal_eval(splits[7])
        blockInstance.expects = ast.literal_eval(splits[8])
        blocks.append(blockInstance)

    #find the hot paths
    trace = findTrace(blocks)
    f = open('output/5/'+outputName + "_trace.txt", 'w')
    for node in trace:
        f.write(node+";")
    f.close()
    shutil.copy('output/5/' + outputName + "_trace.txt", 'output/0/' + outputName + "_trace.txt")

    # Cut and Sew Algorithm
    # Codes below just do tail dupliation with one block every time.It stops until there're no JOINS on trace.
    dupCount = 0
    loopCount = 0
    while True:
        Loopflag=0
        for block1 in blocks:
            if block1.name in trace:
                abc,versTmp=findLoop(blocks)
                if len(block1.parentsNames)>1 and block1.name not in versTmp:
                    Loopflag=1
                    break
        if Loopflag==0:
            break
        if Loopflag==1:
                loopCount=loopCount+1
                loopVertices,vers=findLoop(blocks)
                blocks, dupCount = tailDuplication(blocks, dupCount ,loopVertices,trace)

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
    graph.write_jpg('output/5/'+outputName + ".jpg")
    shutil.copy('output/5/' + outputName + ".jpg", 'output/0/' + outputName + ".jpg")

    # reorder lineNumbers of instructions,such that indexs of instructions starts from 0
    for blocktmp in blocks:
        newInstructions = {}
        instIndex = 0
        for key in sorted(blocktmp.instructions):
            newInstructions[instIndex]=blocktmp.instructions[key]
            instIndex=instIndex+1
        blocktmp.instructions=newInstructions

    # Save new CFG raw data
    f = open('output/5/'+outputName + ".txt", 'w')
    for blocktmp in blocks:
        f.write(blocktmp.name + ";" + str(blocktmp.parentsNames) + ";" + str(blocktmp.childrenNames) + ";" +
                str(blocktmp.instructions) + "\n")
    f.close()
    shutil.copy('output/5/' + outputName + ".txt", 'output/0/' + outputName + ".txt")

def tailDuplication(blocks, dupCount,loopVertices,trace):
    # remove the back edge of a loop,and restore later
    for blocktmp in blocks:
        if (blocktmp.name in loopVertices.keys()):
            blocktmp.removeChdName(loopVertices[blocktmp.name])
        loopVerticesTmp=copy.deepcopy(loopVertices)
        for val in loopVertices.values():
            if blocktmp.name == val:
                blocktmp.removePrtName(list(loopVerticesTmp.keys())[list(loopVerticesTmp.values()).index(blocktmp.name)])
                loopVerticesTmp.pop(list(loopVerticesTmp.keys())[list(loopVerticesTmp.values()).index(blocktmp.name)])
    # begin to duplicate
    dupFlag = False
    stack3=[]
    for blocktmp in blocks:
        # debug
        if blocktmp.name=='TRIG_RDX_TZ11':
            None

        if blocktmp.name not in trace:
            continue

        if  (dupFlag):
            break
        if len(blocktmp.parentsNames) > 1:
            dupFlag = True
            for parent in blocktmp.parentsNames:
                if  parent in trace:
                    if trace.index(blocktmp.name)-trace.index(parent)==1:
                        continue
                for blocktmp2 in blocks:
                    if (str(parent) == str(blocktmp2.name)):

                        blocktmp2.removeChdName(blocktmp.name)
                        bb = copy.deepcopy(blocktmp)
                        for prt in bb.parentsNames:
                            if str(prt) != str(parent):
                                bb.removePrtName(prt)
                        for prt in blocktmp.parentsNames:
                            if str(prt) == str(parent):
                                blocktmp.removePrtName(prt)
                        dupCount = dupCount + 1
                        bb.newName = "dup" + str(dupCount)
                        blocktmp2.addChdName(bb.newName)
                        branchInst = blocktmp2.instructions[sorted(blocktmp2.instructions)[-1]]
                        whiteSpace_ind = branchInst.find(' ')
                        op = ''
                        regs = []
                        jmpName = ''
                        if whiteSpace_ind != -1 and branchInst != 'ret':
                            op = branchInst.strip().split(' ')[0]
                            regs = branchInst.strip().split(' ')[1].split(',')
                        if whiteSpace_ind == -1 and branchInst != 'ret':
                            op = branchInst.strip().split('\t')[0]
                            regs = branchInst.strip().split('\t')[1].split(',')

                        if op in branches.sw_unconditional_jump:
                            jmpName = regs[int(branches.sw_unconditional_jump[op])]
                        elif op in branches.sw_conditional_branch:
                            jmpName = regs[int(branches.sw_conditional_branch[op])]

                        if jmpName == blocktmp.name:
                                blocktmp2.instructions[sorted(blocktmp2.instructions)[-1]] = branchInst.replace(jmpName,
                                                                                                    bb.newName)
                        else:
                            None

                        stack = [bb]
                        stack2 = [bb]
                        while stack != []:
                            bb = stack.pop(0)

                            appendFlag = True
                            for x in stack2:
                                if (x.name == bb.name):
                                    appendFlag = False
                            if (appendFlag):
                                dupCount = dupCount + 1
                                bb.newName = "dup" + str(dupCount)
                                stack2.append(bb)

                            for child in bb.childrenNames:
                                for tt in blocks:
                                    if str(child) == str(tt.name):
                                        stack.append(copy.deepcopy(tt))

                        stack3 = copy.deepcopy(stack2)
                        stackName = []
                        for ss0 in stack3:
                            stackName.append(ss0.newName)
                        for ss1 in stack3:
                            branchInst = ss1.instructions[sorted(ss1.instructions)[-1]]
                            whiteSpace_ind = branchInst.find(' ')
                            op = ''
                            regs=[]
                            jmpName=''
                            if branchInst=='unop':
                                op = 'unop'
                            elif whiteSpace_ind != -1 and branchInst != 'ret':
                                op = branchInst.strip().split(' ')[0]
                                regs = branchInst.strip().split(' ')[1].split(',')
                            elif whiteSpace_ind == -1 and branchInst != 'ret':
                                op = branchInst.strip().split('\t')[0]
                                regs = branchInst.strip().split('\t')[1].split(',')
                            else:
                                None

                            if op in branches.sw_unconditional_jump:
                                jmpName = regs[int(branches.sw_unconditional_jump[op])]
                            elif op in branches.sw_conditional_branch:
                                jmpName = regs[int(branches.sw_conditional_branch[op])]
                            for ss2 in stack2:
                                if jmpName == ss2.name:
                                    ss1.instructions[sorted(ss1.instructions)[-1]]=branchInst.replace(jmpName,ss2.newName)
                            else:
                                None


                        for ss1 in stack3:
                            m = ss1.childrenNames[:]
                            for chd in m:
                                for ss2 in stack2:
                                    if chd == ss2.name:
                                        ss1.removeChdName(chd)
                                        ss1.addChdName(ss2.newName)

                            m = ss1.parentsNames[:]
                            for prt in m:
                                for ss2 in stack2:
                                    if prt == ss2.name:
                                        ss1.removePrtName(prt)
                                        ss1.addPrtName(ss2.newName)


                        for ss1 in stack3[1:]:
                            for prt in ss1.parentsNames:
                                if prt not in stackName:
                                    ss1.removePrtName(prt)
                break

    nameMap={}
    for ss1 in stack3:
        nameMap[ss1.name]=ss1.newName
    for ss1 in stack3:
        firstInst=ss1.instructions[sorted(ss1.instructions)[0]]
        index= firstInst.find(':')
        if index!=-1:
            ss1.instructions[sorted(ss1.instructions)[0]]=firstInst.replace(firstInst[:index], ss1.newName)

    kStack = []
    for ss1 in stack3:
        if ss1.name in loopVertices.keys():
            for ss2 in stack3:
                if ss2.name == loopVertices[ss1.name]:
                    temp = ss2.newName
                    ss1.addChdName(temp)
                    ss2.addPrtName(ss1.newName)
                    kStack.append(ss1)

            for ss2 in blocks:
                if ss2.name == loopVertices[ss1.name] and ss1 not in kStack:
                        ss1.addChdName(ss2.name)
                        ss2.addPrtName(ss1.newName)

    for ss1 in stack3:
        ss1.name = ss1.newName

    for qq in blocks:
        if (qq.name in loopVertices.keys()):
            qq.addChdName(loopVertices[qq.name])

        loopVerticesTmp=copy.deepcopy(loopVertices)
        for it in loopVerticesTmp.values():
            if qq.name == it:
                qq.addPrtName(list(loopVerticesTmp.keys())[list(loopVerticesTmp.values()).index(
                qq.name)])
                loopVerticesTmp.pop(list(loopVerticesTmp.keys())[list(loopVerticesTmp.values()).index(
                    qq.name)])
    blocks = blocks + stack3
    return blocks, dupCount

 # find Loops in CFG (find circles in graph)
def findLoop(blocks):
    relationDic = collections.OrderedDict()
    for block in blocks:
        relationDic[block.name] = block.childrenNames
    circles = []
    vertices=[]
    loopVertices={}
    def recursion(temp):
        li = relationDic[temp[-1]]
        if not li:
            return
        for i in li:
            if i not in temp:
                temp.append(i)
                recursion(temp)
                temp.remove(i)
            else:
                if temp[0] in relationDic[temp[-1]]:
                    trig=False
                    for circle in circles:
                        if sorted(temp) == sorted(circle) :
                            trig=True
                    if not trig:
                        circles.append(copy.deepcopy(temp))
                        loopVertices[temp[-1]]=temp[0]
                    return
    temp = []
    for key in relationDic:
        temp.append(key)
        recursion(temp)
        temp.remove(key)
    for circle in circles:
        for vertex in circle:
            if vertex not in vertices:
                vertices.append(vertex)
    return loopVertices,vertices

if __name__ == "__main__":
    main()
