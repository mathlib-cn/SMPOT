# 2020/12/19 by Typhoon
# encoding: utf-8
# Handle header and footer of the file.

import sys
import copy
import shutil
from utility import reg_map
from utility import branches

INFILE = sys.argv[1]
Header = INFILE.split('.')[0] + '_header.S'
Footer = INFILE.split('.')[0] + '_footer.S'
Preprocessed = INFILE.split('.')[0] + '_ppd.S'

def exclude(code):
    if code.find('.frame')!=-1:
        return ''
    elif code.find('ldgp')!=-1:
        return ''
    elif code.find('exception')!=-1:
        return ''
    elif code.find('ret zero')!=-1:
        return 'ret\n'
    else:
        return code

def main():
    in_file = open('input/'+INFILE, 'r')
    sw = in_file.readlines()
    in_file.close()
    out_file_header = open('output/1/'+Header, 'w')
    out_file_footer = open('output/1/'+Footer, 'w')
    out_file_ppd = open('output/1/'+Preprocessed, 'w')
    CASE = 0
    sw_codes = copy.deepcopy(sw)

    for line in xrange(len(sw_codes)):
        code = sw_codes[line]
        if CASE ==0:
            if code.find('.ent') == -1:
                out_file_header.writelines(code)
            else:
                out_file_header.writelines(code)
                CASE=1  #Footer saved and set CASE=1
        elif CASE == 1:
            if code.find('.end') == -1:
                excludeStr=exclude(code)
                if (excludeStr!=''):
                    out_file_ppd.writelines(excludeStr)
            else:
                out_file_footer.writelines(code)
                CASE=2
        else:
            out_file_footer.writelines(code)

    out_file_header.close()
    out_file_footer.close()
    out_file_ppd.close()

    shutil.copy('input/'+INFILE, 'done/' + INFILE)
    shutil.copy('output/1/' + Header, 'output/0/' + Header)
    shutil.copy('output/1/' + Footer, 'output/0/' + Footer)
    shutil.copy('output/1/' + Preprocessed, 'output/0/' + Preprocessed)


if __name__ == "__main__":
    main()




