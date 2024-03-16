
'''

关于作者专用模块，在主程序中使用 import data.function.abmk 来导入.

'''



#  ==================================
#             IMPORT LIST
#  ==================================

from webbrowser import open

#  ==================================
#            FUNCTION LIST
#  ==================================




'''
visit 函数

用于通过 关于作者 界面的按键快捷访问作者账号主页

'''

def visit(author): #打开作者账号连接
    a = str(author)

    if a == 'TA_JLPawa':
        open('https://space.bilibili.com/1101301178')
    elif a == 'Github':
        open('https://github.com/Ta-Jlpawa/PMSL')