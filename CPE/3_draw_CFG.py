# 2020/12/19 by Typhoon
# encoding: utf-8
# Analyse Control-flow of an assembler and draw its control-flow graph(CFG)

import sys
import copy
import shutil
from utility import branches
import pydotplus as pdp

class block:
	def __init__(self, name):
		self.name = name
		self.startLine= -1
		self.endLine= -1
		self.instructions = {}
		self.children = []
		self.parents = []
		self.childrenNames = []
		self.parentsNames = []

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

def main():
	blocks=[]
	auxiliary={}

	# Make sure everything is in proper format
	if len(sys.argv) != 3:
		print("Improper input format:\n\"python filename outputName\"")
		exit()
	
	# Read in parameters
	fileName, outputName = sys.argv[1:]

	# Open instruction file
	fileIn = open(fileName,'r')
        srcCodes = copy.deepcopy(fileIn.readlines())
        fileIn.close()

	# Clear comment and special intructions like '.align'
	rawCodes=[]
	for line in xrange(len(srcCodes)):
		if srcCodes[line].find('align')!=-1:
			continue
		code = srcCodes[line].rstrip().split('#')
		rawCodes.append(code[0].rstrip())

	#Create auxiliary to save block names
	for line in xrange(len(rawCodes)):
		code = rawCodes[line].strip()
		blockName_ind = code.find(':')
		if(blockName_ind!=-1):
			blockName = code[:blockName_ind]
			auxiliary[blockName]=line

	#Create CFG
	newBlock=False 
	switch=False 	#if block has ended,switch to True
	newBlockCount=0
	blockInstance=block("init")
	for line in xrange(len(rawCodes)):
		code = rawCodes[line].strip()
		blockName_ind = code.find(':')
		whiteSpace_ind = code.find(' ')
		whiteSpace_ind2 = code.find('\t')
		
		if(newBlock): #block start
			if(blockName_ind == -1): 
				newBlockCount=newBlockCount+1
				blockName = "seg"+str(newBlockCount)
				blockInstance =block(blockName)
				blockInstance.startLine=line
				blockInstance.addInst(line,code)
				switch=False
			newBlock=False			
		
		if(blockName_ind!=-1): #block end/start
			if(not switch):
				blockInstance.addChild(line)
				blockInstance.endLine=line-1
				blocks.append(blockInstance)
				switch=False
			blockName =code[:blockName_ind]
			blockInstance =block(blockName)
			blockInstance.startLine=line
			blockInstance.addInst(line,code)
			switch=False
		
		elif(whiteSpace_ind!=-1): #block end
			op = code[:whiteSpace_ind].strip()
			regs = code[whiteSpace_ind:].strip().split(',')
			if(op in branches.sw_conditional_branch):	# has two children
				jmpName=regs[int(branches.sw_conditional_branch[op])]
				jmpLine=auxiliary[jmpName]
				blockInstance.addChild(jmpLine)
				blockInstance.addChild(line+1)
				blockInstance.endLine=line
				blockInstance.addInst(line,code)
				blocks.append(blockInstance)
				newBlock=True
				switch=True
			elif op in branches.sw_unconditional_jump:	# has one child
				if op=='br':
					jmpName=regs[-1]
				else:
					jmpName = regs[int(branches.sw_unconditional_jump[op])]
				jmpLine = auxiliary[jmpName]
				blockInstance.addChild(jmpLine)
				blockInstance.endLine = line
				blockInstance.addInst(line, code)
				blocks.append(blockInstance)
				newBlock = True
				switch = True
			else:
				blockInstance.addInst(line,code)
				continue
		
		elif(whiteSpace_ind2!=-1): #block end
			op = code[:whiteSpace_ind2].strip()
			regs = code[whiteSpace_ind2:].strip().split(',')
			if(op in branches.sw_conditional_branch):
				jmpName=regs[int(branches.sw_conditional_branch[op])]
				jmpLine=auxiliary[jmpName]
				blockInstance.addChild(jmpLine)
				blockInstance.addChild(line+1)
				blockInstance.endLine=line
				blockInstance.addInst(line,code)
				blocks.append(blockInstance)
				newBlock=True
				switch=True
			elif op in branches.sw_unconditional_jump:	# has one child
				if op=='br':
					jmpName=regs[-1]
				else:
					jmpName = regs[int(branches.sw_unconditional_jump[op])]
				jmpLine = auxiliary[jmpName]
				blockInstance.addChild(jmpLine)
				blockInstance.endLine = line
				blockInstance.addInst(line, code)
				blocks.append(blockInstance)
				newBlock = True
				switch = True
			else:
				blockInstance.addInst(line,code)
				continue
	
		elif(code == 'ret'): #block end
			blockInstance.endLine=line
			blockInstance.addInst(line,code)
			blocks.append(blockInstance)
			switch=True
		else:
			blockInstance.addInst(line,code)
			continue

	#Modify segName in instructions
	for blocktmp in blocks:
		if blocktmp.name=='init':
			continue
		firstInstIndex=sorted(blocktmp.instructions)[0]
		firstInst=blocktmp.instructions[firstInstIndex]
		if firstInst.find(':')!=-1:
			if firstInst.split(':')[1]!='':
				firstInst=firstInst.split(':')[1].replace('\t','')
				blocktmp.instructions[firstInstIndex]=firstInst
				blocktmp.addInst(0,blocktmp.name+':')
		else:
			blocktmp.addInst(0,blocktmp.name+':')

	#Add rest block details		
	for blocktmp in blocks:
		for child in blocktmp.children:
			for blocktmp2 in blocks:
				if (child==blocktmp2.startLine):
					blocktmp2.addParent(blocktmp.startLine)
					blocktmp2.addPrtName(blocktmp.name)
					blocktmp.addChdName(blocktmp2.name)

	#Print blocks on screen
	'''
	for blocktmp in blocks:
		print blocktmp.name+":"
		print blocktmp.instructions
		print "------------------------------------------------------------------"
	print "\n"
	'''

	#Print CFG on screen
	'''
	print ('{:<20}{:<20}{:<20}{:<20}{:<20}{:<20}{:<20}'.format("blockName","startLine","endLine","parents","children","prtNames","chdNames"))
	for blocktmp in blocks:
		print ('{:<20}{:<20}{:<20}{:<20}{:<20}{:<20}{:<20}'.format(blocktmp.name,blocktmp.startLine,blocktmp.endLine,blocktmp.parents,blocktmp.children,blocktmp.parentsNames,blocktmp.childrenNames))
	'''

	#Draw CFG
	outStr=''	
	childName=''
	for blocktmp in blocks:
		if (blocktmp.name== "init"): 
			continue
		else:
			for child in blocktmp.children:
				for blocktmp2 in blocks:
					if (child==blocktmp2.startLine):
						childName=blocktmp2.name
						outStr=outStr+blocktmp.name+"->"+childName+";"


	graph = pdp.graph_from_dot_data('digraph demo1{ node [shape=box, style="rounded", color="black"];'+outStr+' }')
	graph.write_jpg('output/3/'+outputName+".jpg")

	#Save CFG raw data
	f = open('output/3/'+outputName+"_rawdata.txt", 'w')
	for blocktmp in blocks:
		if(blocktmp.name!='init'):
			f.write(blocktmp.name+";"+str(blocktmp.parentsNames)+";"+str(blocktmp.childrenNames) +";"+str(blocktmp.instructions)+"\n")
	f.close()
	shutil.copy('output/3/'+outputName+"_rawdata.txt", 'output/0/' +outputName+"_rawdata.txt")


if __name__ == "__main__":
    main()
