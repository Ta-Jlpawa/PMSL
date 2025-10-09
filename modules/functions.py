
import json
import tkinter as tk
from typing import *
from pyautogui import confirm,prompt
from subprocess import getoutput
from tkinter import filedialog

"""
此模块包含了部分程序关键函数
"""

def read_json_get_value(file_path, key):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file).get(key)
    return(data)

def read_json_writing_value(file_path, key, value):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        data[key] = value
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, sort_keys=False, ensure_ascii=False)

def writing(file_path: str, text: Union[str, List[str]], mode: int = 0) -> None: 
    # 写入文件
    opfile = open(file_path, 'w+')
    if mode == 0: 
        # 直接写入
        opfile.write(text)
    else: 
        # 逐行写入
        for i in text:
            opfile.write(str(i)+'\n')
    opfile.close

def readtxt(file_path : str) -> list: 
    # 读取文件
    read = open(file_path, 'r')
    line = read.readlines()
    read.close
    reline = []
    for anline in line:
        anline = anline.replace('\n', '')
        reline.append(anline)
    return reline

def writing_find(file_path: str, text: str, find: str) -> None:
    read = readtxt(file_path)
    index = read.index(find)
    read[(index+1)] = text
    writing(file_path,read,1)

def readtxt_find(file_path: str, find: str, num: int = 1) -> list:
    read = readtxt(file_path)
    index = read.index(find)
    if num == 1:
        get = read[index+1]
    else:
        get = []
        for i in range(1,num + 1):
            get_i = read[index+i]
            get.append(get_i)
    return get

def testofset(version): 
    # 可行性检验
    a = getoutput('java')
    b = getoutput('javac')
    c = getoutput('java --version')
    print(a+'\n'+b+'\n'+c+'\n')
    try:
        if '--help' in a and '--help' in b and 'Java(TM)' in c:
            back = confirm(text="你的各方面配置似乎无误!现在你可以开始开设一个属于你自己的服务器了!"+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'",title=version,buttons=['继续'])
            read_json_writing_value('data/set_pgm/program_settings.json', 'java_test', '1')
        elif '不是内部或外部命令，也不是可运行的程序' in a or '不是内部或外部命令，也不是可运行的程序' in b or 'Error' in c:
            read_json_writing_value('data/set_pgm/program_settings.json', 'java_test', '2')
            back = confirm(text="检测到你的Java配置出现错误,请检查配置."+'\n'+'建议重新配置Java,记得配置时勾选设置系统路径'+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])
        else:
            back = confirm(text="检测时遇到意料之外的返回值,请手动确认java配置是否正常."+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'"
                       +'\n'+"然而出现了未知的错误,因此请自行在cmd中重运行如下命令来检查:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])
    except:
        back = confirm(text="检测时遇到意料之外的错误,请手动确认java配置是否正常."+'\n'+"程序运行了如下命令:"+'\n'+"'java','javac','java --version'"
                       +'\n'+"然而出现了未知的错误,因此请自行在cmd中重运行如下命令来检查:"+'\n'+"'java','javac','java --version'",title=version,buttons=['返回'])
        
def get_java_version():
    a = getoutput('java --version')
    read_json_writing_value('data/set_pgm/program_message.json', 'java_version_message', a)
    if 'Java(TM)' in a:
        b = a.splitlines()[0]
        c= b.split(' ')[1]
        d = c.split('.')[0]
    else:
        d = '无'
    
    return d

def versionset(version): 
    # 服务器版本设置
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
    
def set_core(core):
        read_json_writing_value("data/set/created_server_data.json","core",core)

def set_run_memory(core,version):
    a = int(read_json_get_value("data/set/created_server_data.json","run_memory"))
    if core == 1 and a > 1:
        a = a-1
        read_json_writing_value("data/set/created_server_data.json","run_memory",str(a))
    elif core == 2:
        a = a+1
        read_json_writing_value("data/set/created_server_data.json","run_memory",str(a))
    elif core == 114514:
        back = prompt(text='输入你想开设的服务器运行内存(输入正整数,单位:G).',title=version,default=str(a))
        if back != None:
            try:
                back = int(back)
            except:
                back2 = confirm(text="请输入一个正整数!",title=version,buttons=['重新输入'])
                back = None
        if back ==  None:
            back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
        elif int(back) >= 12:
            back2 = confirm(text="我的天啊,你真的想要用这么巨大的内存开一个小小的MC服务器?",title=version,buttons=['让我访问!','我放弃'])
            if back2 == '让我访问!':
                read_json_writing_value("data/set/created_server_data.json","run_memory",str(back))
                back = confirm(text="最有实力的一集.但我还是听你的!已保存于data/set/ru.txt",title=version,buttons=['继续'])
        elif int(back) <= 0:
            back2 = confirm(text="我认为如果不为服务器分配运行内存,服务器是没法启动的",title=version,buttons=['重新输入'])
        else:
            read_json_writing_value("data/set/created_server_data.json","run_memory",str(back))
            back = confirm(text="已保存于data/set/ru.txt",title=version,buttons=['继续'])

def reset_eula():
    eula = readtxt('serverdown/eula.txt')
    a=int(len(eula))
    eula[a-1]='eula=true'
    writing('serverdown/eula.txt',eula,1)

def set_forge_user_jvm():
    user_jvm = readtxt('serverdown/user_jvm_args.txt')
    run_memory = read_json_get_value("data/set/created_server_data.json","run_memory")
    user_jvm.append('-Xms' + run_memory + 'G')
    user_jvm.append('-Xmx' + run_memory + 'G')
    writing('serverdown/user_jvm_args.txt',user_jvm,1)

def set_forge_run_bat():
    run_bat = readtxt('serverdown/run.bat')
    for i in run_bat:
        if 'java @user_jvm_args.txt' in i:
            index_i = run_bat.index(i)
            break
    reset_str = run_bat[index_i][:-2]
    reset_str = reset_str + '--nogui' + run_bat[index_i][-2:]
    run_bat[index_i] = reset_str
    writing('serverdown/run.bat',run_bat,1)

def set_start_svrf():
    read_json_writing_value('data/set/created_server_data.json','first_start',"1")

def read_Server():
    try:
        Server = readtxt('.ServerList/ServerList.txt')
    except:
        Server = ['ANSI占位用句']
    Server.remove('ANSI占位用句')
    return Server

def choose_png(say):
    window = tk.Tk()
    window.withdraw()
    path = str(filedialog.askopenfilename(title='[ 自定义标示图 ] '+say, filetypes=[('图片','.png')]))
    if path == '':
        path = 'None'
    return path

def choose_ttf():
    window = tk.Tk()
    window.withdraw()
    path = str(filedialog.askopenfilename(title='[ 自定义字体 ] 选择一个格式为ttf的字体文件.',filetypes=[('字体文件','.ttf')]))
    if path == '':
        path = 'None'
    return path

def list_pagination(list, num = 7):
    '''
    列表分页函数
    input: (list) [ 'xxx' , 'xxx' , 'xxx' , ... ]
    output: (list) [ [ 'xxx' , 'xxx' ] , [ 'xxx' , 'xxx' ] , ... ]
    '''
    a = 0
    re_list = [[]]
    for i in list: #每七个选项分为一页
        len_num = len(re_list)
        if a == num: #如果到第八个则创建下一页并分配
            re_list.append([])
            re_list[len_num].append(i)
            a = 0
        else:
            re_list[len_num-1].append(i)
        a = a + 1
    return re_list