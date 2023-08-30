
'''
更改程序设置专用模块，在主程序中使用 import data.function.setting 来导入.
此模块需要补充.

'''


version='PMS V1.0.0'


#  ==================================
#             IMPORT LIST
#  ==================================

from subprocess import getoutput
from pyautogui import confirm

def writing(filepath,text,mode): #Str Str/list Int #写入文件
    opfile=open(str(filepath),'w+')
    if int(mode) == 0: #直接写入
        opfile.write(str(text))
    else: #逐行写入
        for i in text:
            opfile.write(str(i)+'\n')
    opfile.close


#  ==================================
#            FUNCTION LIST
#  ==================================



'''
testofset 函数

用于检查使用者的Java环境是否正确配置,使用者需要有Java系统变量才能通过

'''

def testofset(): #可行性检验
    a=getoutput('java')
    b=getoutput('javac')
    c=getoutput('java --version')
    print(a+'\n'+b+'\n'+c+'\n')
    if '--help' in a and '--help' in b and 'Java(TM)' in c:
        back = confirm(text="你的各方面配置似乎无误!现在你可以开始开设一个属于你自己的服务器了!"+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'",title=version,buttons=['继续'])
        writing('data/set/testofset.txt','1',0)
    elif '不是内部或外部命令，也不是可运行的程序' in a or '不是内部或外部命令，也不是可运行的程序' in b or 'Error' in c:
        writing('data/set/testofset.txt','2',0)
        back = confirm(text="检测到你的Java配置出现错误,请检查配置."+'\n'+'建议重新配置Java,记得配置时勾选设置系统路径'+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])