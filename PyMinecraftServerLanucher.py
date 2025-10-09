
#  ==================================
#             IMPORT LIST
#  ==================================

import os
import time as t
import sys
import threading as thr
import pygame as p
import random
import subprocess
import queue
import urllib
import urllib.request
import shutil
import cv2
import numpy as np
from pyautogui import confirm,prompt
from typing import *

from modules import functions as f
from modules import abmk
from modules import serversetting as svset
from modules import file_operation
from modules import button_event as be



#  ==================================
#            FUNCTION LIST
#  ==================================


class ImageManager:

    '''
    图片统一加载\n
    (注意!加载自定义图像时无法加载其缩放版本,因为缩放的像素是写入到程序中的,请等待后续版本)\n
    (加载的自定义图像统一为原图,没有任何缩放版本,使用第一种get方法来调用)

    folder_path: 输入一个str,为全部目标图片所在的文件夹路径
    use_alpha: 是否读取图片透明度
    scale_map: 输入一个字典,记录所需要的图像缩放大小

    scale_map格式:
    
    scale_map = {
        'a': [(1, 2), (3, 4), (5, 6), ...]
        'b': [(7, 8), ...]
        ...
    }

    存储图片的images字典格式:

    images = {
        'a': xxx,
        'b': {
            'original': xxx,
            (1, 2): xxx,
            (3, 4): xxx,
            ...
        }
        ...
    }

    调用get方法的方式:

    screen.blit(images.get("a"), (screen_x, screen_y))      此方法绘制没有任何缩放版本的图片\n
    screen.blit(images.get("a", 'o'), (screen_x, screen_y))      此方法绘制有缩放版本但未经过缩放的图片(原图)\n
    screen.blit(images.get("a", (scale_x, scale_y)), (screen_x, screen_y))      此方法绘制带缩放的图片

    '''

    def __init__(self, folder_path, use_alpha=True, scale_map=None, alpha_map=None):
        self.images = {}    #   图片存储到字典images
        self.use_alpha = use_alpha
        self.scale_map = scale_map
        self.alpha_map = alpha_map
        self.load_all(folder_path)

    def load_all(self, folder_path):

        for filename in os.listdir(folder_path):
            path = os.path.join(folder_path, filename)
            
            if os.path.isdir(path):     #   如果文件是文件夹，则遍历此子文件夹里的文件
                self.load_all(path)

            else:   #   如果不是文件夹，检测是否是指定格式图片，如果是则载入字典
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):

                    img = p.image.load(path)
                    img = img.convert_alpha() if self.use_alpha else img.convert()
                    name = os.path.splitext(filename)[0]

                    # 根据 scale_map 缩放
                    if self.scale_map and name in self.scale_map:
                        self.images[name] = {}
                        self.images[name+'(original)'] = img

                        for size in self.scale_map[name]:
                            scaled = p.transform.smoothscale(img, size)
                            self.images[name][size] = scaled

                    else:
                        self.images[name] = img

        #print(str(self.images))

    def get(self, name, size=None):
        if size == None:
            return self.images.get(name)
        else:
            return self.images.get(name, {}).get(size)
        


class FontManager:
    '''
    字体统一加载\n
    (注意!暂时无法加载自定义字体,因为加载的字号是写入到程序中的,请等待后续版本)\n
    (自定义的字体会被识别到,但是不会加载该字体)

    folder_path: 输入一个str,为全部目标字体文件所在的文件夹路径
    size_map: 输入一个字典,记录所需要的字体字号

    size_map格式:

    size_map = {
        'a': [1, 2, 3, ...]
        'b': [4, 5, 6, ...]
        ...
    }

    存储文字的fonts字典格式

    fonts = {
        'a': {
            1: xxx,
            2: xxx,
            3: xxx,
            ...
        }
        ...
    }

    调用get方法的方式:

    font = fonts.get("a", size)      此方法获取指定字号的文字

    '''
    def __init__(self, folder_path, size_map=None):
        self.fonts = {}    #   图片存储到字典fonts
        self.size_map = size_map
        self.load_all(folder_path)
        

    def load_all(self, folder_path):

        for filename in os.listdir(folder_path):
            path = os.path.join(folder_path, filename)
            
            if os.path.isdir(path):     #   如果文件是文件夹，则遍历此子文件夹里的文件
                self.load_all(path)

            else:   #   如果不是文件夹，检测是否是指定格式图片，如果是则载入字典
                if filename.lower().endswith((".ttf")):

                    name = os.path.splitext(filename)[0]
                    self.fonts[name] = {}

                    # 根据 size_map 设置文字大小

                if self.size_map and name in self.size_map:
                    for size in self.size_map[name]:
                        font = p.font.Font(path, size)
                        self.fonts[name][size] = font

        #print(str(self.fonts))

    def get(self, name, size=15):
        return self.fonts.get(name, {}).get(size)



class BackgroundFollower:

    #  背景鼠标跟踪效果

    def __init__(self, image_path, screen, window_size, ease=0.05 , start=True):
        self.window_width, self.window_height = window_size
        self.screen = screen
        self.start = start

        # 加载背景图
        self.background = p.image.load(image_path).convert()
        self.bg_width, self.bg_height = self.background.get_size()

        # 可移动最大偏移
        self.max_offset_x = self.bg_width - self.window_width
        self.max_offset_y = self.bg_height - self.window_height

        # 当前偏移
        self.offset_x = self.max_offset_x // 2
        self.offset_y = self.max_offset_y // 2

        self.ease = ease

    def update(self):

        if self.start == True:

            # 鼠标位置
            mouse_x, mouse_y = p.mouse.get_pos()
            dx = (mouse_x - self.window_width / 2) / (self.window_width / 2)
            dy = (mouse_y - self.window_height / 2) / (self.window_height / 2)

            # 目标偏移（反向）
            target_x = self.max_offset_x * dx / 2 + self.max_offset_x / 2
            target_y = self.max_offset_y * dy / 2 + self.max_offset_y / 2

            # 缓动
            self.offset_x += (target_x - self.offset_x) * self.ease
            self.offset_y += (target_y - self.offset_y) * self.ease

            # 限制范围
            self.offset_x = max(0, min(self.offset_x, self.max_offset_x))
            self.offset_y = max(0, min(self.offset_y, self.max_offset_y))

            # 绘制
            self.screen.blit(self.background, (-self.offset_x, -self.offset_y))
        
        else:
            self.screen.blit(self.background, (-self.offset_x, -self.offset_y))



