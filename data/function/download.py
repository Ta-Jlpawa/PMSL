
'''
下载服务器核心专用模块，在主程序中使用 import data.function.download 来导入.

'''



#  ==================================
#             IMPORT LIST
#  ==================================

import urllib
import urllib.request

#  ==================================
#            FUNCTION LIST
#  ==================================




'''
loading 函数 (urllib.request.urlretrieve回调函数)

返回一个下载进度(load)，可用于展示进度条
格式为 0.00 - 100.00 的浮点数
下载时通过 dal 函数中的 try: 语句自动调用
##############################################   此函数暂无输出，需要修改来添加输出

'''

def loading(finish,allof,fileof): #下载进度

    load=100.0*finish*allof/fileof
    if load>100.0:
        load=100.0



'''
dal 函数

输入为 download ,用于下载核心（无法连接网站时则可重复调用）
返回的 download 为正整数,1代表已成功下载,0代表下载失败

'''

def dal(download):
    download=1

    r=open("data/set/core.txt",'r')
    a=r.readlines()
    a=str(a[0])
    r.close

    r=open("data/set/version.txt",'r')
    c=r.readlines() 
    b,linem=[],0
    for aline in c:
        aline=aline.replace('\n','')
        b.append(aline)
        linem=linem+1
#b0:版本 b1:fabric加载器/forge_old小版本/paper小版本 b2:fabric安装器
    r.close

    if a=='forge':
        http='https://adfoc.us/serve/sitelinks/?id=271228&url=https://maven.minecraftforge.net/net/minecraftforge/forge/'+str(b[0])+'-'+str(b[1])+'/forge-'+str(b[0])+'-'+str(b[1])+'-installer.jar'
    if a=='spigot':
        http='https://download.getbukkit.org/spigot/spigot-'+str(b[0])+'.jar'
    if a=='fabric':
        http='https://meta.fabricmc.net/v2/versions/loader/'+str(b[0])+'/'+str(b[1])+'/'+str(b[2])+'/server/jar'
    if a=='paper':
        http='https://api.papermc.io/v2/projects/paper/versions/'+str(b[0])+'/builds/'+str(b[1])+'/downloads/paper-'+str(b[0])+'-'+str(b[1])+'.jar'
  
    print("本程序将于"+http+"(此为官网)处下载服务器核心"+"\n"+"由于是外网,下载较慢请耐心等待"+"\n"+"附:fabric核心下载时采用了不同的传输方法,因此下载fabric核心时进度可能显示错误,但无关紧要")
    print("下载进度: 00.00%  (如卡在此条大于15秒,则可能是链接繁忙,可尝试重启)")
    op=urllib.request.build_opener()
    op.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36')]
    urllib.request.install_opener(op)
    try:
        urllib.request.urlretrieve(http,'ServerFile/SERVER.jar',loading)
    except:
        print('ERROR,下载失败,请检查网络及版本是否正确,等待片刻重试')
        input('下载暂停,稍等片刻后按下回车键(Enter)以重新尝试下载')
        download=0

    print('下载'+str(b[0])+'版本核心完成')
    return download