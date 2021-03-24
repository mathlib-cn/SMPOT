from utility import latency
import copy
from utility import branches
from utility import instructions_arithmetic
from utility import machine_model
import collections
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





class node:
    def __init__(self, line, inst, original):
        self.line = line
        self.inst = inst
        self.children = {}
        self.parents = {}
        self.latencyPath = 0
        self.originalText = original

    def addChild(self, childName, child):
        self.children[childName] = child

    def addParent(self, parentName, parent):
        self.parents[parentName] = parent
        
    def __str__(self):
        return str(self.line) + " - Children: " + str(self.children) + "\nParents: " + str(self.parents) + "\n"



