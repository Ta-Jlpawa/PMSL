#  ==================================
#             IMPORT LIST
#  ==================================

import os
import time as t
import sys
import threading as thr
import pygame as p
from pyautogui import confirm,prompt
#===#
import data.function.functions as f
import data.function.download as d
import data.function.setting as setting
import data.function.abmk as abmk
import data.function.derula as derula
import data.function.serversetting as svset

#  ==================================
#            FUNCTION LIST
#  ==================================

def thisver():
    text(['by TA_JLPawa [FREE]',version],[[5,645],[5,660]],[[0,0,0],[0,0,0]],[10,10],'data/msyh.ttc')

def window(photopath,xy,rxy): #all-list #渲染图片
    a=0
    for i in photopath:
        if int(rxy[a][0]) and int(rxy[a][1]) != 0: #缩放
            b=p.transform.scale(p.image.load(str(i)),(int(rxy[a][0]),int(rxy[a][1])))
        else:             #原图
            b=p.image.load(str(i))
        bylp.blit(b,[int(xy[a][0]),int(xy[a][1])])
        a=a+1
    p.display.update()


def text(textlist,xy,color,size,ttf): #L L L L Str #渲染文字
    a=0
    for i in textlist:
        b=p.font.Font(str(ttf),int(size[a]))
        c=b.render(str(i),True,(int(color[a][0]),int(color[a][1]),int(color[a][2])))
        bylp.blit(c,[int(xy[a][0]),int(xy[a][1])])
        a=a+1
    p.display.update()

def buildui(ui,ttf): #读取ui文件
    zzxg=f.readtxt(str(ui))
    a=0
    b='0'
    c=0
    d=0
    for i in zzxg:
        a=a+1
        if a == 1:
            b=str(i)
        if a == 2:
            c=int(i)
        if a == 3:
            d=int(i)
        if a == 4:
            text([b],[[c,d]],[[0,0,0]],[int(i)],str(ttf))
            a=0


def buildwin(win): #Int #构建界面
    bylp.fill((255,255,255))
    a=0

    if win == 0: #主界面
        window(['data/w.png'],[[0,0],[30,195]],[[0,0]]) #sample
        window(['data/b.png','data/b.png','data/b.png','data/b.png',],[[600,250],[600,350],[600,450],[600,550]],[[300,70],[300,70],[300,70],[300,70]])
        text(['开启服务器','服务器配置','程序设置','关于作者'],[[650,260],[650,360],[670,460],[670,560]],[[0,0,0],[0,0,0],[0,0,0],[0,0,0]],[40,40,40,40],'data/msyh.ttc')
    
    if win == 1: #开启服务器——选择核心
        window(['data/b.png','data/b.png','data/b.png','data/b.png','data/b.png','data/b.png','data/b.png','data/b.png'],[[10,10],[30,265],[30,315],[30,590],[310,265],[310,315],[590,265],[590,315]],[[150,42],[180,42],[180,42],[180,42],[180,42],[180,42],[235,42],[235,42]])
        text(['<--BACK'],[[20,17]],[[0,0,0]],[25],'data/msyh.ttc')
        buildui('data/ui_开启服务器_2.txt','data/msyh.ttc')

    if win == 2: #服务器配置
        window(['data/b.png'],[[10,10]],[[150,42]])
        text(['<--BACK'],[[20,17]],[[0,0,0]],[25],'data/msyh.ttc')
        buildui('data/ui_服务器配置.txt','data/msyh.ttc')

    if win == 3: #程序设置
        window(['data/b.png','data/b.png','data/b.png'],[[10,10],[30,155],[250,155]],[[150,42],[180,42],[180,42]])
        text(['<--BACK'],[[20,17]],[[0,0,0]],[25],'data/msyh.ttc')
        buildui('data/ui_程序设置.txt','data/msyh.ttc')

    if win == 4: #关于作者
        window(['data/b.png'],[[10,10]],[[150,42]])
        window(['data/b.png'],[[20,440]],[[150,42]])
        text(['<--BACK'],[[20,17]],[[0,0,0]],[25],'data/msyh.ttc') #sample
        text(['点此跳转'],[[40,445]],[[0,0,0]],[25],'data/msyh.ttc')
        buildui('data/ui_作者相关.txt','data/msyh.ttc')

    if win == 12: #开启服务器——选择版本
        window(['data/b.png','data/b.png','data/b.png','data/b.png','data/b.png'],[[10,10],[30,195],[30,255],[30,315],[30,590]],[[150,42],[180,42],[180,42],[180,42],[180,42]])
        text(['<--BACK'],[[20,17]],[[0,0,0]],[25],'data/msyh.ttc')
        buildui('data/ui_开启服务器_1.txt','data/msyh.ttc')

    if win == 13: #开启服务器——下载核心
        window(['data/b.png','data/b.png','data/b.png'],[[10,10],[30,590],[590,315]],[[150,42],[180,42],[235,42]])
        text(['<--BACK'],[[20,17]],[[0,0,0]],[25],'data/msyh.ttc')
        buildui('data/ui_开启服务器_3.txt','data/msyh.ttc')

    thisver()
    p.display.update()

