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
import cv2
import numpy as np
#from moviepy.editor import *
from pyautogui import confirm,prompt
#===#
import data.function.functions as f
import data.function.abmk as abmk
import data.function.serversetting as svset

#  ==================================
#            FUNCTION LIST
#  ==================================

def thisver():
#   绘制版本号
    text(str(version)+'  By '+str(maker)+'    /    '+str(fps)+'FPS',(10,585),(255,255,255),10,'data/HarmonyOS_Sans_SC_Bold.ttf')

def window(path,xy,rxy): 
#   渲染图片  'str' , (x,y) , (rx,ry)
#   以path为路径，xy为显示坐标，rxy为缩放大小
#   来在窗口上显示图片
    if int(rxy[0]) and int(rxy[1]) != 0: # 缩放
        b=p.transform.scale(p.image.load(str(path)).convert_alpha(),rxy)
    else:                                # 原图（rxy均不为0）
        b=p.image.load(str(path)).convert_alpha()
    if len(rxy) == 3:
        b.set_alpha(rxy[2])
    bylp.blit(b,xy)

def alpha_window(path,xy,rxy,mode,num,a):
#   渲染图片  'str' , (x,y) , (rx,ry) , 'alpha_up / alpha_down' , (100 /初始数值/ , 50 /目标值/ , 1 /变化速率每帧/ , 100 /下一个目标值/) , show_window中的第几项
#   播放一个可变换透明度的图像的动画,一次性
#   仅可在 play_window 函数中调用 , 仅可于 子线程 中调用
    global show_window
    if int(rxy[0]) and int(rxy[1]) != 0:
        b=p.transform.scale(p.image.load(str(path)),rxy)
    else:
        b=p.image.load(str(path))

    alpha = num[0]
    end_alpha = num[1]
    next_alpha = num[3]
    speed = num[2]

    if mode == 'alpha_up':
        if alpha < end_alpha:
            alpha = alpha + speed
            image_copy = b.copy()
            image_copy.set_alpha(alpha)
            show_window[a][4][1][0] = alpha
        else:
            show_window[a][4][1][1] = next_alpha
            show_window[a][4][1][3] = end_alpha
            show_window[a][4][0] = 'alpha_down'
    elif mode == 'alpha_down':
        if alpha > end_alpha:
            alpha = alpha - speed
            image_copy = b.copy()
            image_copy.set_alpha(alpha)
            show_window[a][4][1][0] = alpha
        else:
            show_window[a][4][1][1] = next_alpha
            show_window[a][4][1][3] = end_alpha
            show_window[a][4][0] = 'alpha_up'

    bylp.blit(image_copy,xy)

def cv2_imread(path,mode):
    img = cv2.imdecode(np.fromfile(path,dtype=np.uint8),mode)
    return img

def cut_window(path,show_server):
#   裁剪
    #path = u''+path+''
    img = cv2_imread(path,-1)
    img = cv2.resize(img, (215,397))
    points = np.array([[35,0],[215,0],[180,397],[0,397]])
    points = np.array([points])
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.polylines(mask, points, 1, 255)
    cv2.fillPoly(mask, points, 255)
    re_img = cv2.bitwise_and(img, img, mask=mask)
    bg = np.ones_like(img, np.uint8) * 255
    cv2.bitwise_not(bg, bg, mask=mask)
    img = bg + re_img
#   白底替换透明
    height , width , channels = img.shape
    end_img = np.ones((height, width, 4)) * 255
    end_img[:, :, :4] = img
    for i in range(height):
        for j in range(width):
            if end_img[i, j, :3].tolist() == [255.0, 255.0, 255.0]:
                end_img[i, j, :] = np.array([255.0, 255.0, 255.0, 0])

    cv2.imwrite('.ServerData/'+show_server+'/server_icon.png', end_img)

def text(texts,xy,color,size,ttf): 
#   渲染文字  'str' , (x,y) , (R,G,B, A【可选】) , int , 'str'
#   text:文字，xy:文字绘制坐标，color:文字颜色，size:文字大小(字号)，ttf:使用的字体文件路径
#   渲染一行文字并绘制
    b=p.font.Font(str(ttf),int(size))
    c=b.render(str(texts),True,color)
    if len(color) == 4:
        c.set_alpha(color[3])
    bylp.blit(c,xy)

def auto_center_text(texts,xy,rexy,color,size,ttf): 
#   渲染一个自动居中的文字
    b=p.font.Font(str(ttf),int(size))
    c=b.render(str(texts),True,color)
    text_width, text_height = c.get_size()
    bylp.blit(c,[int(xy[0])+(int(rexy[0])-text_width)/2,int(xy[1])+(int(rexy[1])-text_height)/2])

def find_point(p1,p2,p3,p4):
    # 顶点的坐标 pn = (x,y)  #此函数用于寻找不规则图形按钮的范围，目前并未使用
    vertices = [p1,p2,p3,p4]
    points_inside = f.points_in_irregular_quad(vertices)
    return points_inside

def button(png,xy,button_size,text,color,size,ttf): 
#   便捷创建一个有底图有文字的按钮，文字自动居中
#   当png值为'none'时无底图
#   png:图像路径，xy:按钮绘制坐标，button_size:按钮大小，text:文字，color:文字颜色，size:文字大小(字号)，ttf:使用的字体文件路径
    if png != 'none':
        window(png,xy,button_size)
    auto_center_text(text,xy,button_size,color,size,ttf)

def add_show_window(add_obj):
#   在非buildwin()函数中操控显示的图像
#   当有正在显示的项目相同时，将自动避免列表中的项目重复
    global show_window
    for obj in add_obj:
        try:
            show_window.remove(obj)
        except:
            a=0
        show_window.append(obj)
    
def reload_add_show_window(add_obj):
#   在非buildwin()函数中操控显示的图像，同时刷新显示列表
#   等效为仅显示buildwin()基础图像与add_obj中的图像
    global win
    buildwin(win)
    show_window.extend(add_obj)

