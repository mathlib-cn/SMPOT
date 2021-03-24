# 2020/12/19 by Typhoon
# encoding: utf-8
# One-key Execution
# python [-a/-b/-c] [-a/-b/-c/-x] [assembly]
# python interpreter : Python v2.7 with PyCharm 2020.3.4 (Community Edition)
# The first parameter sets the schedule priority of trace scheduler,it only works for the hot path(trace).
# The sceond parameter sets the schedule priority of list scheduler,it only works for the side paths.
# The last parameter should be the name of input,and the file must be located in '/input'.

# -a : longest latency-weighted path to root
# -b : highest latency instruction
# -c : highest descendant latency-weighted
# -x : close the scheduler for side paths

# ATTENTION:
# For now the first parameter you can only use -a and the second one you can only use -x,like "python -a -x sin.S".
# Other parameters will be supported later.

import os
import sys
import time

strategy_TS = sys.argv[1]
strategy_GS = sys.argv[2]
INFILE = sys.argv[3]
OUTFILE = INFILE.split('.')[0] + '_scheduled.S'

def init():
    path = path = os.getcwd()+'/output'
    for i in os.listdir(path):
        path_file = os.path.join(path, i)
        if os.path.isfile(path_file):
            os.remove(path_file)
        else:
            for f in os.listdir(path_file):
                path_file2 = os.path.join(path_file, f)
                if os.path.isfile(path_file2):
                    os.remove(path_file2)


def main():
    print '*** READY TO LUNCH ***'
    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    path = os.getcwd()

    print '\nINITIALIZING...'
    init()
    print 'DONE'

    print '\nSTEP #1 : PREPROCESS'
    print 'Wating ...'
    os.system('python 1_preprocess.py '+INFILE)
    print 'STEP #1 FINISHED'

    print '\nSTEP #2 : STANDARDIZE'
    print 'Wating ...'
    os.system('python 2_standardize.py '+INFILE.split('.')[0]+'.S')
    print 'STEP #2 FINISHED'

    print '\nSTEP #3 : DRAW_CFG'
    print 'Wating ...'
    os.system('python 3_draw_CFG.py '+'output/0/'+INFILE.split('.')[0]+'_std.S '+INFILE.split('.')[0])
    print 'STEP #3 FINISHED'

    print '\nSTEP #4 : INIT_EXCEPECTS'
    print 'Wating ...'
    os.system('python 4_init_expects.py '+'output/0/' +INFILE.split('.')[0]+'_rawdata.txt '
              + 'input/'+INFILE.split('.')[0]+'_expects.txt '+INFILE.split('.')[0])
    print 'STEP #4 FINISHED'

    print '\nSTEP #5 : TAIL_DUPLICATION'
    print 'Wating ...'
    os.system('python 5_tail_duplication.py '+'output/0/'+INFILE.split('.')[0]+'.txt '+'td_'+INFILE.split('.')[0])
    print 'STEP #5 FINISHED'

    print '\nSTEP #6 : COMBINE_BLOCKS'
    print 'Wating ...'
    os.system('python 6_combine_blocks.py '+'output/0/td_'+INFILE.split('.')[0]+'.txt '
              +'output/0/td_'+INFILE.split('.')[0] + '_trace.txt '+ 'cb_'+INFILE.split('.')[0])
    print 'STEP #6 FINISHED'

    print '\nSTEP #7 : SCHEDULER'
    print 'Wating ...'
    os.system('python 7_scheduler.py '+strategy_TS+' '+strategy_GS+' '+
              'output/0/cb_'+INFILE.split('.')[0]+'.txt '+'output/0/cb_'+INFILE.split('.')[0] + '_trace.txt '
              + INFILE.split('.')[0]+ '_scheduled')
    print 'STEP #7 FINISHED'

    print '\nSTEP #8 : REGROUP'
    print 'Wating ...'
    os.system('python 8_regroup.py '+INFILE.split('.')[0])
    print 'STEP #8 FINISHED'

    print '\nSTEP #9 : ASSEMBLE'
    print 'Wating ...'
    os.system('python 9_assemble.py '+INFILE.split('.')[0])
    print 'STEP #9 FINISHED'

    print '\n*** TRACE SCHEDULING DONE ***'
    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

if __name__ == "__main__":
    main()