#  ==================================
#          BUILDING WINDOWS
#  ==================================

version='PMS V1.0.0'

p.init()
win = 0

bylp=p.display.set_mode([1000,680])            #1000,680

p.display.set_caption('Py Minecraft Server 开服器','By TA_JLPawa')
icon=p.image.load('data/icon.png')
p.display.set_icon(icon)
buildwin(win)
#  ==================================
#            BUTTON EVENT
#  ==================================

while True:
    for e in p.event.get():
        if e.type==p.QUIT:
            p.quit()
            exit()
        if e.type==p.MOUSEBUTTONUP:
            mx,my=p.mouse.get_pos()

            print(str(mx)+','+str(my)) #打印鼠标点击位置(仅限程序开发辅助)######################测试语句

            if win == 0: #主界面
                if mx in range(600,900) and my in range(250,320):
                    testset=f.readtxt('data/set/testofset.txt')

                    if int(testset[0]) == 0:  #未检验
                        back = confirm(text="在开设服务器之前,非常建议运行一次可行性检验!"+'\n'+'否则程序有可能因为个人配置而报错!',title=version,buttons=['开始','跳过','返回'])
                        if back == '开始':
                            setting.testofset()
                        elif back == '跳过':
                            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
                            f.writing('data/set/testofset.txt','1',0)
                            win=1
                            buildwin(win)

                    elif int(testset[0]) == 1: #已检验
                        win=1
                        buildwin(win)

                    elif int(testset[0]) == 2: #未通过
                        back = confirm(text="上次可行性检验未通过,是否开始重检测?"+'\n'+'请确保你的错误已修复!',title=version,buttons=['开始','跳过','返回'])
                        if back == '开始':
                            setting.testofset()
                        elif back == '跳过':
                            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
                            f.writing('data/set/testofset.txt','1',0)
                            win=1
                            buildwin(win)

                if mx in range(600,900) and my in range(350,420):
                    win=2
                    buildwin(win)
                if mx in range(600,900) and my in range(450,520):
                    win=3
                    buildwin(win)
                if mx in range(600,900) and my in range(550,620):
                    win=4
                    buildwin(win)

            elif win == 1:
                if mx in range(10,160) and my in range(10,52):
                    win=0
                    buildwin(win)
                if mx in range(30,210) and my in range(590,632): #下一步源码示例
                    win=12
                    buildwin(win)
                

            elif win == 2:
                if mx in range(10,160) and my in range(10,52):
                    win=0
                    buildwin(win)

            elif win == 3:
                if mx in range(10,160) and my in range(10,52):
                    win=0
                    buildwin(win)
                if mx in range(30,210) and my in range(155,197):
                    back = confirm(text='确定开始运行一次可行性检验吗?',title=version,buttons=['开始','返回'])
                    if back == '开始':
                        setting.testofset()
                if mx in range(250,430) and my in range(155,197):
                    f.writing('data/set/testofset.txt','0',0)
                    back = confirm(text="可行性检验数据文件(data/set/testofset.txt)已重置.",title=version,buttons=['明白'])

            elif win == 4:
                if mx in range(10,160) and my in range(10,52):
                    win=0
                    buildwin(win)
                if mx in range(20,170) and my in range(440,482):
                    abmk.visit('TA_JLPawa')

            elif win == 12:
                if mx in range(10,160) and my in range(10,52):
                    win=1
                    buildwin(win)
                if mx in range(30,210) and my in range(195,237):
                    f.versionset()
                if mx in range(30,210) and my in range(255,297):
                    a=f.readtxt('data/ver.txt')
                    print(a)
                    back = confirm(text="已将可选版本参考打印于后台cmd.",title=version,buttons=['继续'])
                if mx in range(30,210) and my in range(315,357):
                    f.writing('data/set/version.txt','1.19.2',0)
                    back = confirm(text="已恢复默认值于data/set/version.txt",title=version,buttons=['继续'])
                if mx in range(30,210) and my in range(590,632):
                    win=13
                    buildwin(win)