import os
from pyautogui import confirm,prompt

'''
FUNCTION.

ERROR List:
500,001,114,514

'''

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
    #print(reline)######################测试语句
    return reline


def versionset(): #服务器版本设置
    a=readtxt('data/set/version.txt')
    b=readtxt('data/ver.txt')
    back = prompt(text='输入你想开设的服务器版本.',title=version,default=a[0])
    if back ==  None:
        back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
    elif back not in b:
        back2 = confirm(text="你的输入不在支持范围内,此次输入将不做保存..?",title=version,buttons=['让我访问!','还是不保存了'])
        if back2 == '让我访问!':
            writing('data/set/version.txt',str(back),0)
            back = confirm(text="已保存于data/set/version.txt",title=version,buttons=['继续'])
    else:
        writing('data/set/version.txt',str(back),0)
        back = confirm(text="已保存于data/set/version.txt",title=version,buttons=['继续'])

def CVset(): #版本设置
    a=readtxt('data/set/core.txt')
    b=readtxt('data/core_ver.txt')
    c=readtxt('data/set/version.txt')
    #print(a[0])
    if str(a[0]) == 'Paper' or str(a[0]) == 'Forge':
        back = prompt(text='输入你想开设的服务器核心版本.',title=version,default='1')
        if back ==  None:
            back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
        else:
            writing('data/set/core_version.txt',str(back),0)
            back = confirm(text="已保存于data/set/core_version.txt",title=version,buttons=['继续'])
    elif str(a[0]) == 'Fabric':
        back = prompt(text='输入你想要的Fabric Loader Version (Fabric加载器版本).',title=version,default='0.14.18')
        if back ==  None:
            back2 = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
            d=readtxt('data/set/core_version.txt')
            back = str(d[0])
        else:
            back2 = confirm(text="已保存于data/set/core_version.txt",title=version,buttons=['继续'])

        back1 = prompt(text='输入你想要的Installer Version (Fabric安装器版本).',title=version,default='0.11.2')
        if back1 ==  None:
            back2 = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
            d=readtxt('data/set/core_version.txt')
            try:
                back1 = str(d[1])
                writing('data/set/core_version.txt',[str(back),str(back1)],1)
            except:
                writing('data/set/core_version.txt',str(back),0)
        else:
            back2 = confirm(text="已保存于data/set/core_version.txt",title=version,buttons=['继续'])
            writing('data/set/core_version.txt',[str(back),str(back1)],1)
    else:
        back = confirm(text="WTF你是怎么触发这个的",title=version,buttons=['继续'])
    


def coreset(core):
    back = confirm(text="确定将目标服务器核心设置为"+str(core)+"?",title=version,buttons=['确定','不要'])
    if back == '确定':
        writing('data/set/core.txt',str(core),0)
        back = confirm(text="已保存开服核心为"+str(core)+".",title=version,buttons=['继续'])

def ruset(core):
    if int(core) != 114514:
        back = confirm(text="确定将服务器运行内存设置为"+str(core)+"?",title=version,buttons=['确定','不要'])
        if back == '确定':
            writing('data/set/ru.txt',str(core),0)
            back = confirm(text="已保存服务器运行内存为"+str(core)+".",title=version,buttons=['继续'])
    else:
        a=readtxt('data/set/ru.txt')
        back = prompt(text='输入你想开设的服务器运行内存(输入正整数,单位:G).',title=version,default=a[0])
        try:
            if back != None:
                back = int(back)
        except:
            back2 = confirm(text="作者在这里专门放了个try语句,只害怕有大聪明把'G'加上,这个只用输入数字即可!",title=version,buttons=['哦哦'])
            back = None
        if back ==  None:
            back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
        elif int(back) >= 12:
            back2 = confirm(text="我的天啊,你真的想要用这么巨大的内存开一个小小的MC服务器?",title=version,buttons=['让我访问!','我放弃'])
            if back2 == '让我访问!':
                writing('data/set/ru.txt',str(back),0)
                back = confirm(text="最有实力的一集.但我还是听你的!已保存于data/set/ru.txt",title=version,buttons=['继续'])
        else:
            writing('data/set/ru.txt',str(back),0)
            back = confirm(text="已保存于data/set/ru.txt",title=version,buttons=['继续'])

def reset_eula():
    eula = readtxt('serverdown/eula.txt')
    a=int(len(eula))
    eula[int(a-1)]='eula=true'
    writing('serverdown/eula.txt',eula,1)

def read_Server():
    try:
        Server = readtxt('.ServerList/ServerList.txt')
    except:
        Server = ['ANSI占位用句']
    Server.remove('ANSI占位用句')
    return Server