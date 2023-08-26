import os
from subprocess import getoutput
from pyautogui import confirm,prompt

version='PMS V1.0.0'

def writing(filepath,text,mode): #Str Str/list Int #写入文件
    opfile=open(str(filepath),'w+')
    if int(mode) == 0: #直接写入
        opfile.write(str(text))
    else: #逐行写入
        for i in text:
            opfile.write(str(i)+'\n')
    opfile.close


def readtxt(filepath): #读取文件
    read=open(str(filepath),'r')
    line=read.readlines()
    read.close
    reline=[]
    for anline in line:
        anline=anline.replace('\n','')
        reline.append(anline)
    #print(reline)######################测试语句
    return reline

def ui(list): #UI列表封装
    a=1

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

def versionset(): #服务器版本设置
    a=readtxt('data/set/version.txt')
    b=readtxt('data/ver.txt')
    back = prompt(text='输入你想开设的服务器版本.',title=version,default=a[0])
    if back ==  None:
        back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
    elif back not in b:
        back = confirm(text="你的输入不在支持范围内,此次输入将不做保存.",title=version,buttons=['继续'])
    else:
        writing('data/set/version.txt',str(back),0)
        back = confirm(text="已保存于data/set/version.txt",title=version,buttons=['继续'])