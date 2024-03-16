#  ==================================
#             IMPORT LIST
#  ==================================

import os
import time as t
import sys
import threading as thr
import pygame as p
import random
import urllib
import urllib.request
import shutil
from pyautogui import confirm,prompt
#===#
import data.function.functions as f
import data.function.setting as setting
import data.function.abmk as abmk
import data.function.serversetting as svset


#  ==================================
#            FUNCTION LIST
#  ==================================

def thisver():
#   绘制版本号
    text([str(version)+'  By '+str(maker)],[[10,580]],[[255,255,255]],[10],'data/msyh.ttc')

def window(path,xy,rxy): 
#   all-list #渲染图片
#   以path为路径，xy为显示坐标，rxy为缩放大小
#   来在窗口上显示图片
    a=0
    for i in path:
        if int(rxy[a][0]) and int(rxy[a][1]) != 0: #缩放
            b=p.transform.scale(p.image.load(str(i)),(int(rxy[a][0]),int(rxy[a][1])))
        else:             #原图（rxy均不为0）
            b=p.image.load(str(i))
        bylp.blit(b,[int(xy[a][0]),int(xy[a][1])])
        a=a+1
    p.display.update()

def text(textlist,xy,color,size,ttf): 
#   L L L L Str #渲染文字
#   textlist:文字列表，xy:文字绘制坐标，color:文字颜色，size:文字大小(字号)，ttf:使用的字体文件路径
#   渲染一行文字并绘制
    a=0
    for i in textlist:
        b=p.font.Font(str(ttf),int(size[a]))
        c=b.render(str(i),True,(int(color[a][0]),int(color[a][1]),int(color[a][2])))
        bylp.blit(c,[int(xy[a][0]),int(xy[a][1])])
        a=a+1
    p.display.update()

def button(png,xyz,rexyz,textlist,color,size,ttf):   
#   便捷创建一个有底图有文字的按钮，文字自动居中
#   当png值为'none'时无底图
#   png:图像路径，xyz:按钮绘制坐标，rexyz:按钮大小，textlist:文字列表，color:文字颜色，size:文字大小(字号)，ttf:使用的字体文件路径
#    [a,b]    [[a,b],[c,d]]    [[a,b],[c,d]]    [a,b]    [[a,b,c],[d,e,f]]    [a,b]    [a,b]
    global tarea
    a=0
#   [[a,b,c,d],[a,b,c,d]]
    for i in png:
        if i != 'none':
            window([i],[xyz[a]],[rexyz[a]])
        text([textlist[a]],[[int(xyz[a][0]+(rexyz[a][0]-size[a]*int(len(textlist[a])))/2),int(xyz[a][1]+(rexyz[a][1]-size[a])/2-size[a]*0.25)]],[color[a]],[size[a]],ttf[a])
        tarea.append([int(xyz[a][0]),int(xyz[a][1]),int(xyz[a][0]+rexyz[a][0]),int(xyz[a][1]+rexyz[a][1])])
        a=a+1

def tip():
    global tips
    a=int(len(tips))
    b=random.randint(0,a-1)
    c=str(tips[b])
    f=390
    e=str.split(c,'&')
    window(['data/op_server_2_tip.png'],[[40,370]],[[0,0]])
    for i in e:
        if f == 390:
            text(['Tip:  '+i],[[60,f]],[[255,255,255]],[20],'data/msyh.ttc')
        else:
            text([i],[[60,f]],[[255,255,255]],[20],'data/msyh.ttc')
        f=f+25
    
def chooselist(textlist,color,size,ttf):
    global charea
    charea = []
    x=530
    y=53
    tx=520
    ty=51
    a=0
    window(['data/choose_list.png'],[[510,0]],[[0,0]])
    text(['描述功能真的没时间做完QwQ..'],[[531,365]],[color[a]],[20],ttf[a])
    for i in textlist:
        text([i],[[x,y]],[color[a]],[size[a]],ttf[a])
        text(['点此栏选择'],[[880,y+5]],[color[a]],[15],ttf[a])
        charea.append([tx,ty,tx+441,ty+30])
        a=a+1
        y=y+30
        ty=ty+30

def loading(finish,allof,fileof): #下载进度
    global daling
    load=100.0*finish*allof/fileof
    if load>100.0:
        load=100.0
    if daling == 114514:
        daling = 0
        DALSTOPERROR
    if int(7.7*load) != 0:
        window(['data/lg.png'],[[60,313]],[[int(7.7*load),20]])
        window(['data/bg.png'],[[60,340]],[[800,23]])
    text(['下载进度: %'+str(float(load))],[[60,340]],[[255,255,255]],[15],'data/msyh.ttc')
    
