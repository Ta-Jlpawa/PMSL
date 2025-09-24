# ◇  PMSL 
![Language](https://img.shields.io/badge/Python-3.9.11-blue)  ![Downloads](https://img.shields.io/github/downloads/Ta-Jlpawa/PMSL/total?label=Downloads)  ![Stars](https://img.shields.io/github/stars/Ta-Jlpawa/PMSL)  ![Watch](https://img.shields.io/github/watchers/Ta-Jlpawa/PMSL)

## Py Minecraft Server Launcher

PMSL 全称 Py Minecraft Server Launcher.  
是一个完全使用Python编写的Minecraft游戏服务器快捷创建/启动/配置程序.  
此程序完全免费，禁止私自商用.

## 系统支持

此程序支持 **Windows 10** 及以上的 **64** 位系统.

## 此程序的版本

目前此程序已更新至   **V 1.1.0** .

## 此程序的功能

- 在程序内快捷创建服务器
- 通过程序启动已有服务器
- 在程序内快捷修改服务器设置文件
- 个性化部分界面

## 未来的更新计划

- 进一步优化界面
- 支持使用更多种类的服务器核心
- 优化自定义核心功能
- 支持修改更多的服务器设置

## 开发者注意事项

主程序`PyMinecraftServerLanucher.py`通过执行名为`start.exe`的可执行文件来运行服务器，`start.exe`来源于存储库中的`start.py`，因此若想要正常运行主程序，需要将`start.py`打包为可执行文件并放在主程序目录下，或者自行将`PyMinecraftServerLanucher.py`中涉及`start.exe`的源码改为调用`start.py`.

**举例:**
```python

def start_exe():
    os.system(r"start powershell.exe cmd /k 'start.exe'")

```
**改为**
```python

def start_exe():
    os.system(r"start powershell.exe cmd /k 'start.py'")

```

## 关于作者

此程序目前参与制作的有:

**TA_JLPawa**  （Github:Ta-jlpawa）  
Bilibili: [点击这里前往我的B站主页~](https://space.bilibili.com/1101301178)

你可以通过网页链接联系作者.
