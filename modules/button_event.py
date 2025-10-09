from pyautogui import confirm,prompt
from typing import *

from . import functions as f
from . import abmk
from . import serversetting as svset
from . import file_operation



def Win_0_Create_New_Server(version: str) -> int:

    testset = int(f.read_json_get_value('data/set_pgm/program_settings.json','java_test'))

    if testset == 0:  #未检验
        back = confirm(text="在开设服务器之前,非常建议运行一次可行性检验!"+'\n'+'否则程序有可能因为个人配置而报错!',title=version,buttons=['开始','跳过','返回'])
        if back == '开始':
            f.testofset(version)
        elif back == '跳过':
            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
            f.read_json_writing_value('data/set_pgm/program_settings.json', 'java_test', '1')
            server_type = '插件服'
            win=11
            svset.reset_data()

    elif testset == 1: #已检验
        try:
            Server = f.readtxt('.ServerList/ServerList.txt')
        except:
            Server = ['ANSI占位用句']
        if len(Server) <= 99:
            win=11
            server_type = '插件服'
            svset.reset_data()
        else:
            back = confirm(text="创建的服务器过多(最多99个),如需要创建新服务器,请移除一个现有的服务器.",title=version,buttons=['明白'])

    elif testset == 2: #未通过
        back = confirm(text="上次可行性检验未通过,是否开始重检测?"+'\n'+'请确保你的错误已修复!',title=version,buttons=['开始','跳过','返回'])
        if back == '开始':
            f.testofset(version)
        elif back == '跳过':
            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
            f.read_json_writing_value('data/set_pgm/program_settings.json', 'java_test', '1')
            win=11
            server_type = '插件服'
            svset.reset_data()
    
    return win