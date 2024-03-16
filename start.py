import os
from pyautogui import confirm

version='PMSL V1.0.0'

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
    return reline

start_List = readtxt('start_Num.txt')
start_Num = str(start_List[1])

if start_Num == '0':
    one=r'serverdown'
    os.chdir(one)
    try:
        os.system('begin.bat')
    except:
        back = confirm(text="ERROR:514.初次启动服务器时发生错误,可能是begin.bat未能成功创建.",title=version,buttons=['继续'])
else:
    path = '.ServerFile/'+start_Num
    one= r''+path
    os.chdir(one)
    try:
        os.system('begin.bat')
    except:
        back = confirm(text="ERROR:514.1.启动"+start_Num+"服务器时发生错误.",title=version,buttons=['继续'])