def dal():
    global daling
    daling = 1
    d=f.readtxt('data/set/download.txt')
    if int(d[0]) == 0:
        download=1
        a=f.readtxt('data/set/core.txt')
        b=f.readtxt('data/set/version.txt')
        c=f.readtxt('data/set/core_version.txt')

        if str(a[0]) == 'Spigot':
            http_s='https://download.getbukkit.org/spigot/spigot-'+str(b[0])+'.jar'
        if str(a[0]) == 'Forge':
            http_s='https://adfoc.us/serve/sitelinks/?id=271228&url=https://maven.minecraftforge.net/net/minecraftforge/forge/'+str(b[0])+'-'+str(c[0])+'/forge-'+str(b[0])+'-'+str(c[0])+'-installer.jar'
        if str(a[0]) == 'Fabric':
            http_s='https://meta.fabricmc.net/v2/versions/loader/'+str(b[0])+'/'+str(c[0])+'/'+str(c[1])+'/server/jar'
        if str(a[0]) == 'Paper':
            http_s='https://api.papermc.io/v2/projects/paper/versions/'+str(b[0])+'/builds/'+str(c[0])+'/downloads/paper-'+str(b[0])+'-'+str(c[0])+'.jar'

        #print(http_s)
        window(['data/bg.png'],[[60,175]],[[800,23]])
        text(['下载地址:'+str(http_s)],[[60,170]],[[255,255,255]],[15],'data/msyh.ttc')
        op=urllib.request.build_opener()
        op.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36')]
        urllib.request.install_opener(op)
        sername = f.readtxt('data/set/sername.txt')

        try:
            if str(a[0]) != 'Fabric':
                urllib.request.urlretrieve(http_s,'serverdown/'+str(sername[1])+'.jar',loading)
            else:
                window(['data/bg.png'],[[60,340]],[[800,23]])
                text(['下载进度: Fabric核心下载时无法查看进度,请等待此处显示下载完成.'],[[60,340]],[[255,255,255]],[15],'data/msyh.ttc')
                urllib.request.urlretrieve(http_s,'serverdown/'+str(sername[1])+'.jar')
                window(['data/bg.png'],[[60,340]],[[800,23]])
                text(['Fabric核心下载完成!'],[[60,340]],[[0,255,0]],[15],'data/msyh.ttc')
        except:
            window(['data/bg.png'],[[60,340]],[[800,23]])
            text(['ERROR:500.下载时发生未知错误,可能是网络问题,链接问题或网站问题.请检查网络并重试.'],[[60,340]],[[255,0,0]],[15],'data/msyh.ttc')
            download=0
            daling = 0

        f.writing('data/set/download.txt',str(download),0)
        daling = 0

def start_exe():
    os.system(r"start powershell.exe cmd /k 'start.exe'")

def start_First():
    f.writing('start_Num.txt',['ANSI占位用句','0'],1)
    start_exe()
    f.writing('data/set/start_svrf.txt','1',0)

def start_F():
    a = f.readtxt('data/set/ru.txt')
    n = f.readtxt('data/set/sername.txt')
    f.writing("serverdown/begin.bat",'java -Xms'+str(a[0])+'G -Xmx'+str(a[0])+'G -jar '+str(n[1])+'.jar --nogui',0)
    thr_stF=thr.Thread(target=start_First,daemon=1)
    thr_stF.start()

def show_eula():########################################
    try:
        eula = f.readtxt("serverdown/eula.txt")
    except:
        back = confirm(text="ERROR:001.在读取或展示服务器eula.txt时发生未知错误.\n可能是服务器自动下载文件时出了差错\n检查java配置,尝试重试几次即可.",title=version,buttons=['继续'])
    x=63
    y=184
    for i in eula:
        if len(i) > 75:
            text([str(i[:74])+'...'],[[x,y]],[[255,255,255]],[20],'data/msyh.ttc')
        else:
            text([str(i)],[[x,y]],[[255,255,255]],[20],'data/msyh.ttc')
        y=y+30

def get_server_properties_path():
    global stserver
    Server = f.read_Server()
    len_Server = len(Server)
    if len_Server != 0:
        setting_server = str(Server[stserver])
        setting_fpath = '.ServerFile/'+setting_server+'/server.properties'
    else:
        setting_fpath = 'none'
    return setting_fpath
        
def set_server_properties(win,what,test_what,texts):
    pro_path = get_server_properties_path()
    if pro_path != 'none':
        pro_data = str(svset.server_properties_data(pro_path,str(test_what)))

        if what == 0:
            back = prompt(text=str(texts),title=version,default=str(pro_data))
            if back == None:
                back2 = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
            else:
                svset.writing_server(pro_path,str(test_what),str(back))
                back2 = confirm(text="已保存为:"+str(back),title=version,buttons=['继续'])
                buildwin(win)

        elif what == 1:
            if pro_data == 'true':
                svset.writing_server(pro_path,str(test_what),'false')
            elif pro_data == 'false':
                svset.writing_server(pro_path,str(test_what),'true')
            back2 = confirm(text="已更改设置.",title=version,buttons=['继续'])
            buildwin(win)


