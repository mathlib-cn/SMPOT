# 2020/12/19 by Typhoon
# encoding: utf-8

import copy
from utility import latency
from utility import branches
import collections
from utility import instructions_arithmetic
from utility import machine_model
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

# if have dependence return 1,else return 0
def find_dependence(instruction, tracePoint, trace, blocks):	# instruction can't be 'ret'
	abc, versTmp = findLoop(blocks)

	if tracePoint.name== 'TRIG_RDX_TZ4':
		None
	currentNode=tracePoint

	#if len(node.childrenNames)==1: # The branch in this block is unconditional jump like 'j'
	#	return 0
	if len(tracePoint.childrenNames)==0 : # Its the end of the trace
		return 0,currentNode,-1,''
	else:
		instructionSplit = instruction.replace(',', ' ').split()
		raw_wreg=instructionSplit[-1]
		if instructionSplit[0] in instructions_arithmetic.sw_imm_load_arithmetic \
				or instructionSplit[0] in instructions_arithmetic.sw_mem_load_arithmetic:
			raw_wreg=instructionSplit[1]
		firstNode = tracePoint
		stack=[]
		for child in tracePoint.childrenNames:
			if child not in trace:
				firstNode = child
		for block in blocks:
			if block.name == firstNode:
				stack=[block]
				break
		while stack!=[]:
			currentNode=stack.pop(0)
			if currentNode.name=='TRIG_RDX_TZ4':
				None
			for line in sorted(currentNode.instructions)[1:]:
				inst=currentNode.instructions[line]
				instSplits=inst.replace(',', ' ').split()
				if len(instSplits)>2:
					wReg = instSplits[-1]
				for index,split in enumerate(instSplits): #clear '( )'
					ind=split.find('(')
					if ind!=-1:
						instSplits[index]=split[ind+1:-1]
				op = instSplits[0]
				if op == 'ret' or op =='unop':
					continue
				if instructionSplit[0] in instructions_arithmetic.sw_mem_store_arithmetic:
					if op in instructions_arithmetic.sw_mem_load_arithmetic:
						if raw_wreg == wReg:
							return 1,currentNode,line,inst
						else:
							continue
					else:
						continue

				else:
					if op in instructions_arithmetic.sw_imm_load_arithmetic or op in instructions_arithmetic.sw_mem_load_arithmetic:
						wReg=instSplits[1]
					else:
						wReg = instSplits[-1]
					if raw_wreg in instSplits[1:]:
						if op in branches.sw_conditional_branch or op in branches.sw_unconditional_jump:
							return 1,currentNode,line,inst
						elif op == 'wfpcr':
							return 1,currentNode,line,inst
						elif op == 'rfpcr':
							return 0,currentNode,-1,''
						elif op in instructions_arithmetic.sw_mem_store_arithmetic :
							return 1,currentNode,line,inst
						elif op not in instructions_arithmetic.sw_imm_load_arithmetic and wReg == raw_wreg and wReg not in instSplits[:-1] :	# ld a1,24(a1)	sd a1,24(a1)	#General Case
							return 0,currentNode,-1,''
						elif op in instructions_arithmetic.sw_imm_load_arithmetic and wReg==raw_wreg and wReg not in instSplits[2:]:
							return 0, currentNode, -1, ''
						else:
							return 1,currentNode,line,inst
					else:
						continue
			for child in currentNode.childrenNames:
				for block in blocks:
					if block.name==child and block.name not in abc.values():
						stack.append(block)
						break
		return 0,currentNode,-1,''

cycleFileName=''

def superblock_scheduling(blocks,trace,strategy,outputName):
	global cycleFileName
	cycleFileName=outputName

	depTable1=check_downward_motion(blocks,trace)
	depTable2=check_upward_motion(blocks,trace)

	return constrained_basic_block_scheduler(blocks,trace,depTable1,depTable2,strategy)


