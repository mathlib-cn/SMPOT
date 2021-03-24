# 2020/12/19 by Typhoon
# encoding: utf-8

import copy
from utility import latency
from utility import branches
import collections
from utility import instructions_arithmetic
from utility import machine_model

cycleFileName=''

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
def find_dependence(instruction, tracePoint, trace, blocks):
	abc, versTmp = findLoop(blocks)


	currentNode=tracePoint


	if len(tracePoint.childrenNames)==0 :
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
				for index,split in enumerate(instSplits):
					ind=split.find('(')
					if ind!=-1:
						instSplits[index]=split[ind+1:-1]
				op = instSplits[0]
				if op == 'ret' or op =='unop':
					continue
				if instructionSplit[0] in instructions_arithmetic.sw_mem_store_arithmetic: # memory dependency
					if op in instructions_arithmetic.sw_mem_load_arithmetic:
						if raw_wreg == wReg:
							return 1,currentNode,line,inst
						else:
							continue
					else:
						continue

				else:	#register dependency
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

def superblock_scheduling(blocks,trace,strategy,outputName):
	global cycleFileName
	cycleFileName=outputName

	depTable1=check_downward_motion(blocks,trace)
	depTable2=check_upward_motion(blocks,trace)

	return constrained_basic_block_scheduler(blocks,trace,depTable1,depTable2,strategy)

# Avoid code compensation on motion above a split
def check_upward_motion(blocks,trace):
	depTable=[]	#element is a list like [instBlock,line,inst,splitBlockName,depBlock,depLine,depInst]

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
						depInst=''
						currentIndex=trace.index(block.name)-1
						currentNodeName=trace[currentIndex]
						for blocktmp2 in blocks:
							if blocktmp2.name==currentNodeName:
								currentNode=blocktmp2
						while retVal==0 :
							retVal,depBlock,depLine,depInst=find_dependence(inst,currentNode,trace,blocks)
							if retVal==1:	#must have two children and the last instruction must be a branch
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
									break	#its the end of the trace
	return depTable

# Avoid code compensation on motion below a split
def check_downward_motion(blocks,trace):
	depTable=[]	#element is a list like [instBlock,line,inst,splitBlockName,depBlock,depLine,depInst]

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
						depInst=''
						currentNode=block
						while retVal==0 :
							if inst.find('$f13')!=-1:
								None
							retVal,depBlock,depLine,depInst=find_dependence(inst,currentNode,trace,blocks)
							if retVal==1:	#must have two children and the last instruction must be a branch
								#depTable.append([block,key,inst,currentNode,depBlock,depLine,depInst])
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
									break	#its the end point of the trace
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
		ideal_origin_cycle(superBlock, depGraph)
	elif strategy == "-b":
		None
		#output = b(depGraph)
	elif strategy == "-c":
		None
		#output = c(depGraph)
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
		# Strip commas and split
		segName=elem[0]
		originalLineNumber=elem[1]
		instruction=elem[2]
		line = [i.strip(",") for i in instruction.replace(',',' ').split()]
		#print line
		op = line[0]
		# Create node of dependency graph
		nodes.append(node(newLineNumber, originalLineNumber, op , instruction ,segName))
		newLineNumber=newLineNumber+1

	currentBlockName = ''
	currentBlockIndex = -1


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

		# Strip commas and split
		line = [i.strip(",") for i in curr.inst.replace(',', ' ').split()]
		instruction = line[0]
		dstReg = ''
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

		# rfpcr 20201124
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
	while pushCount < machine_model_instance.total_Decoder and ready!=[] and len(issue_cache)<60:
		operation = max(ready, key=lambda x: x.latencyPath)
		ready.remove(operation)
		issue_cache.append(operation)
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

