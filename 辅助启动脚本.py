import urllib
import urllib.request
import os
import sys
#import ostajlp
#if __name__=='__main__':
 #   app=QApplication(sys.argv)
  #  MainWindow=QMainWindow()
 #  ui=ostajlp.Ui_MainWindow()
  #  ui.setupUi(MainWindow)
   # MainWindow.show()
  #  sys.exit(app.exec_())
one=r'myserver'
tryfl=open("step.txt",'r')
linefl=tryfl.readlines()
tryfl.close
def clo(file,writ):
    opfile=open(file,'w')
    opfile.close
    opfile=open(file,'a+')
    opfile.write(writ)
    opfile.close
def loading(finish,allof,fileof):
  sys.stdout.write('\x1b[1A')
  sys.stdout.write('\x1b[2K')
  lod=100.0*finish*allof/fileof
  if lod>100.0:
    lod=100.0
  print("下载进度：%.2f%%" %(lod))
def opensvr():
  os.chdir(one)
  os.system('begin.bat')
def dal(a):
  if a==1:
    a=2
    print("本程序将于"+http+"(此为官网)处下载服务器核心"+"\n"+"由于是外网,下载较慢请耐心等待"+"\n"+"附:fabric核心下载时采用了不同的传输方法,因此下载fabric核心时进度可能显示错误,但无关紧要")
    print("下载进度: 00.00%  (如卡在此条大于15秒,则可能是链接繁忙,可尝试重启)")
    op=urllib.request.build_opener()
    op.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36')]
    urllib.request.install_opener(op)
    try:
      urllib.request.urlretrieve(http,'myserver/SERVER.jar',loading)
    except:
      print('ERROR,下载失败,请检查网络及版本是否正确,等待片刻重试'+'\n'+"有时官网会拒绝访问,这时需要手动前往浏览器下载核心并选择'运行指定jar'!")
      input('下载暂停,稍等片刻后按下回车键(Enter)以重新尝试下载')
      a=1
    return(a)
#1
if int(linefl[0])==1:
  verfl=open("version.txt",'r')
  linevr=verfl.readlines()
  txtvr,linem=[],0
  for aline in linevr:
      aline=aline.replace('\n','')
      txtvr.append(aline)
      linem=linem+1
  verfl.close
  a,op,vers,finish,allof,fileof=1,'0',str(txtvr[0]),0,0,0
  if str(txtvr[1])=='forge':
    http='https://maven.minecraftforge.net/net/minecraftforge/forge/'+vers+'-'+str(txtvr[2])+'/forge-'+vers+'-'+str(txtvr[2])+'-installer.jar'
  if str(txtvr[1])=='spigot':
    http='https://download.getbukkit.org/spigot/spigot-'+vers+'.jar'
  if str(txtvr[1])=='fabric':
    http='https://meta.fabricmc.net/v2/versions/loader/'+vers+'/'+str(txtvr[2])+'/'+str(txtvr[3])+'/server/jar'
  if str(txtvr[1])=='paper':
    http='https://api.papermc.io/v2/projects/paper/versions/'+vers+'/builds/'+str(txtvr[2])+'/downloads/paper-'+vers+'-'+str(txtvr[2])+'.jar'
  while a==1:
    a=dal(a)
  print('下载'+vers+'版本核心完成')
  clo("step.txt",'2')
#3
if int(linefl[0])==3:
  clo("step.txt",'4')
  opensvr()
#5
if int(linefl[0])==5:
  opensvr()