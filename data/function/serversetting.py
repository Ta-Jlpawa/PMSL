import shutil
import os

'''

快捷更改服务器配置文件专用模块,在主程序中使用 import data.function.serversetting 来导入.
此模块需要编写

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
    return reline





def reset_data():
    #重置数据

    #.Server Data 服务器的相关数据(创建时的data/set文件)
    #.Server File 服务器的本体文件
    #.Server List 已创建的服务器列表
    #serverdown 未确定时的服务器文件存放地
    shutil.rmtree('data/set')
    shutil.copytree('data.set(backup_copy)','data/set')
    try:
        serlist = readtxt('.ServerList/ServerList.txt')
    except:
        serlist = ['ANSI占位用句']
    sername = 'NewServer_'+str(len(serlist))
    sername_file = readtxt('data/set/sername.txt')
    sername_file.append(sername)
    writing('data/set/sername.txt',sername_file,1)
    try:
        os.makedirs('serverdown')
    except:
        print('文件夹已存在,无需创建.')

def get_new_server():
    #记录开启的服务器名
    sername = readtxt('data/set/sername.txt')
    try:
        serlist = readtxt('.ServerList/ServerList.txt')
    except:
        serlist = ['ANSI占位用句']
    serlist.append(str(sername[1]))
    writing('.ServerList/ServerList.txt',serlist,1)
    #复制服务器数据
    shutil.copytree('data/set','.ServerData/'+str(sername[1]))
    shutil.copytree('serverdown','.ServerFile/'+str(sername[1]))
    shutil.rmtree('serverdown')

def custom_server():
    #复制自定义的服务器文件
    sername = readtxt('data/set/sername.txt')
    shutil.copyfile(str(sername[1])+'.jar','serverdown/'+str(sername[1])+'.jar')
    
def delete_server(name):
    Server = readtxt('.ServerList/ServerList.txt')
    try:
        Server.remove(str(name))
        writing('.ServerList/ServerList.txt',Server,1)
        shutil.rmtree('.ServerFile/'+str(name))
        shutil.rmtree('.ServerData/'+str(name))
    except:
        print('ERROR,未找到目标服务器.')

def writing_server(filepath,test_what,text):
    #filepath,    文件路径
    #test_what    检测文本
    #text:        写入什么
    reline = readtxt(filepath)
    a = 0
    for i in reline:
        cot = str(i).find(str(test_what))
        if str(cot) != '-1':
            reline[a] = str(test_what)+str(text)
            break
        else:
            a = a+1
    
    opfile=open(str(filepath),'w+')
    for i in reline:
        opfile.write(str(i)+'\n')
    opfile.close

def server_properties_data(filepath,test_what):
    server_properties = readtxt(filepath)
    a = 0
    for i in server_properties:
        cot = str(i).find(str(test_what))
        if str(cot) != '-1':
            re_server_properties = str(server_properties[a]).replace(str(test_what),'')
            break
        else:
            a = a+1
    return re_server_properties