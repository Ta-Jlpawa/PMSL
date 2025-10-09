import os
from time import sleep
from pyautogui import confirm
from modules import functions as f

"""
此附加程序用于进行服务器启动相关的操作
"""

version = f.read_json_get_value('Version.json','name') + ' ' + f.read_json_get_value('Version.json','version')


start_List = f.readtxt('start_Num.txt')
start_Num = str(start_List[1])



if start_Num == '0':
    core = f.read_json_get_value('data/set/created_server_data.json',"core")
    one = r'serverdown'
    two = r'..'
    os.chdir(one)
    if core != 'Forge':
        try:
            print("\n======================================", 
                  "\033[1;36m准备开始第一次运行服务器,此行作为分割线\033[0m", 
                  "======================================\n", sep='\n')
            os.system('begin.bat')
            os.chdir(two)
        except:
            back = confirm(text="ERROR:514.初次启动服务器时发生错误,请检查serverdown/begin.bat是否存在问题.",title=version,buttons=['继续'])

    else:
        try:
            os.system('install.bat')
            print("\n\033[1;33m服务器下载完毕!!\033[0m\n", sep='\n')
            print("\n======================================", 
                  "\033[1;36m准备开始第一次运行服务器,此行作为分割线\033[0m", 
                  "======================================\n", sep='\n')
            os.system('run.bat')
            os.chdir(two)
            f.set_forge_user_jvm()
            f.set_forge_run_bat()
        except:
            back = confirm(text="ERROR:514.初次启动serverdown/install.bat时发生错误,大概率是由于网络连接问题,请尝试手动运行.",title=version,buttons=['继续'])
    f.read_json_writing_value('data/set/created_server_data.json','first_start',"1")
    print("\n\033[1;32m服务器初始化完毕,你可以关闭此界面并在程序中继续操作!!\033[0m\n",
          "\033[1m此界面将在 \033[1;31m10\033[0m\033[1m 秒后自动关闭...\033[0m", sep='\n')
    


else:
    paths = '.ServerFile/'+start_Num
    one= r''+paths
    os.chdir(one)
    try:
        if os.path.isfile('begin.bat'):
            os.system('begin.bat')
        else:
            os.system('run.bat')
    except:
        back = confirm(text="ERROR:514.1.启动"+start_Num+"服务器时发生错误.",title=version,buttons=['继续'])
    print("\n\033[1;32m服务器已关闭,你可以关闭此界面!!\033[0m\n",
          "\033[1m此界面将在 \033[1;31m10\033[0m\033[1m 秒后自动关闭...\033[0m", sep='\n')


sleep(10.0)