def allocation_method(ready,depGraph):
	if ready==[]:
		return None
	op_class0_counter=0	 #Pipeline0
	op_class1_counter=0	 #Pipeline1
	op_class2_counter=0	 #Pipeline0/1
	ready_class0=[]
	ready_class1=[]
	ready_class2=[]
	issue_pair=[]

	for operation in ready:
		if operation.op in instructions_arithmetic.E.keys():
			op_class2_counter+=1
			ready_class2.append(operation.newline)
		elif operation.op in instructions_arithmetic.E0.keys():
			op_class0_counter+=1
			ready_class0.append(operation.newline)
		else: #operation.inst in instructions_arithmetic.E1.keys():
			#print operation.op
			op_class1_counter += 1
			ready_class1.append(operation.newline)

	issue_operation_A = max(ready, key=lambda x: x.latencyPath)
	ready.remove(issue_operation_A)
	# if op is ldih  #ldih and ldi are both executed by E
	if ready!=[]:
		issue_operation_b = max(ready, key=lambda x: x.latencyPath)
	else:
		issue_pair.append(issue_operation_A)
		return issue_pair
	flag=True
	while flag and ready!=[]:
		issue_operation_B=issue_operation_b
		if issue_operation_A.newline in ready_class0 and issue_operation_B.newline in ready_class1 or \
				issue_operation_A.newline in ready_class0 and issue_operation_B.newline in ready_class2:
			flag=False
			break
		if issue_operation_A.newline in ready_class1 and issue_operation_B.newline in ready_class0 or \
				issue_operation_A.newline in ready_class1 and issue_operation_B.newline in ready_class2:
			flag=False
			break
		if issue_operation_A.newline in ready_class2:
			flag=False
			break
		ready.remove(issue_operation_B)
		if ready==[]:
			break
		issue_operation_b = max(ready, key=lambda x: x.latencyPath)
	if flag==True:
		#issue_operation_B=issue_operation_b
		#2 inst use same pipeline
		issue_pair.append(issue_operation_A)
		return issue_pair

	issue_pair.append(issue_operation_A)
	issue_pair.append(issue_operation_B)
	return issue_pair

def ideal_origin_cycle(superBlock,depGraph):

	schedule = {}
	done_newline = set()
	done =[]
	ready = []
	for i in depGraph:
		if i.parents == {}:
			ready.append(i)

	cycle = 0
	inst_list=[]
	nodes = []
	newLineNumber = 0
	for elem in superBlock:
		# Strip commas and split
		segName = elem[0]
		originalLineNumber = elem[1]
		instruction = elem[2]
		line = [i.strip(",") for i in instruction.replace(',', ' ').split()]
		# print line
		op = line[0]
		# Create node of dependency graph
		nodes.append(node(newLineNumber, originalLineNumber, op, instruction, segName))
		newLineNumber = newLineNumber + 1

	for n in nodes:
		for j in depGraph:
			if n.newline==j.newline:
				inst_list.append(j)

	p0=1
	p1=1
	active = []

	while inst_list != []:
		flag=False
		opB=None
		if len(inst_list)>1:
			current_inst_A=inst_list[0]
			for op in ready:
				if op.newline==current_inst_A.newline:
					ready.remove(op)
					done.append(op.newline)
					break

			for op in ready:
				if op.newline==inst_list[1].newline:
					current_inst_B=inst_list[1]
					opB=op
					flag=True
					break
			for line, child in current_inst_A.children.items():
				# Check if child is ready by checking if all parents are done
				isReady = True
				for key, parent in child.parents.items():
					if parent.newline not in done:
						isReady = False
				if isReady:
					ready.append(child)


			if flag:
				if current_inst_A.op in instructions_arithmetic.E0.keys() and current_inst_B.op in instructions_arithmetic.E0.keys():
					inst_list.remove(current_inst_A)
					schedule[current_inst_A.newline]=cycle
					#print 'E0:'+current_inst_A.op+' E0:'+current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E1.keys() and current_inst_B.op in instructions_arithmetic.E1.keys():
					inst_list.remove(current_inst_A)
					schedule[current_inst_A.newline]=cycle
					#print 'E1:'+current_inst_A.op+' E1:'+current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E0.keys() and current_inst_B.op in instructions_arithmetic.E1.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline] = cycle
					schedule[current_inst_B.newline] = cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E0:' + current_inst_A.op + ' E1:' + current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E1.keys() and current_inst_B.op in instructions_arithmetic.E0.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline]=cycle
					schedule[current_inst_B.newline]=cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E1:'+current_inst_A.op+' E0:'+current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E0.keys() and current_inst_B.op in instructions_arithmetic.E.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline] = cycle
					schedule[current_inst_B.newline] = cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E0:' + current_inst_A.op + ' E:' + current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E1.keys() and current_inst_B.op in instructions_arithmetic.E.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline] = cycle
					schedule[current_inst_B.newline] = cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E1:' + current_inst_A.op + ' E:' + current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E.keys() and current_inst_B.op in instructions_arithmetic.E0.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline] = cycle
					schedule[current_inst_B.newline] = cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E:' + current_inst_A.op + ' E0:' + current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E.keys() and current_inst_B.op in instructions_arithmetic.E1.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline] = cycle
					schedule[current_inst_B.newline] = cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E:' + current_inst_A.op + ' E1:' + current_inst_B.op
				elif current_inst_A.op in instructions_arithmetic.E.keys() and current_inst_B.op in instructions_arithmetic.E.keys():
					inst_list.remove(current_inst_A)
					inst_list.remove(current_inst_B)
					schedule[current_inst_A.newline] = cycle
					schedule[current_inst_B.newline] = cycle
					ready.remove(opB)
					done.append(opB.newline)
					for line, child in current_inst_B.children.items():
						# Check if child is ready by checking if all parents are done
						isReady = True
						for key, parent in child.parents.items():
							if parent.newline not in done:
								isReady = False
						if isReady:
							ready.append(child)
					#print 'E:' + current_inst_A.op + ' E:' + current_inst_B.op
				else:
					None
					#print 'Unknow:' + current_inst_A.op + ' Unknow:' + current_inst_B.op
			else:
				current_inst_A = inst_list[0]
				inst_list.remove(current_inst_A)
				schedule[current_inst_A.newline] = cycle
				#print 'single inst:' + current_inst_A.op
		else:
			current_inst_A=inst_list[0]
			inst_list.remove(current_inst_A)
			schedule[current_inst_A.newline] = cycle
			#print 'last single inst:'+current_inst_A.op

		cycle = cycle + 1

	f = open('done/' + cycleFileName.split('_')[0] + "_cycle.txt", 'a+')
	f.writelines('time_origin:'+str(cycle))
	f.close()