# Avoid code compensation
def check_upward_motion(blocks,trace):
	depTable=[]

	for node in trace[1:]:
		for block in blocks:
			if node == block.name:
				for key in sorted(block.instructions)[1:]:
					inst = block.instructions[key]
					instSplits = inst.replace(',', ' ').split()
					op = instSplits[0]
					if op in branches.sw_conditional_branch or op in branches.sw_unconditional_jump:
						continue
					elif op == 'ret':
						continue
					elif op == 'unop':
						continue
					else:
						retVal=0
						currentIndex=trace.index(block.name)-1
						currentNodeName=trace[currentIndex]
						for blocktmp2 in blocks:
							if blocktmp2.name==currentNodeName:
								currentNode=blocktmp2
						while retVal==0 :
							retVal,depBlock,depLine,depInst=find_dependence(inst,currentNode,trace,blocks)
							if retVal==1:
								depLine=sorted(currentNode.instructions)[-1]
								depInst=currentNode.instructions[depLine]
								depTable.append([block,key,inst,currentNode,depLine,depInst])
								break
							else:
								nodeIndex=trace.index(currentNode.name)
								if nodeIndex!=-1:
									nodeIndex=nodeIndex-1
									if nodeIndex==-1:
										break
									for blocktmp in blocks:
										if blocktmp.name==trace[nodeIndex]:
											currentNode = blocktmp
								else:
									break
	return depTable



def check_downward_motion(blocks,trace):
	depTable=[]

	for node in trace:
		for block in blocks:
			if node == block.name:
				for key in sorted(block.instructions)[1:]:
					inst = block.instructions[key]
					instSplits = inst.replace(',', ' ').split()
					op = instSplits[0]
					if op in branches.sw_conditional_branch or op in branches.sw_unconditional_jump:
						continue
					elif op == 'wfpcr':
						continue
					elif op == 'unop':
						continue
					else:
						retVal=0
						currentNode=block
						while retVal==0 :
							if inst.find('$f13')!=-1:
								None
							retVal,depBlock,depLine,depInst=find_dependence(inst,currentNode,trace,blocks)
							if retVal==1:
								depLine=sorted(currentNode.instructions)[-1]
								depInst=currentNode.instructions[depLine]
								depTable.append([block,key,inst,currentNode,depLine,depInst])
								break
							else:
								nodeIndex=trace.index(currentNode.name)
								if nodeIndex!=len(trace)-1:
									nodeIndex=nodeIndex+1
									for blocktmp in blocks:
										if blocktmp.name==trace[nodeIndex]:
											currentNode = blocktmp
								else:
									break
	return depTable


def constrained_basic_block_scheduler(blocks,trace,depTable1,depTable2,strategy):
	superBlock=[]
	for tracePoint in trace:
		for block in blocks:
			if tracePoint==block.name:
				for key in sorted(block.instructions):
					op=block.instructions[key]
					if op.find(':')!=-1:
						continue
					elif  op =='ret' or op =='unop':
						continue
					else:
						superBlock.append([block.name,key,block.instructions[key]])

	depGraph = createDepenGraph(superBlock,depTable1,depTable2)

	# Run specific schedulers on graph
	if strategy == "-a":
		output = a(depGraph)
		ideal_origin_cycle(superBlock,depGraph)
	elif strategy == "-b":
		output = b(depGraph)
	elif strategy == "-c":
		output = c(depGraph)
	else:
		print("Invalid scheduler specified\n-(a,b,c) are accepted")

	traceIndex=0
	currentTracePoint=blocks[0]
	for kk in blocks:
		if kk.name==trace[traceIndex]:
			currentTracePoint=kk
			currentTracePoint.instructions={}
			break

	index=0
	currentTracePoint.addInst(0, currentTracePoint.name + ':')

	for split in output.split(";")[:-1]:
		line = [i.strip(",") for i in split.replace(',', ' ').split()]
		op = line[0]
		if op in branches.sw_conditional_branch:
			index=index+1
			currentTracePoint.addInst(index,split)
			for tp in blocks:
				if tp.name == trace[traceIndex+1]:
					currentTracePoint = tp
					currentTracePoint.instructions = {}
					currentTracePoint.addInst(0, currentTracePoint.name + ':')
					traceIndex=traceIndex+1
					index=0
					break
		else:
			index = index + 1
			currentTracePoint.addInst(index, split)

		if trace[-1]==currentTracePoint.name:
			currentTracePoint.addInst(index+1,'ret')

	return blocks

class node:
	def __init__(self, newLine, originalLine, op, inst, segName):
		self.newline = newLine
		self.originalLine = originalLine
		self.op = op
		self.inst =inst
		self.segName =segName
		self.children = {}
		self.parents = {}
		self.latencyPath = 0

	def addChild(self, childName, child):
		self.children[childName] = child

	def addParent(self, parentName, parent):
		self.parents[parentName] = parent
		
	def __str__(self):
		return str(self.line) + " - Children: " + str(self.children) + "\nParents: " + str(self.parents) + "\n"

