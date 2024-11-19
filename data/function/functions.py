import os
from pyautogui import confirm,prompt
from subprocess import getoutput
import tkinter as tk
from tkinter import filedialog

'''
FUNCTION.

ERROR List:
500,001,114,514

'''

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

def writing_find(filepath,text,find):
    read = readtxt(filepath)
    index = read.index(str(find))
    read[(index+1)] = str(text)
    writing(filepath,read,1)

def readtxt_find(filepath,find):
    read = readtxt(filepath)
    index = read.index(str(find))
    get = read[(index+1)]
    return get

version=readtxt('Version.txt')[0]

def testofset(): #可行性检验
    a=getoutput('java')
    b=getoutput('javac')
    c=getoutput('java --version')
    print(a+'\n'+b+'\n'+c+'\n')
    try:
        if '--help' in a and '--help' in b and 'Java(TM)' in c:
            back = confirm(text="你的各方面配置似乎无误!现在你可以开始开设一个属于你自己的服务器了!"+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'",title=version,buttons=['继续'])
            writing_find('data/set_pgm/set_pgm.txt','1','是否完成Java检测(0否1通过2未通过)')
        elif '不是内部或外部命令，也不是可运行的程序' in a or '不是内部或外部命令，也不是可运行的程序' in b or 'Error' in c:
            writing_find('data/set_pgm/set_pgm.txt','2','是否完成Java检测(0否1通过2未通过)')
            back = confirm(text="检测到你的Java配置出现错误,请检查配置."+'\n'+'建议重新配置Java,记得配置时勾选设置系统路径'+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])
        else:
            back = confirm(text="检测时遇到意料之外的返回值,请手动确认java配置是否正常."+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'"
                       +'\n'+"然而出现了未知的错误,因此请自行在cmd中重运行如下命令来检查:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])
    except:
        back = confirm(text="检测时遇到意料之外的错误,请手动确认java配置是否正常."+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'"
                       +'\n'+"然而出现了未知的错误,因此请自行在cmd中重运行如下命令来检查:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])
        
def get_java_version():
    a=getoutput('java --version')
    if 'Java(TM)' in a:
        b = a.splitlines()[0]
        c= b.split(' ')[1]
        d = c.split('.')[0]
    else:
        d = '无'
    
    return d

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
    d=readtxt('data/set/core_version.txt')[0]
    #print(a[0])
    if str(a[0]) == 'Paper' or str(a[0]) == 'Forge':
        back = prompt(text='输入你想开设的服务器核心版本.',title=version,default=str(d))
        if back ==  None:
            back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
        else:
            writing('data/set/core_version.txt',str(back),0)
            back = confirm(text="已保存于data/set/core_version.txt",title=version,buttons=['继续'])
    elif str(a[0]) == 'Fabric':
        back = prompt(text='输入你想要的Fabric Loader Version (Fabric加载器版本).\n一般情况无需修改,默认继续即可.',title=version,default='0.16.9')
        if back ==  None:
            back2 = confirm(text="你关闭了界面,此次输入将不做保存.\n一般情况无需修改,默认继续即可.",title=version,buttons=['继续'])
            d=readtxt('data/set/core_version.txt')
            back = str(d[0])
        else:
            back2 = confirm(text="已保存于data/set/core_version.txt",title=version,buttons=['继续'])

        back1 = prompt(text='输入你想要的Installer Version (Fabric安装器版本).',title=version,default='1.0.1')
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
    if core == 'Spigot':
        back = confirm(text="确定将目标服务器核心设置为Spigot?\n近期Spigot网站访问受限,可能导致无法正常下载核心!",title=version,buttons=['确定','不要'])
    else:
        back = confirm(text="确定将目标服务器核心设置为"+str(core)+"?",title=version,buttons=['确定','不要'])
    if back == '确定':
        writing('data/set/core.txt',str(core),0)
        back = confirm(text="已保存开服核心为"+str(core)+".",title=version,buttons=['继续'])

def ruset(core):
    a=int(readtxt('data/set/ru.txt')[0])
    if core == 1 and a > 1:
        a = a-1
        writing('data/set/ru.txt',str(a),0)
    elif core == 2:
        a = a+1
        writing('data/set/ru.txt',str(a),0)
    elif core == 114514:
        back = prompt(text='输入你想开设的服务器运行内存(输入正整数,单位:G).',title=version,default=str(a))
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

def choose_file():
    window = tk.Tk()
    window.withdraw()
    path = str(filedialog.askopenfilename(title='[替换服务器标示图] 选择一个格式为png的图片. Tip:显示时图片尺寸为215x397.',filetypes=[('图片','.png')]))
    if path == '':
        path = 'None'
    return path


##########################
#  求不规则按键可点击像素,暂未使用
##########################

def point_in_polygon(x, y, poly):
    n = len(poly)
    inside = False
    xinters = 0
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def points_in_irregular_quad(vertices):
    # Find bounding box of the irregular quad
    min_x = min(vertices, key=lambda v: v[0])[0]
    max_x = max(vertices, key=lambda v: v[0])[0]
    min_y = min(vertices, key=lambda v: v[1])[1]
    max_y = max(vertices, key=lambda v: v[1])[1]

    points_inside = []
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if point_in_polygon(x, y, vertices):
                points_inside.append((x, y))

    return points_inside