def buildwin(win): 
#   Int #构建界面
#   绘制目标界面序号应显示的图像
    global tarea
    global chnum
    global stserver
    tarea=[]
    chnum='0'

    bylp.fill((27,27,27))
    a=0

    if win == 0: #主界面
        #window(['data/psd/IMG_3119(20230916-224620).png'],[[0,0]],[[1000,600]])
        window(['data/background/bg_winter.png'],[[0,0]],[[0,0]])
        window(['data/background/title_winter.png'],[[0,0]],[[0,0]]) #sample
        window(['data/background/serverlist.png'],[[0,0]],[[0,0]])
        button(['data/b_title.png','data/b_title.png','data/b_title.png','data/b_title.png']
               ,[[42,177],[42,265],[42,353],[42,441]]
               ,[[195,58],[195,58],[195,58],[195,58]]
               ,['开启服务器','服务器配置','程序设置','关于作者']
               ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
               ,[25,25,25,25]
               ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
        Server = f.read_Server()
        if len(Server) != 0 and len(Server) <=3:
            x=293
            y=208
            for i in Server:
                window(['data/background/Server.png'],[[x,y]],[[0,0]])
                text([str(i)],[[x+20,y+8]],[[255,255,255]],[35],'data/msyh.ttc')
                button(['data/b_title.png','data/b_title.png']
                    ,[[x+679-40-301,y+111-20-34],[x+679-20-156,y+111-20-34]]
                    ,[[156,40],[156,40]]
                    ,['启动','移除']
                    ,[[255,255,255],[255,0,0]]
                    ,[25,25]
                    ,['data/msyh.ttc','data/msyh.ttc'])
                y=y+111
        elif len(Server) == 0:
            text(['暂未创建服务器...'],[[500,330]],[[255,255,255]],[35],'data/msyh.ttc')
        elif len(Server) > 3:
            text(['创建服务器过多...'],[[500,330]],[[255,255,255]],[35],'data/msyh.ttc')
    
    elif win == 2: #服务器配置
        window(['data/set_world.png'],[[0,0]],[[0,0]])
        button(['data/back.png']
               ,[[20,20]]
               ,[[135,42]]
               ,['']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        button(['data/b_title_next.png','data/b.png']
               ,[[602,50],[36,540]]
               ,[[20,25],[180,35]]
               ,['','切换下一个']
               ,[[255,255,255],[255,255,255]]
               ,[15,15]
               ,['data/msyh.ttc','data/msyh.ttc'])
        button(['none','none','none','none']
               ,[[179,127],[718,126],[179,181],[718,181]]
               ,[[422,39],[243,39],[352,39],[243,39]]
               ,['','','','']
               ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
               ,[15,15,15,15]
               ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
        button(['none','none','none','none','none','none','none','none']
               ,[[335,293],[335,341],[335,389],[335,437],[681,291],[681,339],[681,387],[681,435]]
               ,[[38,38],[38,38],[38,38],[38,38],[38,38],[38,38],[38,38],[38,38]]
               ,['','','','','','','','']
               ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
               ,[15,15,15,15,15,15,15,15]
               ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
        Server = f.read_Server()
        len_Server = len(Server)
        if len_Server == 0:
            text(['暂未创建服务器...'],[[36,510]],[[249,238,145]],[20],'data/msyh.ttc')
        else:
            setting_server = str(Server[stserver])
            setting_filepath = '.ServerFile/'+setting_server+'/server.properties'
            text(['正在配置:'+setting_server],[[36,510]],[[150,249,145]],[20],'data/msyh.ttc')
            #可输入选项
            setting_obj=['level-seed=','difficulty=','level-name=','gamemode=']
            setting_objxyz=[[179,127],[718,126],[179,181],[718,181]]
            a=0
            for i in setting_obj:
                text([svset.server_properties_data(setting_filepath,i)],[[setting_objxyz[a][0],setting_objxyz[a][1]]],[[255,255,255]],[20],'data/msyh.ttc')
                a=a+1
            #仅有'T','F'的选项
            setting_obj=['force-gamemode=','allow-nether=','enable-command-block=','pvp=','spawn-npcs=','spawn-animals=','spawn-monsters=','generate-structures=']
            setting_objxyz=[[335,293],[335,341],[335,389],[335,437],[681,291],[681,339],[681,387],[681,435]]
            a=0
            for i in setting_obj:
                b = str(svset.server_properties_data(setting_filepath,i))
                color = [255,255,255]
                if b == 'true':
                    b='T'
                    color = [0,255,0]
                elif b == 'false':
                    b='F'
                    color = [255,0,0]
                text([b],[[setting_objxyz[a][0]+10,setting_objxyz[a][1]]],[color],[20],'data/msyh.ttc')
                a=a+1
        
    elif win == 21:
        window(['data/set_server.png'],[[0,0]],[[0,0]])
        button(['data/back.png']
               ,[[20,20]]
               ,[[135,42]]
               ,['']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        button(['data/b_title_back.png','data/b.png']
               ,[[358,50],[36,540]]
               ,[[20,25],[180,35]]
               ,['','切换下一个']
               ,[[255,255,255],[255,255,255]]
               ,[15,15]
               ,['data/msyh.ttc','data/msyh.ttc'])
        button(['none','none','none','none','none']
               ,[[224,127],[224,181],[727,181],[224,235],[753,235]]
               ,[[737,39],[130,39],[234,39],[253,39],[208,39]]
               ,['','','','','']
               ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
               ,[15,15,15,15,15]
               ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
        button(['none','none','none','none']
               ,[[335,293],[335,341],[335,389],[901,293]]
               ,[[38,38],[38,38],[38,38],[38,38]]
               ,['','','','']
               ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
               ,[15,15,15,15]
               ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
        Server = f.read_Server()
        len_Server = len(Server)
        if len_Server == 0:
            text(['暂未创建服务器...'],[[36,510]],[[249,238,145]],[20],'data/msyh.ttc')
        else:
            setting_server = str(Server[stserver])
            setting_filepath = '.ServerFile/'+setting_server+'/server.properties'
            text(['正在配置:'+setting_server],[[36,510]],[[150,249,145]],[20],'data/msyh.ttc')
            #可输入选项
            setting_obj=['motd=','max-players=','player-idle-timeout=','server-port=','simulation-distance=']
            setting_objxyz=[[224,127],[224,181],[727,181],[224,235],[753,235]]
            a=0
            for i in setting_obj:
                text([svset.server_properties_data(setting_filepath,i)],[setting_objxyz[a]],[[255,255,255]],[20],'data/msyh.ttc')
                a=a+1
            #仅有'T','F'的选项
            setting_obj=['online-mode=','white-list=','allow-flight=','prevent-proxy-connections=']
            setting_objxyz=[[335,293],[335,341],[335,389],[901,293]]
            a=0
            for i in setting_obj:
                b = str(svset.server_properties_data(setting_filepath,i))
                color = [255,255,255]
                if b == 'true':
                    b='T'
                    color = [0,255,0]
                elif b == 'false':
                    b='F'
                    color = [255,0,0]
                text([b],[[setting_objxyz[a][0]+10,setting_objxyz[a][1]]],[color],[20],'data/msyh.ttc')
                a=a+1

    elif win == 3: #程序设置
        text(['程序设置'],[[28,90]],[[255,255,255]],[35],'data/msyh.ttc')
        button(['data/back.png']
               ,[[20,20]]
               ,[[135,42]]
               ,['']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        button(['data/b.png','data/b.png']
               ,[[30,155],[250,155]]
               ,[[180,42],[180,42]]
               ,['可行性检验','重置检验文件']
               ,[[255,255,255],[255,255,255]]
               ,[25,25]
               ,['data/msyh.ttc','data/msyh.ttc'])
        
    elif win == 4: #关于作者
        window(['data/about_authors.png'],[[0,0]],[[0,0]])
        button(['data/back.png']
               ,[[20,20]]
               ,[[135,42]]
               ,['']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        button(['none','none']
               ,[[684,168],[684,358]]
               ,[[225,52],[225,52]]
               ,['','']
               ,[[255,255,255],[255,255,255]]
               ,[25,25]
               ,['data/msyh.ttc','data/msyh.ttc'])



    elif win == 11: #开启服务器——选择核心
        window(['data/op_server_1.png'],[[0,0]],[[0,0]])
        window(['data/choose_list.png'],[[510,0]],[[0,0]])
        # BACK和NEXT示例button
        button(['data/back.png','data/next.png']
               ,[[20,20],[820,538]]
               ,[[135,42],[135,42]]
               ,['','']
               ,[[255,255,255],[255,255,255]]
               ,[15,15]
               ,['data/msyh.ttc','data/msyh.ttc'])
        #
        button(['data/b.png','data/b.png','data/b.png','data/b.png','data/b.png','none']
               ,[[60,145],[230,145],[60,310],[230,310],[60,470],[243,33]]
               ,[[150,30],[150,30],[150,30],[150,30],[150,30],[256,35]]
               ,['插件服','模组服','MC版本','核心版本','运行内存',' ']
               ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
               ,[15,15,15,15,15,15]
               ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
        button(['data/b.png']
               ,[[165,525]]
               ,[[150,30]]
               ,['自定义核心']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        sername = f.readtxt('data/set/sername.txt')
        text([str(sername[1])],[[250,37]],[[255,255,255]],[20],'data/msyh.ttc')

    elif win == 12: #开启服务器——下载核心
        window(['data/op_server_2.png'],[[40,70]],[[0,0]])
        window(['data/op_server_2_tip.png'],[[40,370]],[[0,0]])
        button(['data/back.png','data/next.png']
               ,[[20,20],[820,538]]
               ,[[135,42],[135,42]]
               ,['','']
               ,[[255,255,255],[255,255,255]]
               ,[15,15]
               ,['data/msyh.ttc','data/msyh.ttc'])
        button(['data/b.png','data/b.png']
               ,[[60,200],[250,200]]
               ,[[150,30],[150,30]]
               ,['开始下载','终止下载']
               ,[[255,255,255],[255,255,255]]
               ,[15,15]
               ,['data/msyh.ttc','data/msyh.ttc'])
        button(['none']
               ,[[45,370]]
               ,[[910,130]]
               ,['']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        text(['Tip:  点击此处框框范围内,可以随机切换Tip语句哦!'],[[60,390]],[[255,255,255]],[20],'data/msyh.ttc')

    elif win == 13: #开启服务器__初次启动及修改eula
        start_f = f.readtxt('data/set/start_svrf.txt')
        if int(start_f[0]) == 0:
            window(['data/eula_1.png'],[[0,0]],[[0,0]])
            button(['data/Loading.png']
               ,[[0,0]]
               ,[[1000,600]]
               ,['']
               ,[[255,255,255]]
               ,[15]
               ,['data/msyh.ttc'])
        elif int(start_f[0]) == 1:
            window(['data/eula_1.png'],[[0,0]],[[0,0]])
            button(['none','none']
               ,[[154,496],[566,494]]
               ,[[288,40],[288,40]]
               ,['','']
               ,[[255,255,255],[255,255,255]]
               ,[15,15]
               ,['data/msyh.ttc','data/msyh.ttc'])
    
    elif win == 14: #服务器开设完成
        window(['data/finish.png'],[[0,0]],[[0,0]])
        button(['data/b.png']
               ,[[352,300]]
               ,[[295,62]]
               ,['返回主界面']
               ,[[255,255,255]]
               ,[28]
               ,['data/msyh.ttc'])
    
    thisver()
    p.display.update()

#  ==================================
#          BUILDING WINDOWS
#  ==================================

version='PMSL V1.0.0'
maker='TA_JLPawa'

p.init()

win = 0
tarea = []
charea = []
chnum = '0'
tips = f.readtxt('data/z_tip.txt')
daling = 0
stserver = 0
custom = 'False'
# win=0: 主界面界面序号
# tarea: Test Area,为鼠标行动xy坐标检测列表
# charea: choose area,为选择框检测坐标
# chnum: choose number,为选择框检测序号
# tips: 所有可显示的Tip集
# daling: 是否正在下载核心
# stserver: 正在配置的服务器序号
# custom: 是否为自定义服务器

bylp=p.display.set_mode([1000,600])            #1000,600

p.display.set_caption('Py Minecraft Server 开服器','By TA_JLPawa')
icon=p.image.load('data/icon.png')
p.display.set_icon(icon)
buildwin(win)

try:
    try_read_serverlist = f.readtxt('.ServerList/ServerList.txt')
except:
    shutil.copytree('ServerList(backup_copy)','.ServerList')


#  ==================================
#            BUTTON EVENT
#  ==================================

while True:
    for e in p.event.get():
        if e.type==p.QUIT:
            p.quit()
            sys.exit()
        if e.type==p.MOUSEBUTTONUP:
            mx,my=p.mouse.get_pos()

            print(str(mx)+','+str(my)) #打印鼠标点击位置(仅限程序开发辅助)######################测试语句

            if win == 0: #主界面
                tarea_len = len(tarea)

                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    testset=f.readtxt('data/set_pgm/testofset.txt')

                    if int(testset[0]) == 0:  #未检验
                        back = confirm(text="在开设服务器之前,非常建议运行一次可行性检验!"+'\n'+'否则程序有可能因为个人配置而报错!',title=version,buttons=['开始','跳过','返回'])
                        if back == '开始':
                            setting.testofset()
                        elif back == '跳过':
                            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
                            f.writing('data/set_pgm/testofset.txt','1',0)
                            win=11
                            svset.reset_data()
                            buildwin(win)

                    elif int(testset[0]) == 1: #已检验
                        try:
                            Server = f.readtxt('.ServerList/ServerList.txt')
                        except:
                            Server = ['ANSI占位用句']
                        if len(Server) <= 4:
                            win=11
                            svset.reset_data()
                            buildwin(win)
                        else:
                            back = confirm(text="创建的服务器过多(最多3个),如需要创建新服务器,请移除一个现有的服务器.",title=version,buttons=['明白'])

                    elif int(testset[0]) == 2: #未通过
                        back = confirm(text="上次可行性检验未通过,是否开始重检测?"+'\n'+'请确保你的错误已修复!',title=version,buttons=['开始','跳过','返回'])
                        if back == '开始':
                            setting.testofset()
                        elif back == '跳过':
                            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
                            f.writing('data/set_pgm/testofset.txt','1',0)
                            win=11
                            svset.reset_data()
                            buildwin(win)

                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win=2
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    win=3
                    buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    win=4
                    buildwin(win)
                if tarea_len > 4:
                    tarea_server_start = tarea[4:]
                    a = 0
                    for i in tarea_server_start:
                        what = tarea_server_start.index(i)
                        if what in [0,2,4]:
                            a=a+1
                            if mx in range(int(i[0]),int(i[2])) and my in range(int(i[1]),int(i[3])):
                                Server = f.readtxt('.ServerList/ServerList.txt')
                                Server_Run = str(Server[a])
                                back = confirm(text="你是否确定启动服务器 "+Server_Run+" ?.",title=version,buttons=['暂不启动','确定'])
                                if back == '确定':
                                    f.writing('start_Num.txt',['ANSI占位用句',Server_Run],1)
                                    thr_stexe=thr.Thread(target=start_exe,daemon=1)
                                    thr_stexe.start()
                        elif what in [1,3,5]:
                            if mx in range(int(i[0]),int(i[2])) and my in range(int(i[1]),int(i[3])):
                                Server = f.readtxt('.ServerList/ServerList.txt')
                                Server_Run = str(Server[a])
                                back = confirm(text="你是否移除服务器 "+Server_Run+" ?.\n这将删除此程序目录下的所有有关此服务器的文件!\n请确保你在其它地方为服务器文件做了备份!!",title=version,buttons=['暂不移除','确定'])
                                if back == '确定':
                                    back = confirm(text="你真的想要移除服务器 "+Server_Run+" 吗?.\n此操作不可挽回!!!",title=version,buttons=['暂不移除','我真的确定!!'])
                                if back == '我真的确定!!':
                                    svset.delete_server(Server_Run)
                                    back = confirm(text=Server_Run+" 已被移除!!",title=version,buttons=['确定'])
                                    win = 0
                                    buildwin(win)

            elif win == 2:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win=21
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    Server = f.read_Server()
                    if len(Server) != 0:
                        if stserver < len(Server)-1:
                            stserver = stserver+1
                        else:
                            stserver = 0
                        buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    set_server_properties(2,0,'level-seed=','请输入世界种子\n更换种子后须重创建世界才能生效')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    set_server_properties(2,0,'difficulty=','请输入目标难度\n可输入\n[peaceful-和平,easy-简单,normal-普通,hard-困难]')
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    set_server_properties(2,0,'level-name=','请输入世界名称\n将作为世界名称及其文件夹名')
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    set_server_properties(2,0,'gamemode=','请输入默认游戏模式\n可输入\n[survival-生存,creative-创造,adventure-冒险,spectator-旁观]')
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                    set_server_properties(2,1,'force-gamemode=',0)
                elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                    set_server_properties(2,1,'allow-nether=',0)
                elif mx in range(int(tarea[9][0]),int(tarea[9][2])) and my in range(int(tarea[9][1]),int(tarea[9][3])):
                    set_server_properties(2,1,'enable-command-block=',0)
                elif mx in range(int(tarea[10][0]),int(tarea[10][2])) and my in range(int(tarea[10][1]),int(tarea[10][3])):
                    set_server_properties(2,1,'pvp=',0)
                elif mx in range(int(tarea[11][0]),int(tarea[11][2])) and my in range(int(tarea[11][1]),int(tarea[11][3])):
                    set_server_properties(2,1,'spawn-npcs=',0)
                elif mx in range(int(tarea[12][0]),int(tarea[12][2])) and my in range(int(tarea[12][1]),int(tarea[12][3])):
                    set_server_properties(2,1,'spawn-animals=',0)
                elif mx in range(int(tarea[13][0]),int(tarea[13][2])) and my in range(int(tarea[13][1]),int(tarea[13][3])):
                    set_server_properties(2,1,'spawn-monsters=',0)
                elif mx in range(int(tarea[14][0]),int(tarea[14][2])) and my in range(int(tarea[14][1]),int(tarea[14][3])):
                    set_server_properties(2,1,'generate-structures=',0)

            elif win == 21:########################################
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win=2
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    Server = f.read_Server()
                    if len(Server) != 0:
                        if stserver < len(Server)-1:
                            stserver = stserver+1
                        else:
                            stserver = 0
                        buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    set_server_properties(21,0,'motd=','请输入要展示的服务器信息(为Unicode码)\n可输入的字符数[0-59]')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    set_server_properties(21,0,'max-players=','请输入服务器支持的最大玩家数量')
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    set_server_properties(21,0,'player-idle-timeout=','请输入玩家被允许的最长挂机时间(单位:分钟)\n设置为0表示关闭此功能')
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    set_server_properties(21,0,'server-port=','请输入服务器(监听的)端口号\n可输入的范围[1-65534]')
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                    set_server_properties(21,0,'simulation-distance=','请输入玩家各个方向上的区块数量(以玩家为中心的半径)\n可输入的范围[3-32]')
                elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                    set_server_properties(21,1,'online-mode=',0)
                elif mx in range(int(tarea[9][0]),int(tarea[9][2])) and my in range(int(tarea[9][1]),int(tarea[9][3])):
                    set_server_properties(21,1,'white-list=',0)
                elif mx in range(int(tarea[10][0]),int(tarea[10][2])) and my in range(int(tarea[10][1]),int(tarea[10][3])):
                    set_server_properties(21,1,'allow-flight=',0)
                elif mx in range(int(tarea[11][0]),int(tarea[11][2])) and my in range(int(tarea[11][1]),int(tarea[11][3])):
                    set_server_properties(21,1,'prevent-proxy-connections=',0)

            elif win == 3:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    back = confirm(text='确定开始运行一次可行性检验吗?',title=version,buttons=['开始','返回'])
                    if back == '开始':
                        setting.testofset()
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    f.writing('data/set_pgm/testofset.txt','0',0)
                    back = confirm(text="可行性检验数据文件(data/set_pgm/testofset.txt)已重置.",title=version,buttons=['明白'])

            elif win == 4:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    abmk.visit('TA_JLPawa')
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    abmk.visit('Github')

            elif win == 11:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    custom = 'False'
                    shutil.rmtree('serverdown')
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])): #下一步源码示例
                    if custom == 'False':
                        win=12
                        buildwin(win)
                    elif custom == 'True':
                        win=13
                        buildwin(win)
                        svset.custom_server()
                        start_F()
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    if chnum != '插件服' and custom == 'False':
                        chnum = '插件服'
                        chooselist(['Spigot','Paper']
                                ,[[255,255,255],[255,255,255]]
                                ,[18,18]
                                ,['data/msyh.ttc','data/msyh.ttc'])
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    if chnum != '模组服' and custom == 'False':
                        chnum = '模组服'
                        chooselist(['Fabric','Forge']
                                ,[[255,255,255],[255,255,255]]
                                ,[18,18]
                                ,['data/msyh.ttc','data/msyh.ttc'])
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    if chnum != 'mc版本' and custom == 'False':
                        chnum = 'mc版本'
                        chooselist(['打开输入界面','查询版本','重置已保存的数据']
                                ,[[255,255,255],[255,255,255],[255,255,255]]
                                ,[18,18,18]
                                ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    a=f.readtxt('data/set/core.txt')
                    if chnum != '核心版本' and custom == 'False':
                        if a[0] == 'Spigot':
                            back = confirm(text="Spigot核心无需再设置核心版本.",title=version,buttons=['继续'])
                        elif a[0] == 'Paper' or a[0] == 'Fabric' or a[0] == 'Forge':
                            chnum = '核心版本'
                            chooselist(['开始输入',"将已保存的数据重置为'0'"]
                                    ,[[255,255,255],[255,255,255]]
                                    ,[18,18]
                                    ,['data/msyh.ttc','data/msyh.ttc'])
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    if chnum != '内存':
                        chnum = '内存'
                        chooselist(['其他','1G','2G','4G','8G','重置已保存的数据']
                                ,[[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255],[255,255,255]]
                                ,[18,18,18,18,18,18]
                                ,['data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc','data/msyh.ttc'])
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                    if custom == 'False':
                        sername = f.readtxt('data/set/sername.txt')
                        sernamed = f.readtxt('.ServerList/ServerList.txt')
                        back = prompt(text='输入你想设置的服务器名称.(建议为全英文)',title=version,default=sername[1])
                        if back ==  None:
                            back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
                        elif len(back) == 0 or len(back) > 12:
                            back = confirm(text="你输入的名字太短/太长了!."+'\n'+'请确保输入的名字大于0个字符并且小于等于12个字符!',title=version,buttons=['继续'])
                        else:
                            if back not in sernamed:
                                f.writing('data/set/sername.txt',['ANSI占位用句',str(back)],1)
                                back = confirm(text="已保存目标服务器名称为: "+str(back)+'.',title=version,buttons=['继续'])
                                sername = f.readtxt('data/set/sername.txt')
                                window(['data/server_name.png'],[[243,33]],[[0,0]])
                                text([str(sername[1])],[[250,37]],[[255,255,255]],[20],'data/msyh.ttc')
                            else:
                                back = confirm(text="目标服务器名称已存在,请重新命名! ",title=version,buttons=['继续'])
                elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                    sername = f.readtxt('data/set/sername.txt')
                    sernamed = f.readtxt('.ServerList/ServerList.txt')
                    back = prompt(text='请将你的自定义服务器核心jar文件放在\n本程序exe文件所在文件夹目录下.\n随后在此输入你的jar文件名称(不带文件后缀,建议为全英文)',title=version,default='')
                    if back ==  None:
                        back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
                    elif len(back) == 0 or len(back) > 12:
                        back = confirm(text="你输入的名字太短/太长了!."+'\n'+'请确保输入的名字大于0个字符并且小于等于12个字符!',title=version,buttons=['继续'])
                    else:
                        if back not in sernamed:
                            f.writing('data/set/sername.txt',['ANSI占位用句',str(back)],1)
                            back = confirm(text="已保存目标服务器名称为: "+str(back)+'.\n现在程序处于自定义模式,部分设置无法更改.\n如需退出请返回主界面.',title=version,buttons=['继续'])
                            custom = 'True'
                            sername = f.readtxt('data/set/sername.txt')
                            window(['data/server_name.png'],[[243,33]],[[0,0]])
                            text([str(sername[1])],[[250,37]],[[255,255,255]],[20],'data/msyh.ttc')
                        else:
                            back = confirm(text="目标服务器名称已存在,请重新命名! ",title=version,buttons=['继续'])
                if chnum == 'mc版本' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.versionset()
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        a=f.readtxt('data/ver.txt')
                        print(a)
                        back = confirm(text="已将可选版本参考打印于后台cmd.",title=version,buttons=['继续'])
                    elif mx in range(int(charea[2][0]),int(charea[2][2])) and my in range(int(charea[2][1]),int(charea[2][3])):
                        f.writing('data/set/version.txt','1.19.2',0)
                        back = confirm(text="已恢复默认值'1.19.2'于data/set/version.txt",title=version,buttons=['继续'])
                elif chnum == '插件服' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.coreset('Spigot')
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        f.coreset('Paper')
                elif chnum == '模组服' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.coreset('Fabric')
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        #f.coreset('Forge')
                        back = confirm(text="Forge暂时不受支持."+'\n'+"因为其开服流程与其他类型服务器步骤不同."+'\n'+"请等待后续更新...",title=version,buttons=['继续'])
                elif chnum == '核心版本' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        try:
                            f.CVset()
                        except:
                            back = confirm(text="ERROR:114.在设置核心版本时发生未知错误.",title=version,buttons=['继续'])
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        f.writing('data/set/core_version.txt','0',0)
                        back = confirm(text="已将已保存的数据重置为'0'",title=version,buttons=['继续'])
                elif chnum == '内存':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.ruset(114514)
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        f.ruset(1)
                    elif mx in range(int(charea[2][0]),int(charea[2][2])) and my in range(int(charea[2][1]),int(charea[2][3])):
                        f.ruset(2)
                    elif mx in range(int(charea[3][0]),int(charea[3][2])) and my in range(int(charea[3][1]),int(charea[3][3])):
                        f.ruset(4)
                    elif mx in range(int(charea[4][0]),int(charea[4][2])) and my in range(int(charea[4][1]),int(charea[4][3])):
                        f.ruset(8)
                    elif mx in range(int(charea[5][0]),int(charea[5][2])) and my in range(int(charea[5][1]),int(charea[5][3])):
                        f.writing('data/set/ru.txt','4',0)
                        back = confirm(text="已恢复默认值'4'于data/set/ru.txt",title=version,buttons=['继续'])

            elif win == 12:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    if daling == 0:
                        win=11
                        buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    if daling == 0 and int(f.readtxt('data/set/download.txt')[0]) == 1:
                        win=13
                        buildwin(win)
                        start_F()
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    if daling == 0 and int(f.readtxt('data/set/download.txt')[0]) == 0 :
                        thr_dal=thr.Thread(target=dal,daemon=1)
                        thr_dal.start()
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    if daling == 1:
                        daling = 114514
                        window(['data/bg.png'],[[60,340]],[[800,20]])
                        text(['PAUSE.'],[[60,340]],[[255,0,0]],[15],'data/msyh.ttc')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    tip()
                    
            elif win == 13:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    start_f = f.readtxt('data/set/start_svrf.txt')
                    if int(start_f[0]) == 1:
                        buildwin(win)
                        show_eula()
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    f.reset_eula()
                    win=14
                    buildwin(win)

            elif win == 14:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    custom = 'False'
                    svset.get_new_server()
                    buildwin(win)