def isImmediate(strInput):
    if strInput.find('0x')!=-1 :
        return True
    elif strInput.lstrip('-').isdigit() :
        return True
    else:
        return False

def createDepenGraph(superBlock,depTable1,depTable2):
	read = collections.defaultdict(list)
	write = collections.defaultdict(list)
	nodes = []
	branchMark=0
	branchNode=node(-1,-1,"","","")
	newLineNumber=0
	for elem in superBlock:
		segName=elem[0]
		originalLineNumber=elem[1]
		instruction=elem[2]
		line = [i.strip(",") for i in instruction.replace(',',' ').split()]
		op = line[0]
		nodes.append(node(newLineNumber, originalLineNumber, op , instruction ,segName))
		newLineNumber=newLineNumber+1



	# Downward motions dependency
	# [instBlock,lineNumber,inst,splitBlockName,depBlock,depLine,depInst]
	for curr in nodes:
		for depElement in depTable1:
			if curr.segName==depElement[0].name and curr.originalLine==depElement[1]:
				for depNode in nodes:
					if depNode.segName==depElement[3].name and depNode.originalLine== depElement[4]:
						curr.addChild(depNode.newline, depNode)
						depNode.addParent(curr.newline, curr)

	# Upward motions dependency
	for curr in nodes:
		for depElement in depTable2:
			if curr.segName == depElement[0].name and curr.originalLine == depElement[1]:
				for depNode in nodes:
					if depNode.segName == depElement[3].name and depNode.originalLine == depElement[4]:
						curr.addParent(depNode.newline, depNode)
						depNode.addChild(curr.newline, curr)


	# Block sequence dependency
	# branch sequence must be in order
	tmpNode = node(-1, -1, "", "", "")
	for curr in nodes:
		if curr.op in branches.sw_conditional_branch:
			if tmpNode.segName=='':
				tmpNode=curr
			else:
				tmpNode.addChild(curr.newline,curr)
				curr.addParent(tmpNode.newline,tmpNode)
				tmpNode=curr


	# General dependency
	for curr in nodes:

		line = [i.strip(",") for i in curr.inst.replace(',', ' ').split()]
		instruction = line[0]
		srcRegs = []

		# ldi
		if curr.op in instructions_arithmetic.sw_imm_load_arithmetic:
			dstReg = line[1]
			if line[2].find('(') != -1:
				srcRegs.append(line[2].rstrip().split('(')[1][:-1])
			else:
				None
			# True check
			for srcReg in srcRegs:
				if srcReg in write:
					for element in write[srcReg]:
						for temp in nodes:
							if temp.newline == element.newline:
								temp.addChild(curr.newline, curr)
								curr.addParent(temp.newline, temp)

			# Anti check
			if dstReg in read:
				for element in read[dstReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# Update read/ write dict
			for srcReg in srcRegs:
				read[srcReg].append(curr)
			write[dstReg].append(curr)

		# memory load
		elif curr.op in instructions_arithmetic.sw_mem_load_arithmetic:
			dstReg = line[1]
			srcReg1 = line[2].split('(')[0]
			srcReg2 = line[2].rstrip().split('(')[1][:-1]
			srcRegs.append(srcReg2)
			srcRegs.append(srcReg2 + "+" + srcReg1)
			# True check
			for srcReg in srcRegs:
				if srcReg in write:
					for element in write[srcReg]:
						for temp in nodes:
							if temp.newline == element.newline:
								temp.addChild(curr.newline, curr)
								curr.addParent(temp.newline, temp)

			# Anti check
			if dstReg in read:
				for element in read[dstReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# Update read/ write dict
			for srcReg in srcRegs:
				read[srcReg].append(curr)
			write[dstReg].append(curr)

		# memory store
		elif instruction in instructions_arithmetic.sw_mem_store_arithmetic:
			srcReg1 = line[1]
			srcReg2 = line[2].rstrip().split('(')[1][:-1]
			srcRegs.append(srcReg2)
			srcRegs.append(srcReg1)
			dstReg = srcReg2 + "+" + line[2].split('(')[0]
			# True check
			for srcReg in srcRegs:
				if srcReg in write:
					for element in write[srcReg]:
						for temp in nodes:
							if temp.newline == element.newline:
								temp.addChild(curr.newline, curr)
								curr.addParent(temp.newline, temp)

			# Anti check
			if dstReg in read:
				for element in read[dstReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# Update read/ write dict
			for srcReg in srcRegs:
				read[srcReg].append(curr)
			write[dstReg].append(curr)

		# branch zero param
		elif curr.op in instructions_arithmetic.sw_branch_zero_param_arithmetic:
			None

		# branch one param
		elif curr.op in instructions_arithmetic.sw_branch_one_param_arithmetic:
			srcReg=line[1]

			# True check
			if srcReg in write:
				for element in write[srcReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# update read/ write dict
			read[srcReg].append(curr)

		# wfpcr 20201124
		elif curr.op == 'wfpcr':
			srcReg=line[1]

			# True check
			if srcReg in write:
				for element in write[srcReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# update read/ write dict
			read[srcReg].append(curr)

		elif curr.op == 'rfpcr':
			dstReg=line[1]

			# True check
			if dstReg in write:
				for element in write[dstReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# update read/ write dict
			write[dstReg].append(curr)

		# general algorithm
		else:
			# True check
			dstReg = line[-1]
			srcRegs = line[1:-1]
			for srcReg in srcRegs:
				# if srcReg is immediate
				if isImmediate(srcReg):
					None
				else:
					if srcReg in write:
						for element in write[srcReg]:
							for temp in nodes:
								if temp.newline == element.newline:
									temp.addChild(curr.newline, curr)
									curr.addParent(temp.newline, temp)

			# Anti check
			if dstReg in read:
				for element in read[dstReg]:
					for temp in nodes:
						if temp.newline == element.newline:
							temp.addChild(curr.newline, curr)
							curr.addParent(temp.newline, temp)

			# Update read/ write dict
			for srcReg in srcRegs:
				read[srcReg].append(curr)
			write[dstReg].append(curr)

	return nodes


class machine_model_class:
	def __init__(self,init_ALUs_int,init_ALUs_flt,init_ALUs_mem,init_ALUs_Decoder,init_Issue_Width,init_Issue_Cache_Size):
		self.total_ALUs_int = init_ALUs_int
		self.total_ALUS_flt = init_ALUs_flt
		self.total_ALUS_mem = init_ALUs_mem
		self.total_Decoder = init_ALUs_Decoder
		self.Issue_Width=init_Issue_Width
		self.Issue_Cache_Size=init_Issue_Cache_Size
		self.available_ALUs_int = init_ALUs_int
		self.available_ALUs_flt = init_ALUs_flt
		self.available_ALUs_mem = init_ALUs_mem

def push_to_issue_cache(ready,machine_model_instance,issue_cache):
	pushCount = 0
	available_ALUs_int=machine_model_instance.available_ALUs_int
	available_ALUs_flt=machine_model_instance.available_ALUs_flt
	available_ALUs_mem=machine_model_instance.available_ALUs_mem
	backup_ready=[]
	ready_copy=copy.deepcopy(ready)
	while pushCount < machine_model_instance.total_Decoder and ready_copy!=[] and len(issue_cache)<machine_model_instance.Issue_Cache_Size:
		operation = max(ready_copy, key=lambda x: x.latencyPath)
		if operation.op in instructions_arithmetic.sw_ALU_mem_arithmetic:
			if available_ALUs_mem==0:
				backup_ready.append(operation)
				ready_copy.remove(operation)
			else:
				for node in ready:
					if node.newline==operation.newline:
						ready.remove(node)
						break
				ready_copy.remove(operation)
				issue_cache.append(operation)
				pushCount=pushCount+1
				available_ALUs_mem=available_ALUs_mem-1
		elif operation.op in instructions_arithmetic.sw_ALU_int_arithmetic:
			if available_ALUs_int==0:
				backup_ready.append(operation)
				ready_copy.remove(operation)
			else:
				for node in ready:
					if node.newline==operation.newline:
						ready.remove(node)
						break
				ready_copy.remove(operation)
				issue_cache.append(operation)
				pushCount=pushCount+1
				available_ALUs_int=available_ALUs_int-1
		else:
			if available_ALUs_flt==0:
				backup_ready.append(operation)
				ready_copy.remove(operation)
			else:
				for node in ready:
					if node.newline==operation.newline:
						ready.remove(node)
						break
				ready_copy.remove(operation)
				issue_cache.append(operation)
				pushCount=pushCount+1
				available_ALUs_flt=available_ALUs_flt-1
	while backup_ready!=[] and pushCount<machine_model_instance.total_Decoder and len(issue_cache)<machine_model_instance.Issue_Cache_Size:
		issue_cache.append(backup_ready[0])
		for node in ready:
			if node.newline==backup_ready[0].newline:
				ready.remove(node)
				break
		backup_ready.remove(backup_ready[0])
		pushCount=pushCount+1


def activation(issue_cache,machine_model_instance):
	lunch = 0
	newActive = []
	while lunch < machine_model_instance.Issue_Width:
		if issue_cache==[]:
			break
		if machine_model_instance.available_ALUs_int==0 and machine_model_instance.available_ALUs_flt==0 \
				and machine_model_instance.available_ALUs_mem==0: # no ALU available
			break
		operation = max(issue_cache, key=lambda x: x.latencyPath)
		issue_cache.remove(operation)

		if operation.op in instructions_arithmetic.sw_ALU_mem_arithmetic:
			#print 'mem:',operation.op
			if machine_model_instance.available_ALUs_mem > 0:
				machine_model_instance.available_ALUs_mem=machine_model_instance.available_ALUs_mem-1
				newActive.append(operation)
				lunch=lunch+1
		elif operation.op in instructions_arithmetic.sw_ALU_int_arithmetic:
			#print 'int:',operation.op
			if machine_model_instance.available_ALUs_int > 0:
				machine_model_instance.available_ALUs_int=machine_model_instance.available_ALUs_int-1
				newActive.append(operation)
				lunch=lunch+1
		else: #flt
			#print 'flt:',operation.op
			if machine_model_instance.available_ALUs_flt > 0:
				machine_model_instance.available_ALUs_flt =machine_model_instance.available_ALUs_flt-1
				newActive.append(operation)
				lunch=lunch+1
	return newActive

def recycle(operation,machine_model_instance):
	if operation.op in instructions_arithmetic.sw_ALU_mem_arithmetic:
		machine_model_instance.available_ALUs_mem = machine_model_instance.available_ALUs_mem + 1
	elif operation.op in instructions_arithmetic.sw_ALU_int_arithmetic:
		machine_model_instance.available_ALUs_int = machine_model_instance.available_ALUs_int + 1
	else:  # flt
		machine_model_instance.available_ALUs_flt = machine_model_instance.available_ALUs_flt + 1

def activation_origin(issue_cache,machine_model_instance):
	lunch = 0
	newActive = []
	ready=[]
	while lunch < machine_model_instance.Issue_Width:
		if issue_cache==[]:
			break
		if machine_model_instance.available_ALUs_int==0 and machine_model_instance.available_ALUs_flt==0 \
				and machine_model_instance.available_ALUs_mem==0:
			break
		operation = max(issue_cache, key=lambda x: x.latencyPath)
		issue_cache.remove(operation)

		if operation.op in instructions_arithmetic.sw_ALU_mem_arithmetic:
			#print 'mem:',operation.op
			if machine_model_instance.available_ALUs_mem > 0:
				machine_model_instance.available_ALUs_mem=machine_model_instance.available_ALUs_mem-1
				newActive.append(operation)
				lunch=lunch+1
		elif operation.op in instructions_arithmetic.sw_ALU_int_arithmetic:
			#print 'int:',operation.op
			if machine_model_instance.available_ALUs_int > 0:
				machine_model_instance.available_ALUs_int=machine_model_instance.available_ALUs_int-1
				newActive.append(operation)
				lunch=lunch+1
		else: #flt
			#print 'flt:',operation.op
			if machine_model_instance.available_ALUs_flt > 0:
				machine_model_instance.available_ALUs_flt =machine_model_instance.available_ALUs_flt-1
				newActive.append(operation)
				lunch=lunch+1
	return newActive

def push_to_issue_cache_origin(inst_list,machine_model_instance,issue_cache): # Decode 4 instructions to issue cache
	pushCount = 0
	while pushCount < machine_model_instance.total_Decoder and inst_list!=[] and len(issue_cache)<machine_model_instance.Issue_Cache_Size:
		operation = inst_list[0]
		inst_list.remove(operation)
		issue_cache.append(operation)
		pushCount=pushCount+1
	#return issue_cache

def ideal_origin_cycle(superBlock,depGraph):
	#depGraph = countLatencies(depGraph)
	machine_model_instance = machine_model_class(machine_model.Units['ALUs_int'],
												 machine_model.Units['ALUs_flt'],
												 machine_model.Units['ALUs_mem'],
												 machine_model.Units['Decoders'],
												 machine_model.Units['Issue_Width'],
												 machine_model.Units['Issue_Cache_Size'],
												 )
	schedule = {}
	done_newline = set()
	done =[]

	cycle = 0
	ready = []
	inst_list=[]
	nodes = []
	newLineNumber = 0
	for elem in superBlock:
		segName = elem[0]
		originalLineNumber = elem[1]
		instruction = elem[2]
		line = [i.strip(",") for i in instruction.replace(',', ' ').split()]
		op = line[0]
		nodes.append(node(newLineNumber, originalLineNumber, op, instruction, segName))
		newLineNumber = newLineNumber + 1

	for n in nodes:
		for j in depGraph:
			if n.newline==j.newline:
				inst_list.append(j)


	active = []
	issue_cache = []
	push_to_issue_cache_origin(inst_list, machine_model_instance, issue_cache)
	for i in depGraph:
		for j in issue_cache:
			if i.parents == {} and i.newline==j.newline:
				ready.append(i)
				issue_cache.remove(j)
	while ready != [] or active != []:
		if ready != []:
			newActive = activation_origin(copy.deepcopy(ready), machine_model_instance)
			for operation in newActive:
				for tmp in ready:
					if tmp.newline == operation.newline:
						ready.remove(tmp)
				schedule[operation.newline] = cycle
				active.append(operation)

		cycle = cycle + 1

		active_removelist = []
		for op in active:
			if schedule[op.newline] + latency.sw[op.op] <= cycle:
				recycle(op, machine_model_instance)
				active_removelist.append(op)
				done_newline.add(op.newline)
				done.append(op)

		for element in active_removelist:
			active.remove(element)
		push_to_issue_cache_origin(inst_list, machine_model_instance, issue_cache)
		for op in issue_cache:
			isReady = True
			for key, parent in op.parents.items():
				if parent.newline not in done_newline:
					isReady = False
			if isReady:
				ready.append(op)
				issue_cache.remove(op)

	f = open('done/' + cycleFileName.split('_')[0] + "_cycle.txt", 'a+')
	f.writelines('time_origin:'+str(cycle))
	f.close()


## longest latency-weighted path to root
def a(depGraph):
	depGraph = countLatencies(depGraph)

	outStr=''
	for node in depGraph:
		for child in node.children:
				for node2 in depGraph:
					if (child==node2.newline):
						childName=node2.newline+1
						outStr=outStr+str(node.newline+1)+"->"+str(childName)+" [label="+str(latency.sw[node.op])+"]"+\
							   str(node.newline+1)+"[shape=circle,label="+str(node.newline+1)+"] "+\
								str(childName) + "[shape=circle,label=" + str(node2.newline+1) + "];"

	graph = pdp.graph_from_dot_data('digraph demo1{'+outStr+' }')
	graph.write_jpg('output/7/'+cycleFileName.split('_')[0] + "_DDG.jpg")



	machine_model_instance=machine_model_class(machine_model.Units['ALUs_int'],
											   machine_model.Units['ALUs_flt'],
											   machine_model.Units['ALUs_mem'],
											   machine_model.Units['Decoders'],
											   machine_model.Units['Issue_Width'],
											   machine_model.Units['Issue_Cache_Size'],
											   )

	schedule = {}
	done = set()

	cycle = 0
	ready = []
	for i in depGraph:
		if i.parents == {}:
			ready.append(i)

	active = []
	issue_cache = []
	push_to_issue_cache(ready,machine_model_instance,issue_cache)
	while issue_cache != [] or active != []:
		if issue_cache != []:
			newActive=activation(copy.deepcopy(issue_cache),machine_model_instance)
			for operation in newActive:
				for tmp in issue_cache:
					if tmp.newline== operation.newline:
						issue_cache.remove(tmp)
				schedule[operation.newline] = cycle
				active.append(operation)
			
		cycle = cycle + 1

		active_removelist=[]
		for op in active:
			if schedule[op.newline] + latency.sw[op.op] <= cycle:
				recycle(op,machine_model_instance)
				active_removelist.append(op)
				done.add(op.newline)

				for line, child in op.children.items():
					isReady = True
					for key, parent in child.parents.items():
						if parent.newline not in done:
							isReady = False
					if isReady:
						ready.append(child)
		for element in active_removelist:
			active.remove(element)
		push_to_issue_cache(ready,machine_model_instance,issue_cache)
	f = open('done/' + cycleFileName.split('_')[0] + "_cycle.txt", 'w')
	f.writelines('time_scheduled:'+str(cycle)+'\n')
	f.close()


	output = ""
	while schedule != {}:
		text = min(schedule, key=schedule.get)
		for temp in depGraph:
			if temp.newline==text:
				output=output + temp.inst+';'
				break
		del schedule[text]
		
	return output

def countLatencies(graph):

	bottom = []
	for i in graph:
		if i.children == {}:
			bottom.append(i)

	for bot in bottom:
		graph[graph.index(bot)].latencyPath = latency.sw[graph[graph.index(bot)].op]
		stack = [graph[graph.index(bot)].newline]
		while stack != []:
			line = stack.pop(0)
			lat = graph[line].latencyPath
			for parentLine in graph[line].parents:
				newParentLat = lat + latency.sw[graph[parentLine].op]
				if graph[parentLine].latencyPath <  newParentLat:
					graph[parentLine].latencyPath =  newParentLat
				stack.append(parentLine)
		
	return graph

## Highest latency instruction
def b(depGraph):

	schedule = {}
	done = set()
	
	cycle = 0
	ready = []
	for i in depGraph:
		if i.parents == {}:
			ready.append(i)
			
	active = []
	
	while ready != [] or active != []:
		if ready != []:
		
			# Remove highest priority
			operation = max(ready, key=lambda x:latency.sw[x.inst])
			ready.remove(operation)
			
			schedule[operation.line] = cycle
			active.append(operation)
			
		cycle = cycle + 1
		  
		for op in active:
			if schedule[op.line] + latency.sw[op.inst] <= cycle:
				active.remove(op)
				done.add(op.line)

				for line, child in op.children.items():
					# Check if child is ready by checking if all parents are done
					isReady = True
					for key, parent in child.parents.items():
						if parent.line not in done:
							isReady = False
					if isReady:
						ready.append(child)
						
	## Create output text from schedule
	output = ""
	while schedule != {}:
		text = min(schedule, key=schedule.get)
		output = output + depGraph[text].originalText
		del schedule[text]
		
	return output

def c(depGraph):
	
	depGraph = countDescendants(depGraph)
	schedule = {}
	done = set()
	
	cycle = 0
	ready = []
	for i in depGraph:
		if i.parents == {}:
			ready.append(i)
			
	active = []
	
	while ready != [] or active != []:
		if ready != []:
		
			# Remove highest priority
			operation = max(ready, key=lambda x:x.latencyPath)
			ready.remove(operation)
			
			schedule[operation.line] = cycle
			active.append(operation)
			
		cycle = cycle + 1
		  
		for op in active:
			if schedule[op.line] + latency.sw[op.inst] <= cycle:
				active.remove(op)
				done.add(op.line)

				for line, child in op.children.items():
					# Check if child is ready by checking if all parents are done
					isReady = True
					for key, parent in child.parents.items():
						if parent.line not in done:
							isReady = False
					if isReady:
						ready.append(child)
						
	## Create output text from schedule
	output = ""
	while schedule != {}:
		text = min(schedule, key=schedule.get)
		output = output + depGraph[text].originalText
		del schedule[text]
		
	return output
	
def countDescendants(graph):
	bottom = []
	for i in graph:
		if i.children == {}:
			bottom.append(i)

	for bot in bottom:
		graph[graph.index(bot)].latencyPath = 0
		stack = [graph[graph.index(bot)].line]
		while stack != []:
			line = stack.pop(0)
			lat = graph[line].latencyPath
			for parentLine in graph[line].parents:
				graph[parentLine].latencyPath = graph[parentLine].latencyPath + lat + 1
				stack.append(parentLine)
			
		return graph

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