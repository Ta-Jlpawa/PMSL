
import shutil
import os
from pyautogui import confirm,prompt
from typing import *


from . import functions as f


"""
此模块用于更改服务器配置文件
"""

def reset_data():

    """
    当创建一个新服务器时，重置初始数据\n
    .Server Data 服务器的相关数据(创建时的data/set文件)\n
    .Server File 服务器的本体文件\n
    .Server List 已创建的服务器列表\n
    serverdown 未确认创建时的临时服务器文件存放地
    """

    shutil.rmtree('data/set')
    shutil.copytree('data.set(backup_copy)','data/set')
    try:
        serlist = f.readtxt('.ServerList/ServerList.txt')
    except:
        serlist = ['ANSI占位用句']
    server_name = 'NewServer_'+str(len(serlist))
    f.read_json_writing_value('data/set/created_server_data.json', 'server_name', server_name)

    try:
        shutil.rmtree('serverdown')
    except:
        pass
    try:
        os.makedirs('serverdown')
    except:
        pass

def get_new_server():
    #记录开启的服务器名
    server_name = f.read_json_get_value('data/set/created_server_data.json', 'server_name')
    try:
        serlist = f.readtxt('.ServerList/ServerList.txt')
    except:
        serlist = ['ANSI占位用句']
    serlist.append(server_name)
    f.writing('.ServerList/ServerList.txt',serlist,1)
    #复制服务器数据
    shutil.copytree('data/set','.ServerData/'+server_name)
    shutil.copytree('serverdown','.ServerFile/'+server_name)
    shutil.rmtree('serverdown')

def custom_server():
    #复制自定义的服务器文件
    server_name = f.read_json_get_value('data/set/created_server_data.json', 'server_name')
    shutil.copyfile(server_name+'.jar','serverdown/'+server_name+'.jar')
    
def delete_server(name):
    Server = f.readtxt('.ServerList/ServerList.txt')
    try:
        Server.remove(str(name))
        f.writing('.ServerList/ServerList.txt',Server,1)
        shutil.rmtree('.ServerFile/'+str(name))
        shutil.rmtree('.ServerData/'+str(name))
    except:
        print('ERROR,未找到目标服务器.')

def writing_server(filepath,test_what,text) -> None:
    #filepath,    文件路径
    #test_what    检测文本
    #text:        写入什么
    try:
        reline = f.readtxt(filepath)
        a = 0
        for i in reline:
            split_str = str(i).split('=')
            if split_str[0] == test_what:
                reline[a] = str(test_what)+'='+str(text)
                break
            else:
                a = a+1
        
        opfile=open(str(filepath),'w+')
        for i in reline:
            opfile.write(str(i)+'\n')
        opfile.close
    except :
        back = confirm(text="[ERROR] : 写入错误. \n读取server_properties文件时发生错误,可能是因为未找到文件\n由于随着mc的更新,部分设置被删除,所以会出现此种情况",title='ERROR',buttons=['继续'])

def server_properties_data(filepath : str, test_what : List[str]) -> dict:
    """
    读取指定的 server_properties 文件\n
    如果找到指定选项,则返回字典中指定选项的值为其在 server_properties 文件中的值,否则为 None
    """
    try:
        server_properties = f.readtxt(filepath)
    except:
        # 如果未找到文件，抛出提醒并返回一个全None的字典
        back = confirm(text="[ERROR] : 读取错误. \n读取server_properties文件时未找到文件",title='ERROR',buttons=['继续'])
        find_data = {}
        for i in test_what:
            find_data[i] = None
        return find_data
    
    find_data = {}
    a = 0

    for i in server_properties:
        split_str = i.split('=')
        server_properties[a] = split_str
        a += 1

    for i in test_what:
        find_data[i] = None
        for j in server_properties:
            if j[0] == i:
                find_data[i] = j[1]
                break

    return find_data
    