def findtag_remove_show_window(find,tag):
    #移除带有指定tag的图像
    #find : 寻找的项目类型   tag : 指定的tag
    global show_window
    remove_obj=[]
    try:
        for i in show_window:
            if i[0] == str(find):
                ii=len(i)
                for iii in i[ii-1]:
                    if iii == str(tag):
                        remove_obj.append(i)
        for i in remove_obj:
            show_window.remove(i)
    except:
        print('Not FOUND')

def t_area_append():
#   为将要渲染的按钮添加判定(如有动画则同时添加动画判定)
#   格式: tarea = [ [ x_1 , y_1 , ex_1 , ey_1 ] , [ x_2 , y_2 , ex_2 , ey_2 ] , ...]
#   格式: tarea_ani = [ [ x_1 , y_1 , ex_1 , ey_1 , png_1 , ###start_num_1 , end_num_1 , speed_1 ] , [ x_2 , y_2 , ex_1 , ey_1 , png_2 , ###start_num_2 , end_num_2 , speed_2 ] , ...]
    global tarea
    global tarea_ani
    global show_window
    for i in show_window:
        if i[0] == 'button':
            try:
                if i[8][0] == 'self':
                    tarea_ani.append([i[2][0],i[2][1],int(i[2][0]+i[3][0]),int(i[2][1]+i[3][1]),i[1]])#,i[8][1][0],i[8][1][1],i[8][1][2]])
                    tarea.append([i[2][0],i[2][1],int(i[2][0]+i[3][0]),int(i[2][1]+i[3][1])])
                else:
                    tarea_ani.append([i[2][0],i[2][1],int(i[2][0]+i[3][0]),int(i[2][1]+i[3][1]),i[8][0]])#,i[8][1][0],i[8][1][1],i[8][1][2]])
                    tarea.append([i[2][0],i[2][1],int(i[2][0]+i[3][0]),int(i[2][1]+i[3][1])])
            except:
                tarea.append([i[2][0],i[2][1],int(i[2][0]+i[3][0]),int(i[2][1]+i[3][1])])
    #print(tarea)
    #print(tarea_ani)

