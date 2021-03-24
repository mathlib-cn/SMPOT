# 2020/12/19 by Typhoon
# encoding: utf-8
# Standardize Source Files
# 1.Clear comments.
# 2.Standardized format and ensure all the instructions are formatted like '\tOPCode OPERAND1,OPERAND2,OPERAND3'.
# 3.Change special character like '$' to 'dor' as '$' is a key word of pydotplus.
# 4.Map all registers to ABI names.
# 5.Clear dead instructions.

import sys
import copy
import shutil
from utility import reg_map
from utility import branches

INFILE = sys.argv[1]
OUTFILETMP = INFILE.split('.')[0] + '_tmp.S'
OUTFILE = INFILE.split('.')[0] + '_std.S'

def main():
    in_file = open('output/0/'+INFILE.split('.')[0]+'_ppd.S', 'r')
    sw = in_file.readlines()
    in_file.close()
    out_file = open('output/2/'+OUTFILE, 'w')
    out_file_tmp = open('output/2/'+OUTFILETMP, 'w')

    sw_codes = copy.deepcopy(sw)

    # clear comments
    # attention not to delete #ifdef/#endif
    for line in xrange(len(sw_codes)):
        code = sw_codes[line].rstrip().split('#')
        newline = code[0].rstrip()
        if newline=='': # the whole line is comment
            continue
        if newline.find(':') == -1:
            if newline.find('beq')!=-1:
                None

            instruction = [i.strip(",") for i in newline.replace(',', ' ').split()]
            newline='\t'+instruction[0]+' '
            for reg in instruction[1:]:
                regIndex=instruction.index(reg)-1
                if reg.find('(') != -1:
                    imm=reg.split('(')[0]
                    regTmp=reg.split('(')[1][:-1]
                    if regTmp in reg_map.reg_map:
                        regTmp=reg_map.reg_map[regTmp]
                    newline=newline+imm+'('+regTmp+'),'
                else:
                    if reg in reg_map.reg_map:
                        reg=reg_map.reg_map[reg]
                    if instruction[0] in branches.sw_unconditional_jump :
                        if branches.sw_unconditional_jump[instruction[0]]==str(regIndex):
                            reg = reg.replace('$', '_dor_')
                    elif instruction[0] in branches.sw_conditional_branch:
                        if branches.sw_conditional_branch[instruction[0]]==str(regIndex) :
                            reg = reg.replace('$', '_dor_')
                    else:
                        None
                    newline = newline + reg +','
            newline=newline[:-1]
        elif newline.split(':')[1]!='':
            segName=newline.split(':')[0].replace('$','_dor_')
            newline=newline.split(':')[1]
            instruction = [i.strip(",") for i in newline.replace(',', ' ').split()]
            newline='\t'+instruction[0]+' '
            for reg in instruction[1:]:
                if reg.find('(') != -1:
                    imm=reg.split('(')[0]
                    regTmp=reg.split('(')[1][:-1]
                    if regTmp in reg_map.reg_map:
                        regTmp=reg_map.reg_map[regTmp]
                    newline=newline+imm+'('+regTmp+'),'
                else:
                    if reg in reg_map.reg_map:
                        reg=reg_map.reg_map[reg]
                    if instruction[0] in branches.sw_unconditional_jump:
                        if branches.sw_unconditional_jump[instruction[0]] == str(regIndex):
                            reg = reg.replace('$', '_dor_')
                    elif instruction[0] in branches.sw_conditional_branch:
                        if branches.sw_conditional_branch[instruction[0]] == str(regIndex):
                            reg = reg.replace('$', '_dor_')
                    else:
                        None
                    newline = newline + reg +','
            newline=segName+':\n'+newline[:-1]
        else:
            newline=newline.replace('$','_dor_')

        out_file_tmp.write(newline + '\n')
    out_file_tmp.close()

    in_file = open('output/2/'+OUTFILETMP, 'r')
    sw = in_file.readlines()
    in_file.close()
    sw_codes = copy.deepcopy(sw)
    # clear unnecessary instructions after unconditional branches and ret
    # these are dead instructions which will never be executed
    removeTrig = False
    for line in xrange(len(sw_codes)):
        newline = code = sw_codes[line].rstrip()
        if newline.find(':') != -1:
            removeTrig = False
        if removeTrig:
            continue
        instruction = [i.strip(",") for i in newline.replace(',', ' ').split()]
        if instruction[0] in branches.sw_unconditional_jump or instruction[0] == 'ret':
            removeTrig = True

        out_file.write(newline + '\n')
    out_file.close()

    shutil.copy('output/2/'+INFILE.split('.')[0] + '_std.S','output/0/'+INFILE.split('.')[0] + '_std.S')


if __name__ == "__main__":
    main()