## longest latency-weighted path to root
def a(depGraph):
	depGraph = countLatencies(depGraph)

	machine_model_instance=machine_model_class(machine_model.Units['ALUs_int'],
											   machine_model.Units['ALUs_flt'],
											   machine_model.Units['ALUs_mem'],
											   machine_model.Units['Decoders'],
											   machine_model.Units['Issue_Width'],
											   machine_model.Units['Issue_Cache_Size'],
											   )

	schedule = []
	done = set()
	schedule2={}
	cycle = 0
	ready = []
	for i in depGraph:
		if i.parents == {}:
			ready.append(i)

	while ready!=[]:
		issue_pair=allocation_method(copy.deepcopy(ready),copy.deepcopy(depGraph))
		if len(done)!=len(schedule):
			None
		for issue_instruction in issue_pair:
			schedule.append(issue_instruction)
			schedule2[issue_instruction.newline]=cycle
			done.add(issue_instruction.newline)
			for op in ready:
				if op.newline==issue_instruction.newline:
					ready.remove(op)
			for line, child in issue_instruction.children.items():
				# Check if child is ready by checking if all parents are done
				isReady = True
				for key, parent in child.parents.items():
					if parent.newline not in done:
						isReady = False
				if isReady:
					ready.append(child)
		cycle=cycle+1
	f = open('done/' + cycleFileName.split('_')[0] + "_cycle.txt", 'w')
	f.writelines('time_scheduled:'+str(cycle)+'\n')
	f.close()


	output = ""
	for node in schedule:
		for temp in depGraph:
			if temp.newline == node.newline:
				output = output + temp.inst + ';'
				break
	return output

def countLatencies(graph):

	bottom = []
	for i in graph:
		if i.children == {}:
			bottom.append(i)
			#print i.newline,i.inst

	for bot in bottom:
		graph[graph.index(bot)].latencyPath = latency.sw_cg[graph[graph.index(bot)].op]
		#graph[graph.index(bot)].latencyPath = 1 #fully pipelined
		#print graph.index(bot)
		stack = [graph[graph.index(bot)].newline]
		#print 'current bot :',bot.newline,bot.inst,bot.segName
		while stack != []:
			#print stack
			line = stack.pop(0)
			lat = graph[line].latencyPath
			for parentLine in graph[line].parents:
				#parentLine=parent.newline
				newParentLat = lat + latency.sw_cg[graph[parentLine].op]
				#newParentLat = lat + 1 #fully pipelined
				if graph[parentLine].latencyPath <  newParentLat:
					graph[parentLine].latencyPath =  newParentLat
				stack.append(parentLine)
		
	return graph


# find Loops in CFG (find circles in graph)
def findLoop(blocks):
    relationDic = collections.OrderedDict()
    for block in blocks:
        relationDic[block.name] = block.childrenNames
    circles = []
    vertices=[] #save node names in loops
    loopVertices={} #save the backward arcs in loops
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
                    # print(sorted(temp))
                    trig=False # make sure no repetitive loop
                    for circle in circles:
                        if sorted(temp) == sorted(circle) :
                            trig=True
                    if not trig:
                        # print '@',sorted(temp)
                        circles.append(copy.deepcopy(temp))
                        loopVertices[temp[-1]]=temp[0]
                    return
    temp = []
    for key in relationDic:
        temp.append(key)
        recursion(temp)
        temp.remove(key)
    #print 'This CFG has',len(circles),'loops.\n',circles
    for circle in circles:
        for vertex in circle:
            if vertex not in vertices:
                vertices.append(vertex)
    #print backLoop,vertices
    return loopVertices,vertices