class PygameConsoleOverlay:
    '''
    集成控制台效果

    '''
    def __init__(self, command=["begin.bat"], size=(800, 600), font_name="consolas", font_size=15, bg='无'):
        self.WIDTH, self.HEIGHT = size
        self.FONT_SIZE = font_size

        try:
            font_name = font_name.replace('.ttf','')
            self.FONT = fonts.get(font_name, self.FONT_SIZE)
            if self.FONT == None:
                font_name = 'data/fonts/'+font_name+'.ttf'
                self.FONT = p.font.Font(font_name, self.FONT_SIZE)
        except:
            font_name="consolas"
            self.FONT = p.font.SysFont(font_name, self.FONT_SIZE)

        self.LINE_HEIGHT = self.FONT.get_linesize()
        self.INPUT_HEIGHT = self.LINE_HEIGHT + 10
        self.SCROLLBAR_WIDTH = 12
        self.PADDING = 5

        self.screen = p.Surface(size)

        if bg != '无':
            bg = bg.replace('.png','')
            self.bg = images.get(bg)
        else:
            self.bg = None

        self.output_lines = []
        self.render_cache = []

        self.highlight_keywords = [["error", (255, 0, 0)], 
                                    ["decode error", (255, 0, 0)],
                                    ["[UTF-8]", (255, 0, 0)],
                                    ["info", (0, 255, 0)], 
                                    ["warn", (255, 255, 0)], 
                                    ["server thread", (0, 0, 255)],
                                    ["servermain", (0, 0, 255)],
                                    ["worker-main", (0, 0, 255)],
                                    ["starting server", (0, 255, 0)],
                                    ["done", (0, 255, 0)]]
        
        self.line_highlight_keywords = [["java", (255, 0, 255)], 
                                        ["building", (198, 0, 225)], 
                                        ["done", (0, 255, 105)],
                                        [">", (0, 230, 255)],
                                        ["stopping", (198, 0, 225)],
                                        ["saving", (198, 0,  225)],
                                        ["saved", (198, 0, 225)]]

        self.scroll_y = 0
        self.scroll_x = 0
        self.dragging_v = False
        self.dragging_h = False
        self.drag_offset_y = 0
        self.drag_offset_x = 0

        self.visible_height = self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH - self.PADDING

        self.input_text = ""
        self.last_command = ""

        self.visible = False

        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            #text=True,
            bufsize=1,
            #encoding='gbk',
            #errors='replace'
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        self.output_queue = queue.Queue()
        self.thread = thr.Thread(target=self.read_from_process, daemon=True)
        self.thread.start()

    def read_from_process(self):
        while True:
            line = self.process.stdout.readline()
            if line:
                try:
                    line = line.decode('gbk')
                except:
                    try:
                        line = '[UTF-8]' + line.decode('utf-8')
                    except:
                        line = 'DECODE ERROR'
                self.output_queue.put(line)
            else:
                break

    def update_output(self):
        """
        从子进程读取新的输出，并更新缓存。
        如果非拖动状态，则自动滚动到底部。
        返回是否有新输出。
        """
        updated = False
        while not self.output_queue.empty():
            line = self.output_queue.get()
            self.output_lines.append(line)
            self.render_cache.append(self.render_highlighted_line(line.rstrip()))
            updated = True

        if updated:
            self.total_lines = len(self.render_cache)
            self.max_scroll_y = max(0, self.total_lines * self.LINE_HEIGHT - self.visible_height)
            #self.max_line_width = max((surf.get_width() for surf in self.render_cache), default=0)
            #self.max_scroll_x = max(0, self.max_line_width - self.visible_width)

            # 自动滚动到底部（如果没有在拖动）
            if not self.dragging_v:
                self.scroll_y = self.max_scroll_y
            #if not self.dragging_h:
            #    self.scroll_x = self.max_scroll_x

        return updated

    def handle_event(self, event):
        if event.type == p.KEYDOWN:
            if event.key == p.K_RETURN:
                self.process.stdin.write((self.input_text + "\n").encode('gbk'))
                self.process.stdin.flush()
                self.output_lines.append("> " + self.input_text)
                self.render_cache.append(self.render_highlighted_line("> " + self.input_text))
                self.last_command = self.input_text
                self.input_text = ""
            elif event.key == p.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == p.K_UP:
                self.input_text = self.last_command
            elif event.key == p.K_DOWN:
                self.input_text = ""
            else:
                self.input_text += event.unicode

        elif event.type == p.MOUSEBUTTONDOWN:
            x, y = event.pos
            if self.WIDTH - self.SCROLLBAR_WIDTH <= x <= self.WIDTH:
                if self.PADDING + self.scroll_bar_y <= y <= self.PADDING + self.scroll_bar_y + self.scroll_bar_height:
                    self.dragging_v = True
                    self.drag_offset_y = y - self.scroll_bar_y
            if self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH <= y <= self.HEIGHT - self.INPUT_HEIGHT:
                if self.PADDING + self.scroll_bar_x <= x <= self.PADDING + self.scroll_bar_x + self.scroll_bar_width:
                    self.dragging_h = True
                    self.drag_offset_x = x - self.scroll_bar_x
            if event.button == 4:
                self.scroll_y = max(0, self.scroll_y - self.LINE_HEIGHT)
            elif event.button == 5:
                self.scroll_y = min(self.max_scroll_y, self.scroll_y + self.LINE_HEIGHT)

        elif event.type == p.MOUSEBUTTONUP:
            self.dragging_v = self.dragging_h = False

        elif event.type == p.MOUSEMOTION:
            if self.dragging_v:
                _, y = event.pos
                self.scroll_bar_y = y - self.drag_offset_y
                self.scroll_bar_y = max(0, min(self.visible_height - self.scroll_bar_height, self.scroll_bar_y))
                self.scroll_y = int(self.scroll_bar_y * self.max_scroll_y / max(1, self.visible_height - self.scroll_bar_height))
            if self.dragging_h:
                x, _ = event.pos
                self.scroll_bar_x = x - self.drag_offset_x
                self.scroll_bar_x = max(0, min(self.visible_width - self.scroll_bar_width, self.scroll_bar_x))
                self.scroll_x = int(self.scroll_bar_x * self.max_scroll_x / max(1, self.visible_width - self.scroll_bar_width))

    def calculate_scroll(self):
        self.total_lines = len(self.render_cache)
        self.visible_height = self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH - self.PADDING
        self.max_scroll_y = max(0, self.total_lines * self.LINE_HEIGHT - self.visible_height)

        self.max_line_width = max((text.get_width() for text in self.render_cache), default=0)
        self.visible_width = self.WIDTH - self.SCROLLBAR_WIDTH - self.PADDING
        self.max_scroll_x = max(0, self.max_line_width - self.visible_width)

        self.scroll_bar_height = max(20, self.visible_height**2 // (self.LINE_HEIGHT * self.total_lines + 1))
        self.scroll_bar_y = int(self.scroll_y * (self.visible_height - self.scroll_bar_height) / max(1, self.max_scroll_y))

        self.scroll_bar_width = max(20, self.visible_width**2 // (self.max_line_width + 1))
        self.scroll_bar_x = int(self.scroll_x * (self.visible_width - self.scroll_bar_width) / max(1, self.max_scroll_x))

    def render(self):
        if not self.visible:
            return self.screen

        self.calculate_scroll()

        self.screen.fill((0, 0, 0))
        if self.bg != None:
            self.screen.blit(self.bg, (0,0))
            

        y_offset = self.PADDING - (self.scroll_y % self.LINE_HEIGHT)
        start_index = self.scroll_y // self.LINE_HEIGHT
        for i in range(start_index, len(self.render_cache)):
            line_surface = self.render_cache[i]
            draw_y = y_offset + (i - start_index) * self.LINE_HEIGHT
            if draw_y > self.visible_height + self.PADDING:
                break
            self.screen.blit(line_surface, (self.PADDING - self.scroll_x, draw_y))

        input_rect = p.Rect(0, self.HEIGHT - self.INPUT_HEIGHT, self.WIDTH, self.INPUT_HEIGHT)
        p.draw.rect(self.screen, (30, 30, 30), input_rect)
        input_surface = self.FONT.render(self.input_text, True, p.Color("green"))
        self.screen.blit(input_surface, (self.PADDING, self.HEIGHT - self.INPUT_HEIGHT + 5))

        p.draw.rect(self.screen, (80, 80, 80), (self.WIDTH - self.SCROLLBAR_WIDTH, self.PADDING + self.scroll_bar_y, self.SCROLLBAR_WIDTH, self.scroll_bar_height))
        p.draw.rect(self.screen, (80, 80, 80), (self.PADDING + self.scroll_bar_x, self.HEIGHT - self.INPUT_HEIGHT - self.SCROLLBAR_WIDTH, self.scroll_bar_width, self.SCROLLBAR_WIDTH))

        return self.screen

    def render_highlighted_line(self, text):
        lower_text = text.lower()
        line_color = None
        for keyword, color in self.line_highlight_keywords:
            if keyword.lower() in lower_text:
                line_color = color
                break

        parts = []
        i = 0
        while i < len(text):
            matched = False
            for word, color in self.highlight_keywords:
                if lower_text[i:].startswith(word.lower()):
                    parts.append((text[i:i+len(word)], color))
                    i += len(word)
                    matched = True
                    break
            if not matched:
                parts.append((text[i], line_color or p.Color("white")))
                i += 1

        surfaces = [self.FONT.render(part, True, color) for part, color in parts]
        full_surface = p.Surface((sum(s.get_width() for s in surfaces), self.LINE_HEIGHT), p.SRCALPHA)
        x_offset = 0
        for surf in surfaces:
            full_surface.blit(surf, (x_offset, 0))
            x_offset += surf.get_width()
        return full_surface

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def is_visible(self):
        return self.visible
    
    def is_alive(self):
        return self.thread.is_alive()

    def terminate(self):
        self.process.terminate()
        self.visible = False



class ImageAnimation:
    '''
    图片缓动效果
    
    '''
    def __init__(self, image_name, screen, start_pos, end_pos, duration):
        self.image = images.get(image_name)
        self.img_rect = self.image.get_rect()

        # 起始点和终点（你可以自定义）
        self.screen = screen
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = duration  # 动画持续时间（秒,浮点数）



    def start(self):
        self.start_time = t.time()
        self.finished = False

    def stop(self):
        self.finished = True

    def ease_in_out(self, t):    
        # 缓动函数：smoothstep（3t^2 - 2t^3）
        return 3 * t**2 - 2 * t**3

    # 缓动运动函数，返回当前位置
    def get_position(self, elapsed):
        if elapsed >= self.duration:
            return self.end_pos
        t = elapsed / self.duration
        eased_t = self.ease_in_out(t)
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * eased_t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * eased_t
        return (x, y)
    
    def update(self):
        try:
            self.start_time
        except AttributeError:
            return
        current_time = t.time()
        elapsed = current_time - self.start_time
        if elapsed < self.duration or self.finished == False:
            position = self.get_position(elapsed)
            self.img_rect.center = position
            self.screen.blit(self.image, self.img_rect)


    
class FlipChooseList:
    '''
    可翻页选择界面, 输入page_content(界面内容)与tag(不同实例之间的标签,用于区分不同类以及在buildwin函数外操作)
    '''
    def __init__(self, page_content = [['none']], tag = 'none', main_coordinate = (250,230), main_area = (400,200), main_size = (500,35), main_x_spacing = 0, main_y_spacing = 5, flip_coordinate = (350,520), flip_size = (100,50), flip_x_spacing = 100):
        self.page_num = len(page_content)
        self.page_content = page_content
        self.displaying_num = 1
        self.tag = tag

        self.main_coordinate = main_coordinate
        self.main_area = main_area
        self.main_size = main_size
        self.main_x_spacing = main_x_spacing
        self.main_y_spacing = main_y_spacing
        self.flip_coordinate = flip_coordinate
        self.flip_size = flip_size
        self.flip_x_spacing = flip_x_spacing

        self.displaying()

    def displaying(self): #更新界面的显示
        choose_list_pro(['上一页','下一页'], 'b_bg_3', self.flip_coordinate, self.main_area, self.flip_size, self.flip_x_spacing, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 20, text_color = (255,255,255), text_offset = (0,0), image_offset = (0,0), tag=self.tag+'Flip_list')
        choose_list_pro(self.page_content[self.displaying_num - 1], 'b_bg_3', self.main_coordinate, self.main_area, self.main_size, self.main_x_spacing, self.main_y_spacing, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 20, text_color = (255,255,255), text_offset = (0,0), image_offset = (0,0), tag=self.tag+'Choose_List')

    def flip_page(self, num): #向指定位置翻页,num为一个偏移量,要求界面偏移num页后允许达到,并且为正值或负值
        if self.displaying_num + num > self.page_num:
            self.displaying()
        elif self.displaying_num + num == 0:
            self.displaying()
        else:
            self.displaying_num = self.displaying_num + num
            self.displaying()

    def get_page_element(self, num): #返回正在显示的界面的指定元素
        return (self.page_content[self.displaying_num - 1][num])
    
    def get_element_counter(self): #返回正在显示的界面的元素数量
        return (len(self.page_content[self.displaying_num - 1]))



class Button:
    def __init__(self, rect, callbacks):
        self.rect = rect
        self.callbacks = callbacks

    def check_click(self, mouse_pos):
        x, y, w, h = self.rect
        if x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h:
            for i in self.callbacks:
                i()
                #back = confirm(text='已执行:'+str(i),title="button",buttons=['继续'])



def Display_Version():  # 绘制版本号
    text(f"{version}   By {maker} / FPS: {clock.get_fps():.2f}",(10,585),(255,255,255),10)



def window(name, xy, scale = False, server_img = False):    #渲染一个图像,分为普通模式与服务器标识图模式

    if server_img == False:
        if scale == False:
            try:
                bylp.blit(images.get(name+'(original)'), xy)
            except:
                bylp.blit(images.get(name), xy)
        else:
            bylp.blit(images.get(name, scale), xy)
    else:
        if scale == False:
            try:
                bylp.blit(server_images.get(name+'(original)'), xy)
            except:
                bylp.blit(server_images.get(name), xy)
        else:
            bylp.blit(server_images.get(name, scale), xy)



def cv2_imread(path,mode):  # 读取选择的服务器标识图
    img = cv2.imdecode(np.fromfile(path,dtype=np.uint8),mode)
    return img



def cut_window(path,show_server):   # 对选择的服务器标识图进行处理
    global server_images
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

    cv2.imwrite('.ServerData/'+show_server+'/'+show_server+'_server_icon.png', end_img)

    server_images = ImageManager(".ServerData")



def text(texts, xy, color, size = 15, ttf = 'HarmonyOS_Sans_SC_Bold'):  # 渲染文字
#   'str' , (x,y) , (R,G,B, A【可选】) , int , 'str'
#   text:文字，xy:文字绘制坐标，color:文字颜色，size:文字大小(字号)，ttf:使用的字体文件名
#   渲染一行文字并绘制
    font = fonts.get(ttf, size)
    font_render = font.render(texts, True, color)

    if len(color) == 4:
        font_render.set_alpha(color[3])

    bylp.blit(font_render, xy)



def auto_center_text(texts, xy, rexy, color, size = 15, ttf = 'HarmonyOS_Sans_SC_Bold'):    #   渲染一个自动居中的文字
    font = fonts.get(ttf, size)
    font_render = font.render(texts, True, color)
    text_width, text_height = font_render.get_size()
    bylp.blit(font_render,[int(xy[0])+(int(rexy[0])-text_width)/2,int(xy[1])+(int(rexy[1])-text_height)/2])



def button(png,xy,button_size,text,color,size,ttf):  # 便捷创建一个有底图有文字的按钮，文字自动居中
#   当png值为'none'时无底图
#   png:图像路径，xy:按钮绘制坐标，button_size:按钮大小，text:文字，color:文字颜色，size:文字大小(字号)，ttf:使用的字体文件路径
    if png != 'none':
        window(png,xy,button_size)
    if text != '':
        auto_center_text(text,xy,button_size,color,size,ttf)



def add_show_window(add_obj):   # 在buildwin()以外修改显示的图像列表
#   当有正在显示的项目相同时，将自动避免列表中的项目重复
    global show_window
    for obj in add_obj:
        try:
            show_window.remove(obj)
        except:
            a=0
        show_window.append(obj)
    


def reload_add_show_window(add_obj):    # 在buildwin()函数以外修改显示的图像列表，同时会刷新显示列表
#   等效为仅显示buildwin()基础图像与add_obj中的图像
    global win
    buildwin(win)
    show_window.extend(add_obj)



def findtag_remove_show_window(find,tag):   # 移除带有指定tag的图像
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
        


def t_area_append():    # 为将要渲染的按钮添加判定(如有动画则同时添加动画判定)
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



def show_server_all_data(win):  # 在创建服务器时显示已经选择的服务器数据
    global server_type
    server_name = f.read_json_get_value('data/set/created_server_data.json', 'server_name') # 服务器名称
    core = f.read_json_get_value('data/set/created_server_data.json', 'core') # 核心种类
    mc_version = f.read_json_get_value('data/set/created_server_data.json', 'mc_version') # MC版本
    if core == 'Fabric': # 核心版本
        core_version = 'L: ' +f.read_json_get_value('data/set/created_server_data.json', 'core_version')[0] + ' I: ' + f.read_json_get_value('data/set/created_server_data.json', 'core_version')[1]
    else:
        core_version = f.read_json_get_value('data/set/created_server_data.json', 'core_version')[0]
    run_memory = f.read_json_get_value('data/set/created_server_data.json', 'run_memory') # 运行内存
    
    server_name = server_name + ' | ' + run_memory + ' G'
    # a | e G | server_type | b | c | d

    findtag_remove_show_window('text',"Server_name")
    findtag_remove_show_window('text',"Server_type")
    findtag_remove_show_window('text',"Server_core")
    findtag_remove_show_window('text',"Server_version")
    findtag_remove_show_window('text',"Server_core_version")
    findtag_remove_show_window('text',"other")

    font = fonts.get('HarmonyOS_Sans_SC_Bold', 20)
    l_font = fonts.get('HarmonyOS_Sans_SC_Bold', 25)

    text_list = [server_name, server_type, core, mc_version, core_version, ' | ']
    font_render_list = []
    if win == 11:
        color_list = [(255,255,255),(239,10,106),(255,255,255),(255,255,255),(255,255,255),(255,255,255)]
        size_list = [20,25,20,20,20,20]
    elif win == 12:
        color_list = [(255,255,255),(255,255,255),(239,10,106),(255,255,255),(255,255,255),(255,255,255)]
        size_list = [20,20,25,20,20,20]
    elif win == 13:
        color_list = [(255,255,255),(255,255,255),(255,255,255),(239,10,106),(255,255,255),(255,255,255)]
        size_list = [20,20,20,25,20,20]
    elif win == 14:
        color_list = [(255,255,255),(255,255,255),(255,255,255),(255,255,255),(239,10,106),(255,255,255)]
        size_list = [20,20,20,20,25,20]
    elif win == 15:
        color_list = [(239,10,106),(255,255,255),(255,255,255),(255,255,255),(255,255,255),(255,255,255)]
        size_list = [25,20,20,20,20,20]

    num = 0
    for i in size_list:
        if i == 25:
            font_render_list.append(l_font.render(text_list[num], True, color_list[num]))
        else:
            font_render_list.append(font.render(text_list[num], True, color_list[num]))
        num = num + 1

    width_list, height_list = [], []
    for i in font_render_list:
        text_width, text_height = i.get_size()
        width_list.append(text_width)
        height_list.append(text_height)

    x = 0
    for i in width_list:
        if i == width_list[5]:
            x = x + i * 4
        else:
            x = x + i
    
    x_coordinate =  (1000 - x) // 2
    y_baseline = 200

    add_show_window([['text',server_name,(x_coordinate,y_baseline - height_list[0] // 2),color_list[0],size_list[0],'HarmonyOS_Sans_SC_Bold',["Server_name"]]
                    ,['text',' | ',(x_coordinate + width_list[0],y_baseline - height_list[5] // 2),color_list[5],size_list[5],'HarmonyOS_Sans_SC_Bold',["other"]]
                    ,['text',server_type,(x_coordinate + width_list[5] + width_list[0],y_baseline - height_list[1] // 2),color_list[1],size_list[1],'HarmonyOS_Sans_SC_Bold',["Server_type"]]
                    ,['text',' | ',(x_coordinate + width_list[5] + width_list[0] + width_list[1],y_baseline - height_list[5] // 2),color_list[5],size_list[5],'HarmonyOS_Sans_SC_Bold',["other"]]
                    ,['text',core,(x_coordinate + width_list[5] * 2 + width_list[0] + width_list[1],y_baseline - height_list[2] // 2),color_list[2],size_list[2],'HarmonyOS_Sans_SC_Bold',["Server_core"]]
                    ,['text',' | ',(x_coordinate + width_list[5] * 2 + width_list[0] + width_list[1] + width_list[2],y_baseline - height_list[5] // 2),color_list[5],size_list[5],'HarmonyOS_Sans_SC_Bold',["other"]]
                    ,['text',mc_version,(x_coordinate + width_list[5] * 3 + width_list[0] + width_list[1] + width_list[2],y_baseline - height_list[3] // 2),color_list[3],size_list[3],'HarmonyOS_Sans_SC_Bold',["Server_version"]]
                    ,['text',' | ',(x_coordinate + width_list[5] * 3 + width_list[0] + width_list[1] + width_list[2] + width_list[3],y_baseline - height_list[5] // 2),color_list[5],size_list[5],'HarmonyOS_Sans_SC_Bold',["other"]]
                    ,['text',core_version,(x_coordinate + width_list[5] * 4 + width_list[0] + width_list[1] + width_list[2] + width_list[3],y_baseline - height_list[4] // 2),color_list[4],size_list[4],'HarmonyOS_Sans_SC_Bold',["Server_core_version"]]])



def tip(file_path,xy,interval):  # 渲染提示框内的文字
    global show_window
    tips = f.readtxt(str(file_path))
    a=int(len(tips))
    b=random.randint(0,a-1)
    c=str(tips[b])
    e=str.split(c,'&')
    rey=xy[1]
    findtag_remove_show_window('text','TIP')
    #print(show_window)
    for i in e:
        if rey == xy[1]:
            show_window.append(['text','Tip:  '+i,(xy[0],rey),(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['TIP']])
        else:
            show_window.append(['text',i,(xy[0],rey),(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['TIP']])
        rey=rey+interval
    #print(show_window)



def choose_list_pro(text_list, background_image_list, coordinate, area, size, x_spacing, y_spacing, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 50, text_color = (255,255,255), text_offset = (0,0), image_offset = (0,0), tag = 'none'):
    '''
    文字列表(为布尔值False时启用非按钮模式,非按钮模式必须有背景图像列表,list),
    背景图像列表(为字符串时视为应用于全部,list), 
    绘制坐标(tuple), 
    总绘制范围(tuple), 
    每块大小(tuple / list[仅不带tag且非按钮模式]), 
    x方向间隔(int), 
    y方向间隔(int), 
    文字字体(str), 
    文字大小(默认20字号,int), 
    文字颜色(默认255,255,255,tuple) 
    居中文字偏移量(可为负值,默认0,0,仅在普通模式下可用,tuple)
    背景图像偏移量(可为负值,默认0,0,仅在非按钮模式模式下可用!!!,支持为列表,tuple / list)
    添加的tag名称(默认'none'不添加tag,注意!tag不能为'self',会和按钮冲突,str)
    [文字样式全部统一,不支持单独指定]

    '''
    a = 0

    x = coordinate[0]
    y = coordinate[1]

    if tag != 'none' and tag != 'self': #带tag
        
        
        if text_list == False:  #非按钮模式
            findtag_remove_show_window('window',tag)
            for i in background_image_list:
                add_show_window([['window', i, (x + image_offset[0], y + image_offset[1]), size, [tag]]])

                a = a + 1
                x = x + size[0] + x_spacing
                if x > coordinate[0] + area[0]: #超出指定绘制范围则换行
                    x = coordinate[0]
                    y = y + size[1] + y_spacing

        else:   #普通模式
            findtag_remove_show_window('button',tag)
            findtag_remove_show_window('auto_center_text',tag)
            for i in text_list:
                if type(background_image_list) == str:  #如果background_image_list为字符串时视为应用于全部
                    add_show_window([['button', background_image_list, (x,y), size, '', (255,255,255), 15, 'HarmonyOS_Sans_SC_Bold', ['self'], [tag]]])
                else:
                    add_show_window([['button', background_image_list[a], (x,y), size, '', (255,255,255), 15, 'HarmonyOS_Sans_SC_Bold', ['self'], [tag]]])

                add_show_window([['auto_center_text', i, (x + text_offset[0], y + text_offset[1]), size, text_color, text_size, ttf, [tag]]])

                a = a + 1
                x = x + size[0] + x_spacing
                if x > coordinate[0] + area[0]: #超出指定绘制范围则换行
                    x = coordinate[0]
                    y = y + size[1] + y_spacing
                

    else: #不带tag

        if text_list == False:
            for i in background_image_list:
                if type(size) == tuple:
                    real_size = size
                    if type(image_offset) == tuple:
                        add_show_window([['window', i, (x + image_offset[0], y + image_offset[1]), real_size]])
                    else:
                        add_show_window([['window', i, (x + image_offset[a][0], y + image_offset[a][1]), real_size]])
                else:
                    real_size = size[a]
                    if type(image_offset) == tuple:
                        add_show_window([['window', i, (x + image_offset[0], y + image_offset[1]), real_size]])
                    else:
                        add_show_window([['window', i, (x + image_offset[a][0], y + image_offset[a][1]), real_size]])
                a = a + 1
                x = x + real_size[0] + x_spacing
                if x > coordinate[0] + area[0]:
                    x = coordinate[0]
                    y = y + real_size[1] + y_spacing
        else:
            for i in text_list:
                if type(background_image_list) == str:
                    add_show_window([['button', background_image_list, (x,y), size, '', (255,255,255), 15, 'HarmonyOS_Sans_SC_Bold', ['self']]])
                else:
                    add_show_window([['button', background_image_list[a], (x,y), size, '', (255,255,255), 15, 'HarmonyOS_Sans_SC_Bold', ['self']]])

                add_show_window([['auto_center_text', i, (x + text_offset[0], y + text_offset[1]), size, text_color, text_size, ttf]])
                a = a + 1
                x = x + size[0] + x_spacing
                if x > coordinate[0] + area[0]:
                    x = coordinate[0]
                    y = y + size[1] + y_spacing



def loading(blocknum, blocksize, totalsize):    # 渲染下载进度
    global daling

    easing_speed = 0.05
    current_progress = 0.0 # 正在显示的进度
    target_progress = 0.0 # 下载进度
    progress_image = images.get("lg",(770,20)) # 进度条图片

    target_progress = 100.0 * blocknum * blocksize / totalsize

    if target_progress>100.0:
        target_progress=100.0

    if daling == 114514:
        DALSTOPERROR
        #这个报错是用来终止下载的awa

    if int(7.7*target_progress) != 0.0:
        # 平滑进度更新
        current_progress += (target_progress - current_progress) * easing_speed

        # 限制进度范围
        current_progress = max(0.0, min(100.0, current_progress))

        # 根据当前进度裁剪图片区域
        progress_width = int(7.7 * 20 * current_progress)
        if progress_width > 0:
        # 从图像裁剪相应部分并绘制
            progress_rect = p.Rect(0, 0, progress_width, 20)

            findtag_remove_show_window('window_load',"LOAD")
            findtag_remove_show_window('auto_center_text',"LOAD")

            add_show_window([['window_load',progress_image, (114,222), progress_rect, ["LOAD"]]])
            add_show_window([['auto_center_text',' %'+str(round(target_progress,2)),(111,219),(776,27),(255,255,255),15,'HarmonyOS_Sans_SC_Bold',["LOAD"]]])

            #print(current_progress)

        #print(str(show_window)+'\n\n\n')
        #t.sleep(2)
    


def Download():    # 下载服务器核心
    global daling
    daling = 1
    d = f.read_json_get_value('data/set/created_server_data.json', 'downloaded')
    if int(d) == 0:
        core = f.read_json_get_value('data/set/created_server_data.json', 'core')
        mc_verision = f.read_json_get_value('data/set/created_server_data.json', 'mc_version')
        core_version_ALL = f.read_json_get_value('data/set/created_server_data.json', 'core_version')

        download_link = f.readtxt_find('data/download_link.txt',core)

        if core == 'Spigot':
            http_s = download_link.replace("{mc_version}", mc_verision)
        elif core == 'Paper':
            core_version = core_version_ALL[0]
            paper_code = f.readtxt_find('data/ver_Paper_core.txt',mc_verision,2)[1]
            http_s = download_link.replace("{mc_version}", mc_verision).replace("{core_version}", core_version).replace("{paper_code}", paper_code)
        elif core == 'Fabric':
            core_version_L = core_version_ALL[0]
            core_version_I = core_version_ALL[1]
            http_s = download_link.replace("{mc_version}", mc_verision).replace("{core_version_L}", core_version_L).replace("{core_version_I}", core_version_I)
        elif core == 'Forge':
            core_version = core_version_ALL[0]
            http_s = download_link.replace("{mc_version}", mc_verision).replace("{core_version}", core_version)
        
        

        findtag_remove_show_window('window',"ERROR")
        findtag_remove_show_window('auto_center_text',"ERROR")

        if len(http_s) > 90:
            add_show_window([['auto_center_text',http_s[:88]+'...',(200,258),(600,24),(255,255,255),15,'HarmonyOS_Sans_SC_Bold',["ERROR"]]])
        else:
            add_show_window([['auto_center_text',http_s,(200,258),(600,24),(255,255,255),15,'HarmonyOS_Sans_SC_Bold',["ERROR"]]])

        op=urllib.request.build_opener()
        op.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36')]
        urllib.request.install_opener(op)
        server_name = f.read_json_get_value('data/set/created_server_data.json', 'server_name')

        try:
            if core != 'Fabric':
                urllib.request.urlretrieve(http_s,'serverdown/'+server_name+'.jar',loading)
                findtag_remove_show_window('auto_center_text',"LOAD")
                add_show_window([['auto_center_text','下载完成!',(111,219),(776,27),(0,255,0),15,'HarmonyOS_Sans_SC_Bold',["ERROR"]]])
            else:
                add_show_window([['auto_center_text','Fabric核心下载时无法查看进度,请等待此处显示下载完成.',(111,219),(776,27),(255,255,255),15,'HarmonyOS_Sans_SC_Bold',["LOAD"]]])
                urllib.request.urlretrieve(http_s,'serverdown/'+server_name+'.jar')
                findtag_remove_show_window('auto_center_text',"LOAD")
                add_show_window([['auto_center_text','Fabric核心下载完成!',(111,219),(776,27),(0,255,0),15,'HarmonyOS_Sans_SC_Bold',["ERROR"]]])
        except:
            if daling != 114514:
                add_show_window([['auto_center_text','ERROR:500.下载时发生未知错误,可能是网络问题,链接问题或网站问题.请检查网络并重试.',(111,219),(776,27),(255,0,0),15,'HarmonyOS_Sans_SC_Bold',["ERROR"]]])
            f.read_json_writing_value('data/set/created_server_data.json', 'downloaded', "0")
            daling = 0
            return None

        f.read_json_writing_value('data/set/created_server_data.json', 'downloaded', "1")
        daling = 0



def start_exe():    # 调用start.exe运行服务器
    os.system(r"start powershell.exe cmd /k 'start.exe'")



def start_First():
    f.writing('start_Num.txt',['ANSI占位用句','0'],1)
    start_exe()



def start_F():
    core = f.read_json_get_value('data/set/created_server_data.json', 'core')
    run_memory = f.read_json_get_value('data/set/created_server_data.json', 'run_memory')
    server_name = f.read_json_get_value('data/set/created_server_data.json', 'server_name')

    if core != 'Forge':
        f.writing("serverdown/begin.bat",'java -Xms' + run_memory + 'G -Xmx' + run_memory + 'G -jar ' + server_name + '.jar --nogui',0)
    else:
        f.writing("serverdown/install.bat",'java -jar ' + server_name + '.jar --installServer',0)

    thr_stF=thr.Thread(target=start_First,daemon=1)
    thr_stF.start()



def show_eula():    # 展示服务器eula文件
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
            add_show_window([['text',str(i),(x,y),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']])
            y=y+30
    except:
        back = confirm(text="WAR:001.未找到eula.txt.\n应该是因为服务器第一次未运行完毕.\n等待片刻重试.",title='[WAR] | '+version,buttons=['继续'])



def get_server_properties_path() -> str:   # 计算正在配置的服务器配置文件的路径
    #global stserver
    server = f.read_Server()
    server_len = len(server)
    if server_len != 0:
        setting_server = str(server[stserver])
        setting_fpath = '.ServerFile/'+setting_server+'/server.properties'
    else:
        setting_fpath = 'none'
    return setting_fpath
        


def set_server_properties(win: int, what: int, test_what: str, texts: str = 'None') -> None:    # 设置服务器配置文件
    pro_path = get_server_properties_path()
    if pro_path != 'none':
        pro_data = svset.server_properties_data(pro_path,[test_what]).get(test_what)

        if what == 0:
            back = prompt(text=str(texts),title=version,default=str(pro_data))
            if back == None:
                back2 = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
            else:
                svset.writing_server(pro_path,str(test_what),str(back))
                buildwin(win)

        elif what == 1:
            if pro_data == 'true':
                svset.writing_server(pro_path,str(test_what),'false')
            elif pro_data == 'false':
                svset.writing_server(pro_path,str(test_what),'true')
            buildwin(win) 



def play_window():
    # window: [ ['window','str',(x,y), (rex,rey)]
    # text: [ ['text','str',(x,y),(R,G,B),int_size,'str_ttf', [ '此项所带的Tag' ](可选) ] ]
    # button: [ ['button,'str_png',(x,y),(bx,by),'str_text',(R,G,B),int_size,'str_ttf',['self / png_path' ](可选) ] ]
    global show_window
    global ani_window
    global tarea

    bylp.fill((27,27,27))

    main_bg.update()

    a = 0
    for i in show_window:

        if i[0] == 'window':
            window(i[1],i[2],i[3])

        elif i[0] == 'window_S':
            window(i[1],i[2],i[3],server_img = True)

        elif i[0] == 'window_load':
            bylp.blit(i[1], i[2], i[3])

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

    

def buildwin(win):  # 构建界面(描述每个界面的内容)
#   Int 
#   绘制目标界面序号应显示的图像
    global tarea
    global tarea_ani
    global stserver
    global show_window
    global ani_window
    global Server
    global Server_len
    global java_version
    global use_cmd
    global fps
    global variable_button_list
    tarea = []
    tarea_ani = []
    show_window = []
    ani_window = []
    variable_button_list = []
    a = 0

    if win == 0: #主界面  #此处显示经过优化，现在变得有点像MC里的tellraw/titleraw指令?
        show_window.extend([#['window','bg_theend',(0,0),False]
                       ['window','title_winter',(0,0),False]
                       ,['window','serverlist',(0,0),False]
                       ,['window','button_text',(0,0),False]
                       ,['button','none',(88,176),(229,48),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]
                       ,['button','none',(88,252),(229,48),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]
                       ,['button','none',(88,328),(229,48),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]
                       ,['button','none',(88,404),(229,48),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]])

        Server = f.read_Server()
        Server_len = len(Server)

        show_window.extend([['text',java_version,(630,88),(255,255,255),40,'HarmonyOS_Sans_SC_Bold']])

        if Server_len < 10:
            show_window.extend([['text','0'+str(Server_len),(870,98),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
        else:
            show_window.extend([['text',str(Server_len),(870,98),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])

        if show_server < 9 and Server_len != 0:
            show_window.extend([['text','0'+str(show_server+1),(770,68),(150,249,145),55,'HarmonyOS_Sans_SC_Bold']])
        elif show_server < 9 and Server_len == 0:
            show_window.extend([['text','00',(770,68),(150,249,145),55,'HarmonyOS_Sans_SC_Bold']])
        else:
            show_window.extend([['text',str(show_server+1),(770,68),(150,249,145),55,'HarmonyOS_Sans_SC_Bold']])

        if Server_len != 0 and Server_len <=99:
            show_server_data = str(f.read_json_get_value('.ServerData/'+str(Server[show_server])+'/created_server_data.json', 'core')
                                   +' / '+f.read_json_get_value('.ServerData/'+str(Server[show_server])+'/created_server_data.json', 'mc_version')
                                   +' / '+f.read_json_get_value('.ServerData/'+str(Server[show_server])+'/created_server_data.json', 'core_version')[0]
                                   +' ('+f.read_json_get_value('.ServerData/'+str(Server[show_server])+'/created_server_data.json', 'run_memory')
                                   +'G)')
            server_icon = os.path.exists('.ServerData/'+str(Server[show_server])+'/'+str(Server[show_server])+'_server_icon')
            if server_icon == True:
                show_window.extend([['window_S',str(Server[show_server])+'_server_icon',(315,158),False]])
            else:
                cut_window('data/imgs/Background/server_pt.png',str(Server[show_server]))
                show_window.extend([['window_S',str(Server[show_server])+'_server_icon',(315,158),False]])
            show_window.extend([['window','server_name',(535,170),False]
                                ,['window','serverchange',(0,0),False]
                                ,['text',str(Server[show_server]),(540,168),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']
                                ,['text',show_server_data,(540,218),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']
                                ,['text','服务器列表',(358,165),(255,255,255,100),15,'HarmonyOS_Sans_SC_Bold']
                                ,['button','b_title',(570,500),(150,40),'启动',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['self']]
                                ,['button','b_title',(740,500),(150,40),'移除',(255,0,0),25,'HarmonyOS_Sans_SC_Bold',['self']]
                                ,['button','none',(315,531),(90,24),'上一个',(0,0,0),15,'HarmonyOS_Sans_SC_Bold',['serverchange_bg']]
                                ,['button','none',(405,531),(90,24),'下一个',(0,0,0),15,'HarmonyOS_Sans_SC_Bold',['serverchange_bg']]
                                ,['button','b_re_name',(890,170),(35,32),'',(0,0,0),15,'HarmonyOS_Sans_SC_Bold',['b_re_name']]
                                ,['button','b_re_icon',(886,213),(35,32),'',(0,0,0),15,'HarmonyOS_Sans_SC_Bold',['b_re_icon']]
                                ,['button','none',(0,570),(1000,30),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']])
        elif Server_len == 0:
            show_window.extend([['text','暂未创建服务器...',(500,330),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
        elif Server_len > 99:
            show_window.extend([['text','创建服务器过多...',(500,330),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
    

    elif win == 2: #世界配置
        show_window.extend([#['window','bg_theend_2',(0,0),False]
                            ['window','set_world',(0,0),False]
                            ,['button','none',(58,46),(200,44),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                            ,['button','b_title_next',(615,53),(32,32),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','none',(58,113),(200,44),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                       ,['button','none',(495,153),(462,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(495,208),(457,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(495,263),(452,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(495,318),(447,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']])

        Server = f.read_Server()
        Server_len = len(Server)

        if Server_len == 0:
            show_window.extend([['text','暂未创建服务器...',(460,102),(249,238,145),20,'HarmonyOS_Sans_SC_Bold']])
        else:
            setting_server = str(Server[stserver])
            setting_file_path = '.ServerFile/'+setting_server+'/server.properties'
            show_window.extend([['text',setting_server,(460,102),(150,249,145),20,'HarmonyOS_Sans_SC_Bold']])

            #可输入选项
            setting_obj = ['level-seed','level-name','gamemode','difficulty']
            setting_objxyz = [[515,153],[515,208],[515,263],[515,318]]
            a = 0
            sp_data = svset.server_properties_data(setting_file_path,setting_obj)

            for i in setting_obj:
                text_1 = sp_data.get(i)
                #print(text_1)
                if type(text_1) == str and len(text_1) >= 32:
                    show_window.extend([['text',str(text_1[:32])+'...',(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']])
                elif type(text_1) == str and len(text_1) < 32:
                    show_window.extend([['text',text_1,(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']])
                else:
                    pass
                a += 1

            #仅有'T','F'的选项
            setting_obj = ['force-gamemode','allow-nether','enable-command-block','pvp','spawn-npcs','spawn-animals','spawn-monsters','generate-structures']
            setting_objxyz = [[575,390],[575,435],[575,480],[575,525],[845,390],[845,435],[845,480],[845,525]]
            a = 0
            sp_data = svset.server_properties_data(setting_file_path,setting_obj)

            for i in setting_obj:
                text_1 = sp_data.get(i)
                # 如果值不为None,则渲染按钮，否则pass
                # 注意，这里设置了两种按钮变量，普通的show_window按钮仅用于绘制按键反馈，实际起执行作用的是variable_button_list中的数量可变按钮
                if text_1 != None:
                    variable_button_list.extend([Button((setting_objxyz[a][0],setting_objxyz[a][1],75,35), [lambda i=i: set_server_properties(2,1,i)])])
                    show_window.extend([['button','b_'+text_1,(setting_objxyz[a][0],setting_objxyz[a][1]),(75,35),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg']]])
                else:
                    pass
                a += 1

            if Server_len < 10:
                show_window.extend([['text','0'+str(Server_len),(170,523),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
            else:
                show_window.extend([['text',str(Server_len),(170,523),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
            if show_server < 9:
                show_window.extend([['text','0'+str(stserver+1),(100,513),(150,249,145),35,'HarmonyOS_Sans_SC_Bold']])
            else:
                show_window.extend([['text',str(stserver+1),(100,513),(150,249,145),35,'HarmonyOS_Sans_SC_Bold']])
        

    elif win == 21:#服务器配置
        show_window.extend([#['window','bg_theend_2',(0,0),False],
                            ['window','set_server',(0,0),False]
                            ,['button','none',(58,46),(200,44),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                            ,['button','b_title_back',(615,53),(32,32),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','none',(58,113),(200,44),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                       ,['button','none',(529,153),(428,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(529,208),(422,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(529,263),(417,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(495,318),(447,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['button','none',(664,373),(273,38),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']])
        
        Server = f.read_Server()
        Server_len = len(Server)

        if Server_len == 0:
            show_window.extend([['text','暂未创建服务器...',(460,102),(249,238,145),20,'HarmonyOS_Sans_SC_Bold']])
        else:
            setting_server = str(Server[stserver])
            setting_file_path = '.ServerFile/'+setting_server+'/server.properties'
            show_window.extend([['text',setting_server,(460,102),(150,249,145),20,'HarmonyOS_Sans_SC_Bold']])

            #可输入选项
            setting_obj = ['motd','server-port','max-players','simulation-distance','player-idle-timeout']
            setting_objxyz = [[515,153],[515,208],[515,263],[515,318],[655,373]]
            a = 0
            sp_data = svset.server_properties_data(setting_file_path,setting_obj)

            for i in setting_obj:
                text_1 = sp_data.get(i)
                if type(text_1) == str and len(text_1) >= 32:
                    show_window.extend([['text',str(text_1[:32])+'...',(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']])
                elif type(text_1) == str and len(text_1) < 32:
                    show_window.extend([['text',text_1,(setting_objxyz[a][0],setting_objxyz[a][1]+8),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']])
                else:
                    pass
                a += 1

            #仅有'T','F'的选项
            setting_obj=['online-mode','white-list','prevent-proxy-connections','allow-flight']
            setting_objxyz=[[536,435],[536,480],[656,525],[846,435]]
            a = 0
            sp_data = svset.server_properties_data(setting_file_path,setting_obj)

            for i in setting_obj:
                text_1 = sp_data.get(i)
                if text_1 != None:
                    variable_button_list.extend([Button((setting_objxyz[a][0],setting_objxyz[a][1],75,35), [lambda i=i: set_server_properties(21,1,i)])])
                    show_window.extend([['button','b_'+text_1,(setting_objxyz[a][0],setting_objxyz[a][1]),(75,35),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg']]])
                else:
                    pass
                a += 1

            if Server_len < 10:
                show_window.extend([['text','0'+str(Server_len),(170,523),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
            else:
                show_window.extend([['text',str(Server_len),(170,523),(255,255,255),35,'HarmonyOS_Sans_SC_Bold']])
            if show_server < 9:
                show_window.extend([['text','0'+str(stserver+1),(100,513),(150,249,145),35,'HarmonyOS_Sans_SC_Bold']])
            else:
                show_window.extend([['text',str(stserver+1),(100,513),(150,249,145),35,'HarmonyOS_Sans_SC_Bold']])

 
    elif win == 31: #程序设置_程序设置
        cmd_use_font = f.read_json_get_value('data/set_pgm/program_settings.json','cmd_font')
        if len(cmd_use_font) > 26: cmd_use_font = cmd_use_font[:23] + '...'
        cmd_bg_png = f.read_json_get_value('data/set_pgm/program_settings.json','cmd_bg_image')
        if len(cmd_bg_png) > 26: cmd_bg_png = cmd_bg_png[:23] + '...'

        show_window.extend([['window','pgm_setting_1',(0,0),False]
                            ,['button','b_back_to_main',(32,35),(178,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                            ,['button','none',(300,90),(35,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','none',(665,90),(35,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','b_bg_3',(285,176),(150,30),'开始',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(285,218),(150,30),'重置',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(285,260),(150,30),'依据系统环境变量',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(285,365),(300,30),cmd_use_font,(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(310,418),(300,30),cmd_bg_png,(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(285,460),(150,30),'默认',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(665,460),(150,30),'默认',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(310,500),(150,30),'False',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(665,500),(150,30),'True',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]])
        
        if use_cmd == True:
            show_window.extend([['button','b_false',(285,311),(75,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]])
        else:
            show_window.extend([['button','b_true',(285,311),(75,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]])


    elif win == 32: #程序设置_画面设置
        custom_bg_png = f.read_json_get_value('data/set_pgm/program_settings.json','custom_bg')
        if len(custom_bg_png) > 26: custom_bg_png = custom_bg_png[:23] + '...'

        show_window.extend([['window','pgm_setting_2',(0,0),False]
                            ,['button','b_back_to_main',(32,35),(178,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                            ,['button','none',(300,90),(35,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','none',(665,90),(35,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','b_bg_3',(285,176),(150,30),str(fps),(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(285,260),(300,30),custom_bg_png,(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_bg_3',(285,300),(150,30),'默认',(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['self']]])
        
        if main_bg.start == True:
            show_window.extend([['button','b_true',(285,215),(75,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]])
        else:
            show_window.extend([['button','b_false',(285,215),(75,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]])
        

    elif win == 33: #程序设置_其他设置
        show_window.extend([['window','pgm_setting_3',(0,0),False]
                            ,['button','b_back_to_main',(32,35),(178,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                            ,['button','none',(300,90),(35,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','none',(665,90),(35,35),'',(255,255,255),25,'HarmonyOS_Sans_SC_Bold',['b_bg']]])
        

    elif win == 4: #关于作者
        show_window.extend([['window','about_authors',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','none',(684,168),(225,52),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg']]
                            ,['button','none',(684,358),(225,52),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg']]])


    elif win == 11: #创建服务器_服务器类型
        show_window.extend([['window','create_server_1',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_next',(820,538),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]])

        choose_list_pro(['插件服','模组服'], 'b_bg_3', (250,250), (600,200), (200,200), 100, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 30, text_color = (255,255,255), text_offset = (0,40), image_offset = (0,0))
        choose_list_pro(False, ['plugin','mod'], (310,280), (600,200), (80,80), 220, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 30, text_color = (255,255,255), text_offset = (0,20), image_offset = (0,0))

        show_server_all_data(win)


    elif win == 12: #创建服务器_核心类型
        show_window.extend([['window','create_server_2',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_next',(820,538),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                        ])
        
        if server_type == '插件服':
            choose_list_pro(['Spigot','Paper'], 'b_bg_3', (250,250), (600,200), (200,200), 100, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 30, text_color = (255,255,255), text_offset = (0,40), image_offset = (0,0))
            choose_list_pro(False, ['spigot_logo','papermc_logo'], (310,280), (600,200), (80,80), 220, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 30, text_color = (255,255,255), text_offset = (0,20), image_offset = (0,0))
        elif server_type == '模组服':
            choose_list_pro(['Fabric','Forge'], 'b_bg_3', (250,250), (600,200), (200,200), 100, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 30, text_color = (255,255,255), text_offset = (0,40), image_offset = (0,0))
            choose_list_pro(False, ['fabric_logo','forge_logo'], (310,280), (600,200), [(80,80),(120,120)], 220, 0, ttf = 'HarmonyOS_Sans_SC_Bold', text_size = 30, text_color = (255,255,255), text_offset = (0,20), image_offset = [(0,0),(-20,-20)])

        show_server_all_data(win)


    elif win == 13: #创建服务器_MC版本
        show_window.extend([['window','create_server_3',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_next',(820,538),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                       ])
        
        core = f.read_json_get_value('data/set/created_server_data.json', 'core')
        mc_version = f.readtxt('data/ver_'+ core +'.txt')
        re_mc_version = f.list_pagination(mc_version, 7)
        choose_mc_ver = FlipChooseList(re_mc_version, 'mc_version')

        show_server_all_data(win)
        

    elif win == 14: #创建服务器_核心版本
        show_window.extend([['window','create_server_4',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_next',(820,538),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                       ])
        core = f.read_json_get_value('data/set/created_server_data.json', 'core')
        

        if core == 'Spigot':
            show_window.extend([['auto_center_text', 'Spigot核心无需选择核心版本', (0,0), (1000,600), (255,255,255), 30, 'HarmonyOS_Sans_SC_Bold']])

        elif core == 'Paper' or core == 'Forge':
            mc_version = f.read_json_get_value('data/set/created_server_data.json', 'mc_version')
            core_version = [f.readtxt_find('data/ver_'+ core +'_core.txt', mc_version)]
            re_core_version = f.list_pagination(core_version, 7)
            choose_core_ver = FlipChooseList(re_core_version, 'core_version')

        elif core == 'Fabric':
            core_version_L = f.readtxt('data/ver_Fabric_Loader.txt')
            re_core_version_L = f.list_pagination(core_version_L, 3)
            core_version_I = f.readtxt('data/ver_Fabric_Installer.txt')
            re_core_version_I = f.list_pagination(core_version_I, 3)

            choose_core_ver_L = FlipChooseList(re_core_version_L, 'core_version_L',main_coordinate=(250,230),flip_coordinate=(350,350),flip_size=(100,30))
            choose_core_ver_I = FlipChooseList(re_core_version_I, 'core_version_I',main_coordinate=(250,400),flip_coordinate=(350,520),flip_size=(100,30))
            


        show_server_all_data(win)


    elif win == 15: #创建服务器_最后设置
        run_memory = int(f.read_json_get_value('data/set/created_server_data.json', 'run_memory'))
        server_name = f.read_json_get_value('data/set/created_server_data.json', 'server_name')
        show_window.extend([['window','create_server_5',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_next',(820,538),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['auto_center_text', '在下方输入为服务器分配的运行内存(必须整数)', (0,245), (1000,30), (255,255,255), 30, 'HarmonyOS_Sans_SC_Bold']
                            ,['auto_center_text', '*为创建的服务器命名', (0,370), (1000,30), (255,255,255), 30, 'HarmonyOS_Sans_SC_Bold']
                       ])
        if run_memory < 2:
            rgb = [232,121,46]
        elif 2 <= run_memory < 8:
            rgb = [116,232,46]
        elif 8 <= run_memory < 12:
            rgb = [46,199,232]
        elif 12 <= run_memory < 16:
            rgb = [232,216,46]
        elif 16 <= run_memory < 32:
            rgb = [46,90,232]
        elif 32 <= run_memory < 64:
            rgb = [232,46,46]
        else:
            rgb = [230,46,232]
        show_window.extend([['button','b_bg_3',(350,295),(300,50), str(run_memory)+' GB', rgb ,25,'HarmonyOS_Sans_SC_Bold',['self']]])

        show_window.extend([['button','b_bg_3',(350,420),(300,50), server_name, (255,255,255),25,'HarmonyOS_Sans_SC_Bold',['self']]])

        show_server_all_data(win)


    elif win == 16:  #创建服务器_下载核心
        show_window.extend([['window','op_server_2',(0,0),False]
                            ,['button','b_back',(20,20),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                            ,['button','b_next',(820,538),(150,40),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['self']]
                       ,['button','none',(301,295),(150,45),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                       ,['button','none',(550,295),(150,45),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_title']]
                       ,['button','none',(45,370),(910,130),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']
                       ,['text','Tip:  点击此处框框范围内,可以随机切换Tip语句哦!',(60,390),(255,255,255),20,'HarmonyOS_Sans_SC_Bold',['TIP']]])
    

    elif win == 17: #创建服务器_展示eula
        first_start = int(f.read_json_get_value('data/set/created_server_data.json', 'first_start'))
        if first_start == 0:
            show_window.extend([['window','eula_1',(0,0),False]
                                ,['button','Loading',(0,0),(1000,600),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']])
        elif first_start == 1:
            show_window.extend([['window','eula_1',(0,0),False]
                        ,['button','none',(291,474),(200,45),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]
                        ,['button','none',(46,474),(200,45),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]
                        ,['button','none',(537,474),(200,45),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold',['b_bg_2']]])
        

    elif win == 18: #创建服务器_完成创建
        a = f.read_json_get_value('data/set/created_server_data.json', 'server_name')
        b = f.read_json_get_value('data/set/created_server_data.json', 'core')
        c = f.read_json_get_value('data/set/created_server_data.json', 'core_version')
        d = f.read_json_get_value('data/set/created_server_data.json', 'run_memory')
        e = f.read_json_get_value('data/set/created_server_data.json', 'mc_version')
        if b in ['Spigot','Paper']:
            b = '插件服 | ' + b
        elif b in ['Fabric','Forge']:
            b = '模组服 | ' + b
        if len(c) == 2:
            c = e + ' | ' + c[0] + ' ' + c[1]
        else:
            c = e + ' | ' + c[0]
        d = d + ' G'
        show_window.extend([#['window','bg_theend_2',(0,0),False]
                            ['window','finish',(0,0),False]
                            ,['auto_center_text',a,(101,245),(800,30),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']
                            ,['auto_center_text',b,(101,307),(800,30),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']
                            ,['auto_center_text',c,(101,369),(800,30),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']
                            ,['auto_center_text',d,(101,430),(800,30),(255,255,255),20,'HarmonyOS_Sans_SC_Bold']
                            ,['button','none',(400,490),(200,42),'',(255,255,255),28,'HarmonyOS_Sans_SC_Bold',['b_bg']]])


    elif win == 50: #服务器控制台界面
        show_window.extend([['button','none',(0,570),(1000,30),'',(255,255,255),15,'HarmonyOS_Sans_SC_Bold']])


    t_area_append()

    if win == 13: #在需要创建类的页面返回类的实例
        return choose_mc_ver
    elif win == 14 and core not in ['Fabric','Spigot']:
        return choose_core_ver
    elif win == 14 and core == 'Fabric':
        return choose_core_ver_L, choose_core_ver_I



#  ==================================
#          BUILDING WINDOWS
#  ==================================



version = f.read_json_get_value('Version.json','name') + ' ' + f.read_json_get_value('Version.json','version')
maker = 'TA_JLPawa'

p.init()

win = 0
daling = 0
stserver = 0
custom = 'False'
server_type = '插件服'
refresh = True
tarea = []
tarea_ani = []
variable_button_list: List[Button] = []
show_window = []
ani_window = []
tip_window = []
show_server = 0
Server = f.read_Server()
Server_len = len(Server)
java_version = str(f.get_java_version())
server_running = False

fps = int(f.read_json_get_value('data/set_pgm/program_settings.json','fps'))
use_cmd = bool(int(f.read_json_get_value('data/set_pgm/program_settings.json','use_system_cmd')))

# win: 主界面界面序号
# daling: 是否正在下载核心
# stserver: 正在配置的服务器序号
# custom: 是否为自定义服务器
# server_type: 已选择的服务器类型
# refresh: 是否启用主循环(不启用则程序结束运行)
# tarea: Test Area,为鼠标行动xy坐标检测列表
# tarea_ani: Trst Area Animation,为需要播放按键动画的动画数据
# variable_button_list: 数量不确定的按钮列表(仅能支持简单功能)
# show_window: 正在显示的图像
# ani_window: 正在播放的动画
# tip_window: 界面中可以显示的提示列表
# show_server: 正在显示的服务器
# Server_len: 已开设的服务器数量
# java_version: 使用的Java版本
# server_running:是否有服务器在运行

# /*** 下列为可更改的程序设置 ***/

# fps: 界面刷新帧率
# use_cmd: 是否使用windows系统cmd，如果为否，则使用程序内嵌控制台

bylp = p.display.set_mode((1000,600))            #1000,600

p.display.set_caption('Py Minecraft Server 开服器','By TA_JLPawa')
icon = p.image.load('data/imgs/icon.png').convert()
p.display.set_icon(icon)
p.event.set_allowed([p.QUIT, p.MOUSEBUTTONUP, p.MOUSEMOTION])

p.key.stop_text_input()
p.key.set_repeat(500, 50)

buildwin(win)

try:
    try_read_serverlist = f.readtxt('.ServerList/ServerList.txt')
except:
    shutil.copytree('ServerList(backup_copy)','.ServerList')



if __name__ == "__main__":

    scales = {
    	"b_title": [(150,40),(200,44),(195,50),(135,40),(140,41),(260,40),(150,45),(178,40)],
    	"b_re_name": [(35,32)],
    	"b_re_icon": [(35,32)],
        "b_bg": [(32,32),(35,35),(225,52),(64,32),(200,42),(75,35)],
	    "b_bg_2": [(229,48),(200,45)],
        "b_bg_3": [(200,200),(500,35),(100,50),(100,30),(300,50),(150,30),(300,30)],
	    "b_bg_title_main_2": [(48,48)],
	    "serverchange": [(90,24)],
	    "serverchange_bg": [(90,24)],
        "b_title_next": [(32,32)],
        "b_title_back": [(32,32)],
        "b_next": [(150,40)],
        "b_back": [(150,40)],
        "b_back_to_main": [(178,40)],
        "b_false": [(75,35)],
        "b_true": [(75,35)],
        "lod_s": [(16,12)],
        "Loading": [(1000,600)],
        "mod": [(80,80)],
        "plugin": [(80,80)],
        "spigot_logo": [(80,80)],
        "papermc_logo": [(80,80)],
        "fabric_logo": [(80,80)],
        "forge_logo": [(120,120)],
        "lg": [(770,20)]
    }

    alphas = {
        "none": 0
    }

    font_size = {
        "HarmonyOS_Sans_SC_Bold":[
            10, 15, 18, 20, 25, 28, 30, 35, 40, 45, 55
        ]
    }

    images = ImageManager("data/imgs",scale_map=scales, alpha_map=alphas)
    server_images = ImageManager(".ServerData")
    fonts = FontManager("data/fonts", size_map=font_size)
    try:
        main_bg = BackgroundFollower("data/imgs/background/Custom/"+f.read_json_get_value('data/set_pgm/program_settings.json','custom_bg'), bylp, (1000,600), 0.1, bool(int(f.read_json_get_value('data/set_pgm/program_settings.json','dynamic_bg'))))
    except:
        main_bg = BackgroundFollower("data/imgs/background/"+f.read_json_get_value('data/set_pgm/program_settings.json','custom_bg'), bylp, (1000,600), 0.1, bool(int(f.read_json_get_value('data/set_pgm/program_settings.json','dynamic_bg'))))
    console = None
    animation = 0
    



#  ==================================
#            BUTTON EVENT
#  ==================================



clock = p.time.Clock()


while refresh:

    clock.tick(fps)
    event = p.event.get()
    
    for e in event:



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
                            ani_window.append(['window','b_bg_title_main_2',(i[0]-57,i[1]),(48,48),[str(tarea_ani_num)]])
                
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
                        if server_running == True:
                            back = confirm(text=Server_Run+" 正在运行中！\n请先在服务器控制台输入'stop'关闭服务器.",title=version,buttons=['确定'])
                        else:
                            Server_Run = str(Server[show_server])
                            back = confirm(text="你是否确定启动服务器 "+Server_Run+" ?.",title=version,buttons=['暂不启动','确定'])
                            if back == '确定':
                                f.writing('start_Num.txt',['ANSI占位用句',Server_Run],1)

                                if use_cmd == True:
                                    thr_stexe=thr.Thread(target=start_exe,daemon=1)
                                    thr_stexe.start()
                                else:
                                    animation = ImageAnimation(
                                        image_name='running_list',
                                        screen= bylp,
                                        start_pos=(500, 615),
                                        end_pos=(500, 585),
                                        duration=1.0,
                                    )

                                    animation.start()

                                    console = PygameConsoleOverlay(command=["start.exe"], size=(1000, 570), 
                                                                   font_name=f.read_json_get_value('data/set_pgm/program_settings.json','cmd_font'), 
                                                                   font_size=15, 
                                                                   bg=f.read_json_get_value('data/set_pgm/program_settings.json','cmd_bg_image'))
                                    server_running = True

                    elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                        if server_running == False:
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
                        else:
                            back = confirm(text="无法移除，因为服务器正在运行中",title=version,buttons=['确定'])

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
                                f.read_json_writing_value('.ServerData/'+Server_Run+'/created_server_data.json', 'server_name', str(back))
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
                        choose_path = f.choose_png('选择一个格式为png的图片,建议图片尺寸为215x397 (1:1.85).')
                        if choose_path != 'None':
                            cut_window(choose_path,Server_Run)
                            buildwin(win)

                    elif mx in range(int(tarea[10][0]),int(tarea[10][2])) and my in range(int(tarea[10][1]),int(tarea[10][3])) and server_running == True and use_cmd != True:
                        console.show()
                        win = 50
                        buildwin(win)
                        continue

                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
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
                            buildwin(win)

                    elif testset == 1: #已检验
                        try:
                            Server = f.readtxt('.ServerList/ServerList.txt')
                        except:
                            Server = ['ANSI占位用句']
                        if len(Server) <= 99:
                            win=11
                            server_type = '插件服'
                            svset.reset_data()
                            buildwin(win)
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
                            buildwin(win)
                            
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win = 2
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    win = 31
                    buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    win = 4
                    buildwin(win)


            elif win == 2 and Server_len != 0: #世界配置界面(有服务器)
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
                    set_server_properties(2,0,'level-seed','请输入世界种子\n请注意,更换种子后须重创建世界才能生效')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    set_server_properties(2,0,'level-name','请输入世界名称\n将作为世界名称及其文件夹名')
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    set_server_properties(2,0,'gamemode','请输入默认游戏模式\n可输入\n[survival-生存,creative-创造,adventure-冒险,spectator-旁观]')
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    set_server_properties(2,0,'difficulty','请输入目标难度\n可输入\n[peaceful-和平,easy-简单,normal-普通,hard-困难]')
                else:
                    for btn in variable_button_list: # 数量可变按钮检测
                        btn.check_click((mx,my))



            elif win == 2 and Server_len == 0: #世界配置界面(无服务器)
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



            elif win == 21 and Server_len != 0: #服务器配置界面(有服务器)   待添加
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
                    set_server_properties(21,0,'motd','请输入要展示的服务器信息(为Unicode码)\n可输入的字符数 [0-59]')
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    set_server_properties(21,0,'server-port','请输入服务器(监听的)端口号\n可输入的范围 [1-65534]')
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    set_server_properties(21,0,'max-players','请输入服务器支持的最大玩家数量')
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    set_server_properties(21,0,'simulation-distance','请输入玩家各个方向上可视的区块数量(以玩家为中心的半径)\n可输入的范围 [3-32]')
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])):
                    set_server_properties(21,0,'player-idle-timeout','请输入玩家被允许的最长挂机时间(单位:分钟)\n设置为0表示关闭此功能')
                else:
                    for btn in variable_button_list: # 数量可变按钮检测
                        btn.check_click((mx,my))



            elif win == 21 and Server_len == 0: # 服务器配置界面(无服务器)
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



            elif win == 31: #程序设置界面
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    pass
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    win = 32
                    buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    back = confirm(text='确定开始运行一次可行性检验吗?',title=version,buttons=['开始','返回'])
                    if back == '开始':
                        f.testofset(version)
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    f.read_json_writing_value('data/set_pgm/program_settings.json','java_test','0')
                    back = confirm(text="可行性检验数据文件已重置.",title=version,buttons=['明白'])
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])): # 调整默认java路径
                    pass
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])): # 更改控制台字体
                    choose_path = f.choose_ttf()
                    if choose_path != 'None':
                        file_operation.copy_ttf(choose_path)
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'cmd_font', choose_path.split('/')[-1])
                        buildwin(win)
                elif mx in range(int(tarea[7][0]),int(tarea[7][2])) and my in range(int(tarea[7][1]),int(tarea[7][3])): # 更改控制台背景图像
                    choose_path = f.choose_png('选择一个格式为png的图片,建议图片尺寸为1000x600 (10:6).')
                    if choose_path != 'None':
                        file_operation.copy_cmd_png(choose_path)
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'cmd_bg_image', choose_path.split('/')[-1])
                        images = ImageManager("data/imgs",scale_map=scales, alpha_map=alphas)
                    else:
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'cmd_bg_image', '无')
                    buildwin(win)
                elif mx in range(int(tarea[8][0]),int(tarea[8][2])) and my in range(int(tarea[8][1]),int(tarea[8][3])):
                    pass
                elif mx in range(int(tarea[9][0]),int(tarea[9][2])) and my in range(int(tarea[9][1]),int(tarea[9][3])):
                    pass
                elif mx in range(int(tarea[10][0]),int(tarea[10][2])) and my in range(int(tarea[10][1]),int(tarea[10][3])):
                    pass
                elif mx in range(int(tarea[11][0]),int(tarea[11][2])) and my in range(int(tarea[11][1]),int(tarea[11][3])):
                    pass
                elif mx in range(int(tarea[12][0]),int(tarea[12][2])) and my in range(int(tarea[12][1]),int(tarea[12][3])):# 内嵌控制台是否启用
                    if server_running == False:
                        if use_cmd == True:
                            use_cmd = False
                            f.read_json_writing_value('data/set_pgm/program_settings.json', 'use_system_cmd', '0')
                        else:
                            use_cmd = True
                            f.read_json_writing_value('data/set_pgm/program_settings.json', 'use_system_cmd', '1')
                        buildwin(win)
                    else:
                        back = confirm(text="此设置只能在服务器关闭后修改 !",title=version,buttons=['明白'])



            elif win == 32: #程序设置界面
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win = 0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win = 31
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    win = 33
                    buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])): # 更改界面刷新帧率
                    if fps == 30:
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'fps', '60')
                        fps = 60
                    elif fps == 60:
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'fps', '30')
                        fps = 30
                    buildwin(win)
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):# 更改主界面背景图像
                    choose_path = f.choose_png('选择一个格式为png的图片,建议图片尺寸为1100x700 (11:7).')
                    if choose_path != 'None':
                        file_operation.copy_cmd_png(choose_path)
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'custom_bg', choose_path.split('/')[-1])
                    else:
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'custom_bg', 'bg_theend_re.png')
                    try:
                        main_bg = BackgroundFollower("data/imgs/background/Custom/"+f.read_json_get_value('data/set_pgm/program_settings.json','custom_bg'), bylp, (1000,600), 0.1, bool(int(f.read_json_get_value('data/set_pgm/program_settings.json','dynamic_bg'))))
                    except:
                        main_bg = BackgroundFollower("data/imgs/background/"+f.read_json_get_value('data/set_pgm/program_settings.json','custom_bg'), bylp, (1000,600), 0.1, bool(int(f.read_json_get_value('data/set_pgm/program_settings.json','dynamic_bg'))))
                    buildwin(win)
                elif mx in range(int(tarea[5][0]),int(tarea[5][2])) and my in range(int(tarea[5][1]),int(tarea[5][3])):
                    pass
                elif mx in range(int(tarea[6][0]),int(tarea[6][2])) and my in range(int(tarea[6][1]),int(tarea[6][3])):
                    if main_bg.start == True:
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'dynamic_bg', '0')
                        main_bg.start = False
                    else:
                        f.read_json_writing_value('data/set_pgm/program_settings.json', 'dynamic_bg', '1')
                        main_bg.start = True
                    buildwin(win)



            elif win == 33: #程序设置界面
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win = 32
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    pass



            elif win == 4: #关于作者界面
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    abmk.visit('TA_JLPawa')
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    abmk.visit('Github')



            elif win == 11: #创建服务器_服务器类型
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    custom = 'False'
                    #shutil.rmtree('serverdown')
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
                    server_type = '插件服'
                    show_server_all_data(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    server_type = '模组服'
                    show_server_all_data(win)



            elif win == 12: #创建服务器_核心类型
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win = 11
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win = 13

                    choose_mc_ver = buildwin(win)  #返回选择框类的实例

                else:
                    if server_type == '插件服':
                        if mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                            f.set_core('Spigot')
                            f.read_json_writing_value('data/set/created_server_data.json', 'core_version', ['none'])
                        elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                            f.set_core('Paper')
                            f.read_json_writing_value('data/set/created_server_data.json', 'core_version', f.read_json_get_value('data.set(backup_copy)/created_server_data.json', 'core_version'))
                    elif server_type == '模组服':
                        if mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                            f.set_core('Fabric')
                            f.read_json_writing_value('data/set/created_server_data.json', 'core_version', [f.readtxt('data/ver_Fabric_Loader.txt')[0], f.readtxt('data/ver_Fabric_Installer.txt')[0]])
                        elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                            f.set_core('Forge')
                            f.read_json_writing_value('data/set/created_server_data.json', 'core_version', ['43.5.0'])
                    show_server_all_data(win)
                    


            elif win == 13: #创建服务器_MC版本
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    del choose_mc_ver
                    win = 12
                    buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    del choose_mc_ver
                    win = 14
                    choose_core = f.read_json_get_value('data/set/created_server_data.json', 'core')
                    if choose_core == 'Fabric':
                        choose_core_ver_L, choose_core_ver_I = buildwin(win)
                    else:
                        choose_core_ver = buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    choose_mc_ver.flip_page(num = -1)
                    tarea = []
                    tarea_ani = []
                    t_area_append()
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    choose_mc_ver.flip_page(num = 1)
                    tarea = []
                    tarea_ani = []
                    t_area_append()

                else:
                    a = 0
                    for i in tarea[4:]:
                        if mx in range(int(i[0]),int(i[2])) and my in range(int(i[1]),int(i[3])):
                            f.read_json_writing_value('data/set/created_server_data.json', 'mc_version', str(choose_mc_ver.get_page_element(a)))
                            show_server_all_data(win)
                        a = a + 1
                    del a



            elif win == 14: #创建服务器_核心版本
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    if choose_core == 'Fabric':
                        del choose_core_ver_L, choose_core_ver_I
                    else:
                        del choose_core_ver
                    del choose_core
                    win = 13
                    choose_mc_ver = buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    if choose_core == 'Fabric':
                        del choose_core_ver_L, choose_core_ver_I
                    else:
                        del choose_core_ver
                    win = 15
                    buildwin(win)
                else:
                    if choose_core  == 'Spigot':
                        pass
                    elif choose_core  == 'Fabric':
                        if mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                            choose_core_ver_L.flip_page(num = -1)
                            choose_core_ver_I.flip_page(num = 0)
                            tarea = []
                            tarea_ani = []
                            t_area_append()
                        elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                            choose_core_ver_L.flip_page(num = 1)
                            choose_core_ver_I.flip_page(num = 0)
                            tarea = []
                            tarea_ani = []
                            t_area_append()
                        elif mx in range(int(tarea[4+choose_core_ver_L.get_element_counter()][0]),int(tarea[4+choose_core_ver_L.get_element_counter()][2])) and my in range(int(tarea[4+choose_core_ver_L.get_element_counter()][1]),int(tarea[4+choose_core_ver_L.get_element_counter()][3])):
                            choose_core_ver_L.flip_page(num = 0)
                            choose_core_ver_I.flip_page(num = -1)
                            tarea = []
                            tarea_ani = []
                            t_area_append()
                        elif mx in range(int(tarea[5+choose_core_ver_L.get_element_counter()][0]),int(tarea[5+choose_core_ver_L.get_element_counter()][2])) and my in range(int(tarea[5+choose_core_ver_L.get_element_counter()][1]),int(tarea[5+choose_core_ver_L.get_element_counter()][3])):
                            choose_core_ver_L.flip_page(num = 0)
                            choose_core_ver_I.flip_page(num = 1)
                            tarea = []
                            tarea_ani = []
                            t_area_append()
                        else:
                            a = 0
                            for i in tarea[4:4+choose_core_ver_L.get_element_counter()]:
                                if mx in range(int(i[0]),int(i[2])) and my in range(int(i[1]),int(i[3])):
                                    f.read_json_writing_value('data/set/created_server_data.json', 'core_version', [str(choose_core_ver_L.get_page_element(a)), f.read_json_get_value('data/set/created_server_data.json', 'core_version')[1]])
                                    show_server_all_data(win)
                                a = a + 1
                            
                            a = 0
                            for i in tarea[6+choose_core_ver_L.get_element_counter():]:
                                if mx in range(int(i[0]),int(i[2])) and my in range(int(i[1]),int(i[3])):
                                    f.read_json_writing_value('data/set/created_server_data.json', 'core_version', [f.read_json_get_value('data/set/created_server_data.json', 'core_version')[0], str(choose_core_ver_I.get_page_element(a))])
                                    show_server_all_data(win)
                                a = a + 1
                            del a
                    elif choose_core  == 'Paper' or 'Forge':
                        if mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                            choose_core_ver.flip_page(num = -1)
                            tarea = []
                            tarea_ani = []
                            t_area_append()
                        elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                            choose_core_ver.flip_page(num = 1)
                            tarea = []
                            tarea_ani = []
                            t_area_append()

                        else:
                            a = 0
                            for i in tarea[4:]:
                                if mx in range(int(i[0]),int(i[2])) and my in range(int(i[1]),int(i[3])):
                                    f.read_json_writing_value('data/set/created_server_data.json', 'core_version', [str(choose_core_ver.get_page_element(a))])
                                    show_server_all_data(win)
                                a = a + 1
                            del a



            elif win == 15: #创建服务器_最后设置
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win = 14
                    if choose_core == 'Fabric':
                        choose_core_ver_L, choose_core_ver_I = buildwin(win)
                    else:
                        choose_core_ver = buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    win = 16
                    buildwin(win)
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    f.set_run_memory(114514,version)
                    buildwin(win)
                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    if custom == 'False':
                        sername = f.read_json_get_value('data/set/created_server_data.json', 'server_name')
                        sernamed = f.readtxt('.ServerList/ServerList.txt')
                        back = prompt(text='输入你想设置的服务器名称.(建议为全英文)',title=version,default=sername)
                        if back ==  None:
                            back = confirm(text="你关闭了界面,此次输入将不做保存.",title=version,buttons=['继续'])
                        elif len(back) == 0 or len(back) > 12:
                            back = confirm(text="你输入的名字太短/太长了!."+'\n'+'请确保输入的名字大于0个字符并且小于等于12个字符!',title=version,buttons=['继续'])
                        else:
                            if back not in sernamed:
                                f.read_json_writing_value('data/set/created_server_data.json', 'server_name', str(back))
                                back = confirm(text="已保存目标服务器名称为: "+str(back)+'.',title=version,buttons=['继续'])
                                show_server_all_data(win)
                            else:
                                back = confirm(text="目标服务器名称已存在,请重新命名! ",title=version,buttons=['继续'])
                    buildwin(win)



            elif win == 16: #创建服务器_下载核心
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    if daling == 0 and int(f.read_json_get_value('data/set/created_server_data.json', 'downloaded')) == 0:
                        win=15
                        buildwin(win)
                    elif daling == 0 and int(f.read_json_get_value('data/set/created_server_data.json', 'downloaded')) == 1:
                        back = confirm(text="【提示】 在核心下载完毕后返回上一个界面,需要重新下载核心",title=version,buttons=['返回','取消'])
                        if back == '返回':
                            win=15
                            buildwin(win)
                            f.read_json_writing_value('data/set/created_server_data.json', 'downloaded',"0")
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    if daling == 0 and int(f.read_json_get_value('data/set/created_server_data.json', 'downloaded')) == 1:
                        del choose_core
                        win=17
                        buildwin(win)
                        start_F()
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    print(int(f.read_json_get_value('data/set/created_server_data.json', 'downloaded')))
                    if daling == 0 and int(f.read_json_get_value('data/set/created_server_data.json', 'downloaded')) == 0:
                        if f.read_json_get_value('data/set/created_server_data.json', 'core') == 'Forge':
                            back = confirm(text="【提示】 由于部分地区网络问题,运行Forge installer时有概率会报\njava.net.SocketTimeoutException: Read timed out.\n错误,该问题是由于网络无法连接至forge的服务器jar链接导致的,与程序无关\n如果无法正常下载,请手动运行如下文件:\n程序文件夹/serverdown/install.bat",title=version,buttons=['继续下载','先不下载'])
                            if back == '先不下载':
                                pass
                            else:
                                thr_Download=thr.Thread(target=Download,daemon=1)
                                thr_Download.start()
                        else:
                            thr_Download=thr.Thread(target=Download,daemon=1)
                            thr_Download.start()

                elif mx in range(int(tarea[3][0]),int(tarea[3][2])) and my in range(int(tarea[3][1]),int(tarea[3][3])):
                    if daling == 1:
                        daling = 114514
                        findtag_remove_show_window('window',"LOAD")
                        findtag_remove_show_window('auto_center_text',"LOAD")
                        reload_add_show_window([['auto_center_text','PAUSE.',(111,219),(776,27),(255,0,0),15,'HarmonyOS_Sans_SC_Bold',["ERROR"]]])
                elif mx in range(int(tarea[4][0]),int(tarea[4][2])) and my in range(int(tarea[4][1]),int(tarea[4][3])):
                    tip('data/z_tip.txt',[60,390],25)



            elif win == 17: #创建服务器_展示eula
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    if int(f.read_json_get_value('data/set/created_server_data.json', 'first_start')) == 1:
                        buildwin(win)
                        show_eula()
                    else:
                        back = confirm(text="第一次运行服务器还未运行完毕!请等待运行结束后点击继续",title=version,buttons=['等待','强制继续'])
                        if back == '强制继续':
                            f.read_json_writing_value('data/set/created_server_data.json', 'first_start', '1')
                            buildwin(win)
                elif mx in range(int(tarea[1][0]),int(tarea[1][2])) and my in range(int(tarea[1][1]),int(tarea[1][3])):
                    try:
                        f.reset_eula()
                        win=18
                        buildwin(win)
                    except:
                        back = confirm(text="WAR:001.未找到eula.txt.\n应该是因为服务器第一次未运行完毕.\n等待片刻重试.",title='[WAR] | '+version,buttons=['继续'])
                elif mx in range(int(tarea[2][0]),int(tarea[2][2])) and my in range(int(tarea[2][1]),int(tarea[2][3])):
                    abmk.visit('Minecraft_eula')



            elif win == 18: #创建服务器_完成创建
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    win=0
                    custom = 'False'
                    svset.get_new_server()
                    buildwin(win)



            elif win == 50:  #服务器运行内嵌CMD界面
                if mx in range(int(tarea[0][0]),int(tarea[0][2])) and my in range(int(tarea[0][1]),int(tarea[0][3])):
                    console.hide()
                    win = 0
                    buildwin(win)



        if console != None and win == 50:
            console.handle_event(e)



    play_window()


    if console != None:
        if console.is_visible():
            if console.update_output():
                pass  # 新输出时可做额外处理
            bylp.blit(console.render(), (0, 0))

        if console.is_alive() == False:
                print("Unknown_CMD : 进程已关闭！")
                try:
                    back = confirm(text="服务器已关闭! \n点击按钮后程序会自动关闭cmd进程并跳转至主界面\n" + str(console.output_lines[-1]),title=version,buttons=['关闭进程'])
                except:
                    back = confirm(text="服务器已关闭! \n点击按钮后程序会自动关闭cmd进程并跳转至主界面\n" + '由于优化机制,未能获取日志',title=version,buttons=['关闭进程'])
                console.terminate()
                console = None
                server_running = False
                win = 0
                animation = ImageAnimation(
                                    image_name='running_list',
                                    screen= bylp,
                                    start_pos=(500, 585),
                                    end_pos=(500, 615),
                                    duration=1.0,
                                )

                animation.start()
                buildwin(win)

    if animation != 0:
        animation.update()

    if server_running == True and use_cmd == False:
        text(f"{Server_Run}  正在运行中...",(10,570),(0,255,0),15)



    Display_Version()



    p.display.update()