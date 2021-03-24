# 2020/12/19 by Typhoon
# encoding: utf-8
# Assemble header and footer of the file with the code section.

import sys
import shutil

INFILE = sys.argv[1]
Header = INFILE + '_header.S'
Footer = INFILE + '_footer.S'
Scheduled = INFILE + '_scheduled.S'

def main():
    in_file_header = open('output/0/'+Header, 'r')
    in_file_footer = open('output/0/'+Footer, 'r')
    in_file_scheduled = open('output/0/'+Scheduled, 'r')
    out_file = open('output/9/d_'+INFILE+'.S','w')

    in_head_lines = in_file_header.readlines()
    for line in xrange(len(in_head_lines)):
        code = in_head_lines[line]
        if code!='':
            out_file.writelines(code)

    in_scheduled_lines = in_file_scheduled.readlines()
    for line in xrange(len(in_scheduled_lines)):
        code = in_scheduled_lines[line]
        if code!='':
            out_file.writelines(code)

    in_footer_lines = in_file_footer.readlines()
    for line in xrange(len(in_footer_lines)):
        code = in_footer_lines[line]
        if code!='':
            out_file.writelines(code)

    in_file_header.close()
    in_file_scheduled.close()
    in_file_footer.close()
    out_file.close()

    shutil.copy('output/9/d_'+INFILE+'.S','output/d_'+INFILE+'.S')
    shutil.copy('output/9/d_'+INFILE+'.S','done/d_'+INFILE+'.S')


if __name__ == "__main__":
    main()