def show_server_all_data():
    global show_window
    a=str(f.readtxt('data/set/sername.txt')[1])
    b=str(f.readtxt('data/set/core.txt')[0])
    c=str(f.readtxt('data/set/core_version.txt')[0])
    d=str(f.readtxt('data/set/ru.txt')[0])
    e=str(f.readtxt('data/set/version.txt')[0])
    if b in ['Spigot','Paper']:
        b = '插件服 | ' + b
    elif b in ['Fabric','Forge']:
        b = '模组服 | ' + b
    c = e + ' | ' + c
    d = d + ' G'
    findtag_remove_show_window('text',"Server_name")
    findtag_remove_show_window('text',"Server_core")
    findtag_remove_show_window('text',"Server_version")
    findtag_remove_show_window('text',"Server_ru")
    add_show_window([['text',a,(250,30),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',["Server_name"]]
                        ,['text',a,(542,372),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',["Server_name"]]
                        ,['text',b,(542,407),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',["Server_core"]]
                        ,['text',c,(542,442),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',["Server_version"]]
                        ,['text',d,(542,477),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',["Server_ru"]]])

def setup(filename):
    files=open("Setup.py")
    os.system("java -jar "+filename+" --installServer")
    os.system("run.bat")

def tip(filepath,xy,interval):
    global show_window
    tips = f.readtxt(str(filepath))
    a=int(len(tips))
    b=random.randint(0,a-1)
    c=str(tips[b])
    e=str.split(c,'&')
    rey=xy[1]
    findtag_remove_show_window('text','TIP')
    #print(show_window)
    for i in e:
        if rey == xy[1]:
            show_window.append(['text','Tip:  '+i,(xy[0],rey),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',['TIP']])
        else:
            show_window.append(['text',i,(xy[0],rey),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',['TIP']])
        rey=rey+interval
    #print(show_window)
    
def chooselist(textlist,color,size,ttf):
    global charea
    charea = []
    x=540
    y=43
    tx=530
    ty=41
    a=0
    findtag_remove_show_window('text',"CHOOSE")
    for i in textlist:
        add_show_window([['text',i,(x,y),color[a],size[a],ttf[a],['CHOOSE']]
                         ,['text','点此栏选择',(880,y+5),color[a],15,ttf[a],['CHOOSE']]])
        charea.append([tx,ty,tx+441,ty+30])
        a=a+1
        y=y+30
        ty=ty+30

def loading(finish,allof,fileof): #下载进度
    global daling
    global show_window
    load=100.0*finish*allof/fileof
    if load>100.0:
        load=100.0
    if daling == 114514:
        DALSTOPERROR
        #这个报错是用来终止下载的awa
    if int(7.7*load) != 0:
        print(int(7.7*load))

        findtag_remove_show_window('window',"LOAD")
        findtag_remove_show_window('auto_center_text',"LOAD")

        add_show_window([['window','data/lg.png',(114,222),(int(7.7*load),20),["LOAD"]]])
        add_show_window([['auto_center_text',' %'+str(round(float(load),2)),(111,219),(776,27),(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["LOAD"]]])

        #print(str(show_window)+'\n\n\n')
        #t.sleep(2)
    
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
            http_s='https://maven.minecraftforge.net/net/minecraftforge/forge/'+str(b[0])+'-'+str(c[0])+'/forge-'+str(b[0])+'-'+str(c[0])+'-installer.jar'
        if str(a[0]) == 'Fabric':
            http_s='https://meta.fabricmc.net/v2/versions/loader/'+str(b[0])+'/'+str(c[0])+'/'+str(c[1])+'/server/jar'
        if str(a[0]) == 'Paper':
            http_s='https://api.papermc.io/v2/projects/paper/versions/'+str(b[0])+'/builds/'+str(c[0])+'/downloads/paper-'+str(b[0])+'-'+str(c[0])+'.jar'

        findtag_remove_show_window('window',"ERROR")
        findtag_remove_show_window('auto_center_text',"ERROR")
        add_show_window([['auto_center_text',str(http_s),(200,258),(600,24),(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["ERROR"]]])

        op=urllib.request.build_opener()
        op.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36')]
        urllib.request.install_opener(op)
        sername = f.readtxt('data/set/sername.txt')

        try:
            if str(a[0]) != 'Fabric':
                urllib.request.urlretrieve(http_s,'serverdown/'+str(sername[1])+'.jar',loading)
                findtag_remove_show_window('auto_center_text',"LOAD")
                add_show_window([['auto_center_text','下载完成!',(111,219),(776,27),(0,255,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["ERROR"]]])
            else:
                add_show_window([['auto_center_text','Fabric核心下载时无法查看进度,请等待此处显示下载完成.',(111,219),(776,27),(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["LOAD"]]])
                urllib.request.urlretrieve(http_s,'serverdown/'+str(sername[1])+'.jar')
                findtag_remove_show_window('auto_center_text',"LOAD")
                add_show_window([['auto_center_text','Fabric核心下载完成!',(111,219),(776,27),(0,255,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["ERROR"]]])
        except:
            if daling != 114514:
                add_show_window([['auto_center_text','ERROR:500.下载时发生未知错误,可能是网络问题,链接问题或网站问题.请检查网络并重试.',(111,219),(776,27),(255,0,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["ERROR"]]])
            download = 0
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
    c=f.readtxt('data/set/core_version.txt')
    if c !="Forge":
        a = f.readtxt('data/set/ru.txt')
        n = f.readtxt('data/set/sername.txt')
        bbb=open("setup.bat","w+")
        f.writing("serverdown/begin.bat",'java -Xms'+str(a[0])+'G -Xmx'+str(a[0])+'G -jar '+str(n[1])+'.jar --nogui',0)
        thr_stF=thr.Thread(target=start_First,daemon=1)
        #####FIND2
        thr_stF.start()
    else:
        setup(c)

def show_eula():########################################
    try:
        eula = f.readtxt("serverdown/eula.txt")
        x=63
        y=180
        re_eula = []
        for i in eula:
            if len(i) > 75:
                re_eula.append(str(i[:75]))
                re_eula.append(str(i[75:]))
            else:
                re_eula.append(str(i))
        for i in re_eula:
            add_show_window([['text',str(i),(x,y),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            y=y+30
    except:
        back = confirm(text="WAR:001.未找到eula.txt.\n应该是因为服务器第一次未运行完毕.\n等待片刻重试.",title='[WAR] | '+version,buttons=['继续'])

def get_server_properties_path():
    global stserver
    Server = f.read_Server()
    Server_len = len(Server)
    if Server_len != 0:
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

def jiemiandonghua():
    ####################################播放主界面的视频及音频，未完成
    #use:xx,yy,endtr
    #bk:
    global xx
    global yy
    global endtr
    VideoCapture =  VideoFileClip('mc/nUI.byTA_JLPgui')
    sound=p.mixer.music.load("mc/zn.byTA_JLPgm")
    p.mixer.music.play()
    p.mixer.music.pause()
    p.mixer.music.play()
    while 1:
        p.time.Clock().tick(60)
        acc,add=VideoCapture.read()
        if endtr==0:
            #add=cv2.cvtColor(add, cv2.COLOR_BGR2RGB)
            #add = np.rot90(add,k=-1)
            add = p.surfarray.make_surface(add)
            add=p.transform.scale(p.transform.flip(add,False,True),(xx,yy))
            #byLP.blit(add,(0,0))
            #zujiemian()
            p.display.update()
        else:
            p.mixer.music.pause()
            break

def play_window():
    # window: [ ['window','str',(x,y),(rx,ry), ['alpha_up / alpha_down',[100 /初始数值/ , 50 /目标值/ , 1 /变化速率每帧/ , 100 /下一个目标值/] ](可选) ] ]
    # text: [ ['text','str',(x,y),(R,G,B),int_size,'str_ttf', [ '此项所带的Tag' ](可选) ] ]
    # button: [ ['button,'str_png',(x,y),(bx,by),'str_text',(R,G,B),int_size,'str_ttf',['self / png_path',[100 /初始数值/ , 50 /目标值/ , 1 /变化速率每帧/ , 100 /下一个目标值/] ](可选) ] ]
    global show_window
    global ani_window
    global tarea

    bylp.fill((27,27,27))
    a = 0
    for i in show_window:
        if i[0] == 'window':
            try:
                if i[4][0] == 'alpha_up' or i[4][0] == 'alpha_down':
                    alpha_window(i[1],i[2],i[3],i[4][0],i[4][1],a)
                        #print(show_window[0])
                else:
                    window(i[1],i[2],i[3])
            except:
                window(i[1],i[2],i[3])
        elif i[0] == 'text':
            text(i[1],i[2],i[3],i[4],i[5])
        elif i[0] == 'auto_center_text':
            auto_center_text(i[1],i[2],i[3],i[4],i[5],i[6])
        elif i[0] == 'button':
            button(i[1],i[2],i[3],i[4],i[5],i[6],i[7])
        a += 1

    if len(ani_window) != 0:
        for i in ani_window:
            window(i[1],i[2],i[3])

        #print(ani_window)

    thisver()
    p.display.update()

def buildwin(win): 
#   Int #构建界面
#   绘制目标界面序号应显示的图像
    global tarea
    global tarea_ani
    global chnum
    global stserver
    global show_window
    global ani_window
    global Server
    global Server_len
    global java_version
    tarea = []
    tarea_ani = []
    chnum = '0'
    show_window = []
    ani_window = []
    #bylp.fill((27,27,27))
    a=0

    if win == 0: #主界面  #此处显示经过优化，现在变得有点像MC里的tellraw/titleraw指令?
        show_window.extend([['window','data/background/bg_theend.png',(0,0),(0,0)]
                       ,['window','data/background/title_winter.png',(0,0),(0,0)]
                       ,['window','data/background/serverlist.png',(0,0),(0,0)]
                       ,['window','data/background/button_text.png',(0,0),(0,0)]
                       ,['button','none',(88,176),(229,48),'',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]
                       ,['button','none',(88,252),(229,48),'',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]
                       ,['button','none',(88,328),(229,48),'',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]
                       ,['button','none',(88,404),(229,48),'',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]])
        Server = f.read_Server()
        Server_len = len(Server)

        show_window.extend([['text',java_version,(630,88),(255,255,255),40,'data/HarmonyOS_Sans_SC_Bold.ttf']])

        if Server_len < 10:
            show_window.extend([['text','0'+str(Server_len),(870,98),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        else:
            show_window.extend([['text',str(Server_len),(870,98),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        if show_server < 9 and Server_len != 0:
            show_window.extend([['text','0'+str(show_server+1),(770,68),(150,249,145),55,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        elif show_server < 9 and Server_len == 0:
            show_window.extend([['text','00',(770,68),(150,249,145),55,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        else:
            show_window.extend([['text',str(show_server+1),(770,68),(150,249,145),55,'data/HarmonyOS_Sans_SC_Bold.ttf']])

        if Server_len != 0 and Server_len <=99:
            show_server_data = str(f.readtxt('.ServerData/'+str(Server[show_server])+'/core.txt')[0]
                                   +' / '+f.readtxt('.ServerData/'+str(Server[show_server])+'/version.txt')[0]
                                   +' / '+f.readtxt('.ServerData/'+str(Server[show_server])+'/core_version.txt')[0]
                                   +' ('+f.readtxt('.ServerData/'+str(Server[show_server])+'/ru.txt')[0]
                                   +'G)')
            server_icon = os.path.exists('.ServerData/'+str(Server[show_server])+'/server_icon.png')
            if server_icon == True:
                show_window.extend([['window','.ServerData/'+str(Server[show_server])+'/server_icon.png',(315,158),(0,0)]])
            else:
                cut_window('data/background/server_pt.png',str(Server[show_server]))
                show_window.extend([['window','.ServerData/'+str(Server[show_server])+'/server_icon.png',(315,158),(0,0)]])
            show_window.extend([['window','data/background/server_name.png',(535,170),(0,0)]
                                ,['window','data/background/serverchange.png',(0,0),(0,0)]
                                ,['text',str(Server[show_server]),(540,168),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']
                                ,['text',show_server_data,(540,218),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']
                                ,['text','服务器列表',(358,165),(255,255,255,100),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                                ,['button','data/b_title.png',(570,500),(150,40),'启动',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                                ,['button','data/b_title.png',(740,500),(150,40),'移除',(255,0,0),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                                ,['button','none',(315,531),(90,24),'上一个',(0,0,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/background/serverchange_bg.png']]
                                ,['button','none',(405,531),(90,24),'下一个',(0,0,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/background/serverchange_bg.png']]
                                ,['button','data/b_re_name.png',(890,170),(35,32),'',(0,0,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_re_name.png']]
                                ,['button','data/b_re_icon.png',(886,213),(35,32),'',(0,0,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_re_icon.png']]])
        elif Server_len == 0:
            show_window.extend([['text','暂未创建服务器...',(500,330),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        elif Server_len > 99:
            show_window.extend([['text','创建服务器过多...',(500,330),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
    

    elif win == 2: #服务器配置
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/set_world.png',(0,0),(0,0)]
                            ,['button','none',(58,46),(200,44),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                            ,['button','data/b_title_next.png',(615,53),(32,32),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]
                            ,['button','none',(58,113),(200,44),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(495,153),(462,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(495,208),(457,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(495,263),(452,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(495,318),(447,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']])

        Server = f.read_Server()
        Server_len = len(Server)

        if Server_len == 0:
            show_window.extend([['text','暂未创建服务器...',(460,102),(249,238,145),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        else:
            setting_server = str(Server[stserver])
            setting_filepath = '.ServerFile/'+setting_server+'/server.properties'
            show_window.extend([['text',setting_server,(460,102),(150,249,145),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            #可输入选项
            setting_obj=['level-seed=','level-name=','gamemode=','difficulty=']
            setting_objxyz=[[515,153],[515,208],[515,263],[515,318]]
            a=0
            for i in setting_obj:
                text_1=svset.server_properties_data(setting_filepath,i)
                if len(text_1) >= 32:
                    show_window.extend([['text',str(text_1[:32])+'...',(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
                else:
                    show_window.extend([['text',text_1,(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
                a=a+1
            #仅有'T','F'的选项
            setting_obj=['force-gamemode=','allow-nether=','enable-command-block=','pvp=','spawn-npcs=','spawn-animals=','spawn-monsters=','generate-structures=']
            setting_objxyz=[[575,390],[575,435],[575,480],[575,525],[845,390],[845,435],[845,480],[845,525]]
            a=0
            for i in setting_obj:
                text_1 = str(svset.server_properties_data(setting_filepath,i))
                show_window.extend([['button','data/b_'+text_1+'.png',(setting_objxyz[a][0],setting_objxyz[a][1]),(81,29),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']])
                a=a+1

            if Server_len < 10:
                show_window.extend([['text','0'+str(Server_len),(170,523),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            else:
                show_window.extend([['text',str(Server_len),(170,523),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            if show_server < 9:
                show_window.extend([['text','0'+str(stserver+1),(100,513),(150,249,145),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            else:
                show_window.extend([['text',str(stserver+1),(100,513),(150,249,145),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        

    elif win == 21:
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/set_server.png',(0,0),(0,0)]
                            ,['button','none',(58,46),(200,44),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                            ,['button','data/b_title_back.png',(615,53),(32,32),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]
                            ,['button','none',(58,113),(200,44),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(529,153),(428,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(529,208),(422,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(529,263),(417,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(495,318),(447,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['button','none',(664,373),(273,38),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        Server = f.read_Server()
        Server_len = len(Server)
        if Server_len == 0:
            show_window.extend([['text','暂未创建服务器...',(460,102),(249,238,145),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        else:
            setting_server = str(Server[stserver])
            setting_filepath = '.ServerFile/'+setting_server+'/server.properties'
            show_window.extend([['text',setting_server,(460,102),(150,249,145),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            #可输入选项
            setting_obj=['motd=','server-port=','max-players=','simulation-distance=','player-idle-timeout=']
            setting_objxyz=[[515,153],[515,208],[515,263],[515,318],[655,373]]
            a=0
            for i in setting_obj:
                text_1=svset.server_properties_data(setting_filepath,i)
                if len(text_1) >= 32:
                    show_window.extend([['text',str(text_1[:32])+'...',(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
                else:
                    show_window.extend([['text',text_1,(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']])
                a=a+1
            #仅有'T','F'的选项
            setting_obj=['online-mode=','white-list=','prevent-proxy-connections=','allow-flight=']
            setting_objxyz=[[536,435],[536,480],[656,525],[846,435]]
            a=0
            for i in setting_obj:
                text_1 = str(svset.server_properties_data(setting_filepath,i))
                show_window.extend([['button','data/b_'+text_1+'.png',(setting_objxyz[a][0],setting_objxyz[a][1]),(81,29),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']])
                a=a+1

            if Server_len < 10:
                show_window.extend([['text','0'+str(Server_len),(170,523),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            else:
                show_window.extend([['text',str(Server_len),(170,523),(255,255,255),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            if show_server < 9:
                show_window.extend([['text','0'+str(stserver+1),(100,513),(150,249,145),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])
            else:
                show_window.extend([['text',str(stserver+1),(100,513),(150,249,145),35,'data/HarmonyOS_Sans_SC_Bold.ttf']])

 
    elif win == 3: #程序设置
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/pgm_setting.png',(0,0),(0,0)]
                            ,['button','data/b_back.png',(20,20),(150,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                            ,['button','data/b_title.png',(72,212),(195,50),'可行性检验',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                            ,['button','data/b_title.png',(72,282),(195,50),'重置检验文件',(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]])
        

    elif win == 4: #关于作者
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/about_authors.png',(0,0),(0,0)]
                            ,['button','data/b_back.png',(20,20),(150,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                        ,['button','none',(684,168),(225,52),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]
                        ,['button','none',(684,358),(225,52),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]])



    elif win == 11: #开启服务器——选择核心
        d=str(f.readtxt('data/set/ru.txt')[0])
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/op_server_1.png',(0,0),(0,0)]
                            ,['button','data/b_back.png',(20,20),(150,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                            ,['button','data/b_next.png',(820,538),(150,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                       ,['button','none',(118,152),(135,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(300,152),(135,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(300,290),(140,41),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(113,290),(140,41),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(239,442),(64,32),d,(255,255,255),25,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]
                       ,['button','none',(196,442),(32,32),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]
                       ,['button','none',(314,442),(32,32),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]
                       ,['button','none',(240,20),(260,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(267,513),(140,41),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]])
        ru_x = int(34*(int(d)-1))
        if ru_x > 306:
            ru_x = 306
        show_window.extend([['window','data/lod_s.png',(113+ru_x,410),(16,12)]])
        show_server_all_data()


    elif win == 12: #开启服务器——下载核心
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/op_server_2.png',(0,0),(0,0)]
                            ,['button','data/b_back.png',(20,20),(150,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                            ,['button','data/b_next.png',(820,538),(150,40),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['self']]
                       ,['button','none',(301,295),(150,45),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(550,295),(150,45),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_title.png']]
                       ,['button','none',(45,370),(910,130),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']
                       ,['text','Tip:  点击此处框框范围内,可以随机切换Tip语句哦!',(60,390),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf',['TIP']]])


    elif win == 13: #开启服务器__初次启动及修改eula
        start_f = f.readtxt('data/set/start_svrf.txt')
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]])
        if int(start_f[0]) == 0:
            show_window.extend([['window','data/eula_1.png',(0,0),(0,0)]
                                ,['button','data/Loading.png',(0,0),(1000,600),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf']])
        elif int(start_f[0]) == 1:
            show_window.extend([['window','data/eula_1.png',(0,0),(0,0)]
                        ,['button','none',(291,474),(200,45),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]
                        ,['button','none',(46,474),(200,45),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]
                        ,['button','none',(537,474),(200,45),'',(255,255,255),15,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg_2.png']]])
    

    elif win == 14: #服务器开设完成
        a=str(f.readtxt('data/set/sername.txt')[1])
        b=str(f.readtxt('data/set/core.txt')[0])
        c=str(f.readtxt('data/set/core_version.txt')[0])
        d=str(f.readtxt('data/set/ru.txt')[0])
        e=str(f.readtxt('data/set/version.txt')[0])
        if b in ['Spigot','Paper']:
            b = '插件服 | ' + b
        elif b in ['Fabric','Forge']:
            b = '模组服 | ' + b
        c = e + ' | ' + c
        d = d + ' G'
        show_window.extend([['window','data/background/bg_theend_2.png',(0,0),(0,0)]
                            ,['window','data/finish.png',(0,0),(0,0)]
                            ,['auto_center_text',a,(101,245),(800,30),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']
                            ,['auto_center_text',b,(101,307),(800,30),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']
                            ,['auto_center_text',c,(101,369),(800,30),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']
                            ,['auto_center_text',d,(101,430),(800,30),(255,255,255),20,'data/HarmonyOS_Sans_SC_Bold.ttf']
                            ,['button','none',(400,490),(200,42),'',(255,255,255),28,'data/HarmonyOS_Sans_SC_Bold.ttf',['data/b_bg.png']]])

    t_area_append()

#  ==================================
#          BUILDING WINDOWS
#  ==================================

version=f.readtxt('Version.txt')[0]
maker='TA_JLPawa'

p.init()

win = 0
tarea = []
tarea_ani = []
charea = []
chnum = '0'
daling = 0
stserver = 0
custom = 'False'
refresh = True
show_window = []
ani_window = []
show_server = 0
Server = f.read_Server()
Server_len = len(Server)
#########fps = int(f.readtxt_find('data/set_pgm/set_pgm.txt','界面刷新帧率'))
fps = str(f.readtxt_find('data/set_pgm/set_pgm.txt','界面刷新帧率'))
java_version = str(f.get_java_version())
# win=0: 主界面界面序号
# tarea: Test Area,为鼠标行动xy坐标检测列表
# tarea_ani: Trst Area Animation,为需要播放动画的动画数据
# charea: choose area,为选择框检测坐标
# chnum: choose number,为选择框检测序号
# daling: 是否正在下载核心
# stserver: 正在配置的服务器序号
# custom: 是否为自定义服务器
# refresh: 是否启用界面刷新
# show_window: 正在显示的图像
# ani_window: 正在播放的动画
# show_server: 正在显示的服务器
# Server_len: 已开设的服务器数量
# fps: 界面刷新帧率
# java_version: 使用的Java版本

bylp=p.display.set_mode((1000,600))            #1000,600

p.display.set_caption('Py Minecraft Server 开服器','By TA_JLPawa')
icon=p.image.load('data/icon.png')
p.display.set_icon(icon)
p.event.set_allowed([p.QUIT, p.MOUSEBUTTONUP, p.MOUSEMOTION])

buildwin(win)

try:
    try_read_serverlist = f.readtxt('.ServerList/ServerList.txt')
except:
    shutil.copytree('ServerList(backup_copy)','.ServerList')

clock = p.time.Clock()


#  ==================================
#            BUTTON EVENT
#  ==================================

while refresh:
    for e in p.event.get():
        if e.type==p.QUIT:
            refresh = False
            p.quit()
            sys.exit()

        if e.type==p.MOUSEMOTION:
            mox,moy=p.mouse.get_pos()

            tarea_ani_len = len(tarea_ani)
            tarea_ani_num = 0

            for i in tarea_ani:
                if mox in range(int(i[0]),int(i[2])) and moy in range(int(i[1]),int(i[3])):
                    # 如果鼠标在对应范围内，添加动画
                    if len(ani_window) == 0:
                        ani_window.append(['window',i[4],(i[0],i[1]),(int(i[2]-i[0]),int(i[3]-i[1])),[str(tarea_ani_num)]])
                        #print(tarea_ani_num)
                        #以下是每个界面部分按钮特有的动画
                        if win == 0 and tarea_ani_num <= 3:
                            ani_window.append(['window','data/background/b_bg_title_main_2.png',(i[0]-57,i[1]),(48,48),[str(tarea_ani_num)]])
                
                else:
                    # 如果鼠标不在对应范围内，移除动画
                    if len(ani_window) != 0:
                        if str(tarea_ani_num) in ani_window[0][4]:
                            ani_window = []

                tarea_ani_num = tarea_ani_num + 1

        if e.type==p.MOUSEBUTTONUP:
            mx,my=p.mouse.get_pos()

            print(mx,my) #打印鼠标点击位置(仅限程序开发辅助)######################测试语句

            if win == 0: #主界面
                tarea_len = len(tarea)
                if tarea_len > 4:
                    if mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                        Server_Run = str(Server[show_server])
                        back = confirm(text="你是否确定启动服务器 "+Server_Run+" ?.",title=version,buttons=['暂不启动','确定'])
                        if back == '确定':
                            f.writing('start_Num.txt',['ANSI占位用句',Server_Run],1)
                            thr_stexe=thr.Thread(target=start_exe,daemon=1)
                            thr_stexe.start()
                    elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                        Server_Run = str(Server[show_server])
                        back = confirm(text="你是否移除服务器 "+Server_Run+" ?.\n这将删除此程序目录下的所有有关此服务器的文件!\n请确保你在其它地方为服务器文件做了备份!!",title=version,buttons=['暂不移除','确定'])
                        if back == '确定':
                            back = confirm(text="你真的想要移除服务器 "+Server_Run+" 吗?.\n此操作不可挽回!!!",title=version,buttons=['暂不移除','我真的确定!!'])
                        if back == '我真的确定!!':
                            svset.delete_server(Server_Run)
                            back = confirm(text=Server_Run+" 已被移除!!",title=version,buttons=['确定'])
                            Server = f.read_Server()
                            Server_len = len(Server)
                            try:
                                Server_Run = str(Server[show_server])
                            except:
                                if Server_len != 0:
                                    show_server = show_server -1
                                    Server_Run = str(Server[show_server])
                            win = 0
                            buildwin(win)
                    elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                        show_server = show_server-1
                        if show_server < 0 :
                            show_server = Server_len-1
                        win = 0
                        buildwin(win)
                    elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                        show_server = show_server+1
                        if show_server == Server_len :
                            show_server = 0
                        win = 0
                        buildwin(win)
                    elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                        Server_Run = str(Server[show_server])
                        back = str(prompt(text='请输入想要重命名的名称.',title=version,default=Server_Run))
                        if back == 'None':
                            back2 = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
                        elif back == '':
                            back2 = confirm(text="输入不能为空哦~.",title=version,buttons=['继续'])
                        else:
                            back2 = confirm(text="确定要将服务器 ["+Server_Run+'] 重命名为 ['+back+'] 吗?',title=version,buttons=['确定','取消'])
                        if back2 == '确定':
                            Server_list = f.readtxt('.ServerList/ServerList.txt')
                            if back in Server_list:
                                back2 = confirm(text='此服务器已经有啦!重命名操作已取消~',title=version,buttons=['确定'])
                            else:
                                f.writing('.ServerData/'+Server_Run+'/sername.txt',['ANSI占位用句',back],1)
                                os.rename('.ServerData/'+Server_Run,'.ServerData/'+back)
                                os.rename('.ServerFile/'+Server_Run,'.ServerFile/'+back)
                                for i in Server_list:
                                    if i == Server_Run:
                                        index = Server_list.index(i)
                                Server_list[index] = back
                                f.writing('.ServerList/ServerList.txt',Server_list,1)
                                Server_Run = back
                                buildwin(win)
                    elif mx in range(int(tarea[9][0]),int(tarea[9][2])) and my in range(int(tarea[9][1]),int(tarea[9][3])):
                        Server_Run = str(Server[show_server])
                        pt_path = f.choose_file()
                        if pt_path != 'None':
                            cut_window(pt_path,Server_Run)
                            buildwin(win)

                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    testset = int(f.readtxt_find('data/set_pgm/set_pgm.txt','是否完成Java检测(0否1通过2未通过)'))

                    if testset == 0:  #未检验
                        back = confirm(text="在开设服务器之前,非常建议运行一次可行性检验!"+'\n'+'否则程序有可能因为个人配置而报错!',title=version,buttons=['开始','跳过','返回'])
                        if back == '开始':
                            f.testofset()
                        elif back == '跳过':
                            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
                            f.writing_find('data/set_pgm/set_pgm.txt','1','是否完成Java检测(0否1通过2未通过)')
                            win=11
                            svset.reset_data()
                            buildwin(win)

                    elif testset == 1: #已检验
                        try:
                            Server = f.readtxt('.ServerList/ServerList.txt')
                        except:
                            Server = ['ANSI占位用句']
                        if len(Server) <= 99:
                            win=11
                            svset.reset_data()
                            buildwin(win)
                        else:
                            back = confirm(text="创建的服务器过多(最多99个),如需要创建新服务器,请移除一个现有的服务器.",title=version,buttons=['明白'])

                    elif testset == 2: #未通过
                        back = confirm(text="上次可行性检验未通过,是否开始重检测?"+'\n'+'请确保你的错误已修复!',title=version,buttons=['开始','跳过','返回'])
                        if back == '开始':
                            f.testofset()
                        elif back == '跳过':
                            back = confirm(text="你可以在‘程序设置’中进行检验数据重置或重检验.",title=version,buttons=['明白'])
                            f.writing('data/set_pgm/set_pgm.txt','1','是否完成Java检测(0否1通过2未通过)')
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

            elif win == 2 and Server_len != 0:
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
                    set_server_properties(2,0,'level-seed=','请输入世界种子\n请注意,更换种子后须重创建世界才能生效')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    set_server_properties(2,0,'level-name=','请输入世界名称\n将作为世界名称及其文件夹名')
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    set_server_properties(2,0,'gamemode=','请输入默认游戏模式\n可输入\n[survival-生存,creative-创造,adventure-冒险,spectator-旁观]')
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    set_server_properties(2,0,'difficulty=','请输入目标难度\n可输入\n[peaceful-和平,easy-简单,normal-普通,hard-困难]')
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

            elif win == 2 and Server_len == 0:
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

            elif win == 21 and Server_len != 0:########################################
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
                    set_server_properties(21,0,'motd=','请输入要展示的服务器信息(为Unicode码)\n可输入的字符数 [0-59]')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    set_server_properties(21,0,'server-port=','请输入服务器(监听的)端口号\n可输入的范围 [1-65534]')
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    set_server_properties(21,0,'max-players=','请输入服务器支持的最大玩家数量')
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    set_server_properties(21,0,'simulation-distance=','请输入玩家各个方向上可视的区块数量(以玩家为中心的半径)\n可输入的范围 [3-32]')
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                    set_server_properties(21,0,'player-idle-timeout=','请输入玩家被允许的最长挂机时间(单位:分钟)\n设置为0表示关闭此功能')
                elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                    set_server_properties(21,1,'online-mode=',0)
                elif mx in range(int(tarea[9][0]),int(tarea[9][2])) and my in range(int(tarea[9][1]),int(tarea[9][3])):
                    set_server_properties(21,1,'white-list=',0)
                elif mx in range(int(tarea[10][0]),int(tarea[10][2])) and my in range(int(tarea[10][1]),int(tarea[10][3])):
                    set_server_properties(21,1,'prevent-proxy-connections=',0)
                elif mx in range(int(tarea[11][0]),int(tarea[11][2])) and my in range(int(tarea[11][1]),int(tarea[11][3])):
                    set_server_properties(21,1,'allow-flight=',0)

            elif win == 21 and Server_len == 0:
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

            elif win == 3:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    back = confirm(text='确定开始运行一次可行性检验吗?',title=version,buttons=['开始','返回'])
                    if back == '开始':
                        f.testofset()
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    f.writing_find('data/set_pgm/set_pgm.txt','0','是否完成Java检测(0否1通过2未通过)')
                    back = confirm(text="可行性检验数据文件(data/set_pgm/set_pgm.txt/是否完成Java检测(0否1通过2未通过))项目已重置.",title=version,buttons=['明白'])

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
                        try:
                            win=13
                            buildwin(win)
                            svset.custom_server()
                            start_F()
                        except:
                            win=0
                            buildwin(win)
                            back = confirm(text='ERROR.'+'\n'+'无法寻找到名为你输入名字的核心jar文件.',title='[ERROR] | '+version,buttons=['继续'])     
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    if chnum != '插件服' and custom == 'False':
                        chooselist(['Spigot','Paper']
                                ,[[255,255,255],[255,255,255]]
                                ,[18,18]
                                ,['data/HarmonyOS_Sans_SC_Bold.ttf','data/HarmonyOS_Sans_SC_Bold.ttf'])
                        chnum = '插件服'
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    if chnum != '模组服' and custom == 'False':
                        chooselist(['Fabric','Forge']
                                ,[[255,255,255],[255,255,255]]
                                ,[18,18]
                                ,['data/HarmonyOS_Sans_SC_Bold.ttf','data/HarmonyOS_Sans_SC_Bold.ttf'])
                        chnum = '模组服'
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    if chnum != 'mc版本' and custom == 'False':
                        chooselist(['打开输入界面','查询所选核心支持版本','重置已保存的数据']
                                ,[[255,255,255],[255,255,255],[255,255,255]]
                                ,[18,18,18]
                                ,['data/HarmonyOS_Sans_SC_Bold.ttf','data/HarmonyOS_Sans_SC_Bold.ttf','data/HarmonyOS_Sans_SC_Bold.ttf'])
                        chnum = 'mc版本'
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    a=f.readtxt('data/set/core.txt')
                    if chnum != '核心版本' and custom == 'False':
                        if a[0] == 'Spigot':
                            back = confirm(text="Spigot核心无需再设置核心版本.",title=version,buttons=['继续'])
                        elif a[0] == 'Paper' or a[0] == 'Fabric' or a[0] == 'Forge':
                            chooselist(['开始输入',"将已保存的数据重置为0","查询Forge可选核心版本 (仅Forge可用)"]
                                    ,[[255,255,255],[255,255,255],[255,255,255]]
                                    ,[18,18,18]
                                    ,['data/HarmonyOS_Sans_SC_Bold.ttf','data/HarmonyOS_Sans_SC_Bold.ttf','data/HarmonyOS_Sans_SC_Bold.ttf'])
                            chnum = '核心版本'
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    f.ruset(114514)
                    buildwin(win)
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                    f.ruset(1)
                    buildwin(win)
                elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                    f.ruset(2)
                    buildwin(win)
                elif mx in range(int(tarea[9][0]),int(tarea[9][2])) and my in range(int(tarea[9][1]),int(tarea[9][3])):
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
                                show_server_all_data()
                            else:
                                back = confirm(text="目标服务器名称已存在,请重新命名! ",title=version,buttons=['继续'])
                elif mx in range(int(tarea[10][0]),int(tarea[10][2])) and my in range(int(tarea[10][1]),int(tarea[10][3])):
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
                            f.writing('data/set/core.txt','Custom',0)
                            f.writing('data/set/core_version.txt','Custom',0)
                            f.writing('data/set/version.txt','Custom',0)
                            show_server_all_data()
                        else:
                            back = confirm(text="目标服务器名称已存在,请重新命名! ",title=version,buttons=['继续'])


                if chnum == 'mc版本' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.versionset()
                        show_server_all_data()
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        sercore = str(f.readtxt('data/set/core.txt')[0])
                        ver_txt = f.readtxt('data/ver_'+sercore+'.txt')
                        back = confirm(text="你所选的 ["+sercore+"] 核心支持的MC版本如下.\n"+str(ver_txt),title=version,buttons=['继续'])
                    elif mx in range(int(charea[2][0]),int(charea[2][2])) and my in range(int(charea[2][1]),int(charea[2][3])):
                        f.writing('data/set/version.txt','1.19.2',0)
                        back = confirm(text="已恢复默认值'1.19.2'于data/set/version.txt",title=version,buttons=['继续'])
                        show_server_all_data()
                elif chnum == '插件服' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.coreset('Spigot')
                        show_server_all_data()
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        f.coreset('Paper')
                        show_server_all_data()
                elif chnum == '模组服' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        f.coreset('Fabric')
                        show_server_all_data()
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        #f.coreset('Forge')
                        #show_server_all_data()
                        ###FIND1
                        back = confirm(text="Forge暂时不受支持."+'\n'+"因为其开服流程与其他类型服务器步骤不同."+'\n'+"请等待后续更新...",title=version,buttons=['继续'])
                elif chnum == '核心版本' and custom == 'False':
                    if mx in range(int(charea[0][0]),int(charea[0][2])) and my in range(int(charea[0][1]),int(charea[0][3])):
                        #try:
                        f.CVset()
                        show_server_all_data()
                        #except:
                            #back = confirm(text="ERROR:114.在设置核心版本时发生未知错误.",title='[ERROR] | '+version,buttons=['继续'])
                    elif mx in range(int(charea[1][0]),int(charea[1][2])) and my in range(int(charea[1][1]),int(charea[1][3])):
                        f.writing('data/set/core_version.txt','0',0)
                        back = confirm(text="已将已保存的数据重置为'0'",title=version,buttons=['继续'])
                        show_server_all_data()
                    elif mx in range(int(charea[2][0]),int(charea[2][2])) and my in range(int(charea[2][1]),int(charea[2][3])):
                        back = confirm(text="Forge支持的核心版本如下.\n1.20.4对应:[49.0.28~49.0.3]\n1.20.3对应:[49.0.2~49.0.1]\n1.20.2对应:[48.1.0~48.0.0]\n1.20.1对应:[47.2.30~47.0.0]\n1.20对应:[46.0.14~46.0.1]",title=version,buttons=['继续'])

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
                        findtag_remove_show_window('window',"LOAD")
                        findtag_remove_show_window('auto_center_text',"LOAD")
                        reload_add_show_window([['auto_center_text','PAUSE.',(111,219),(776,27),(255,0,0),15,'data/HarmonyOS_Sans_SC_Bold.ttf',["ERROR"]]])
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    tip('data/z_tip.txt',[60,390],25)
                    
            elif win == 13:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    start_f = f.readtxt('data/set/start_svrf.txt')
                    if int(start_f[0]) == 1:
                        buildwin(win)
                        show_eula()
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    try:
                        f.reset_eula()
                        win=14
                        buildwin(win)
                    except:
                        back = confirm(text="WAR:001.未找到eula.txt.\n应该是因为服务器第一次未运行完毕.\n等待片刻重试.",title='[WAR] | '+version,buttons=['继续'])
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    abmk.visit('Minecraft_eula')

            elif win == 14:
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    custom = 'False'
                    svset.get_new_server()
                    buildwin(win)

    play_window()

    clock.tick(30)

                    
########################################
'''
还没想好写什么......
'''
########################################
