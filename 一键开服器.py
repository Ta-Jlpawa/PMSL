import os
import time
def clo(file,writ,rig):
    if int(rig)==0:
        opfile=open(file,'w')
        opfile.close
    opfile=open(file,'a+')
    opfile.write(writ)
    opfile.close
def first(core,ver,fablod,fabins,papsmv,formv):
    if core=='spigot':
        clo("version.txt",ver+'\n'+core,0)
    if core=='fabric':
        clo("version.txt",ver+'\n'+core+'\n'+fablod+'\n'+fabins,0)
    if core=='paper':
        clo("version.txt",ver+'\n'+core+'\n'+papsmv,0)
    if core=='forge':
        clo("version.txt",ver+'\n'+core+'\n'+formv,0)
def reset():
    tryfl=open("step.txt",'r')
    linefl=tryfl.readlines()
    tryfl.close
    return linefl
def versay():
    allverfl=open("版本参考.txt",'r')
    linevr=allverfl.readlines()
    txtallvr,linem=[],0
    for aline in linevr:
        aline=aline.replace('\n','')
        txtallvr.append(aline)
        linem=linem+1
    allverfl.close
    return txtallvr
def prin(number,endnum):
    print('\n')
    while number<=endnum:
        print(txtallvr[number])
        number=number+1
    print('\n')
#begin
fablod,fabins,papsmv,txtallvr,beg,formv=0,0,0,[],'0',0
txtallvr=versay()
usermode=str(input("在此输入运行模式"+'\n'+"直接回车为简易模式,键入'hd'为详细模式"+'\n'+"直接通过此程序启动服务器须选择详细模式"+'\n'+"详情见附带教程'使用教程'一栏:"))
if usermode=='hd':
    try:
        tryrd=open("myserver/server.properties",'r')
        serverset=tryrd.readlines()
        tryrd.close
        print('检测到server.properties服务器设置文件,应视为服务器已开设')
        beg=str(input("在此键入'b'视为服务器未开设运行,'n'运行指定jar,否则(按回车键)直接运行已有默认核心:"))
        if beg=='b':
            NAMEERRORTOBREAK
    except:
        rest=str(input('未检测到server.properties服务器设置文件,应视为服务器未开设'+'\n'+"如果你的服务器还未开设,在此键入'r'来自动初始化,否则继续 :"))
        if rest=='r':
            clo('step.txt','0',0)
            clo('version.txt','0',0)
        else:
            print('你放弃了初始化'+'\n'+'你可以通过输入step数值来指定程序从第几步开始运行'+'\n'+"输入'-1'来跳过此步"+'\n'+"如选择跳过,程序将在上一次未完成的step处继续运行,这可能会导致未知的错误!")
            stepnum=int(input('在此输入step数值(可选:0,2,4,5):'))
            if stepnum!=-1:
                clo('step.txt',str(stepnum),0)
                time.sleep(3)
        beg=str(input("在此键入'n'运行指定jar,否则(按回车键)继续:"))
else:
    clo('step.txt','0',0)
    clo('version.txt','0',0)
linefl=reset()
if beg=='n':
    bit=str(int(input('请输入你准备设置的服务器运行内存(输入整数,单位:GB):')))
    svrname=str(int(input('请输入你准备的服务器核心名称(jar名):')))
    clo("myserver/begin.bat",'java -Xms'+bit+'G -Xmx'+bit+'G -jar '+svrname+'.jar --nogui',0)
    po=0
#    for portfor in serverset:
#        try:
#            port=portfor.index('server-port=')
#            print('你的服务器开设端口为:'+serverset[int(po)])
#            break
#        except:
#            po=po+1
#此项功能可能有bug,准备日后修复
    clo("step.txt",'5',0)
    os.system(r'辅助启动脚本.exe')
    linefl[0]=1
#0
if int(linefl[0])==0 and usermode=='hd':
    while 1:
        core=str(input("请输入你想要的服务器核心类型 (键入'p'来查询支持的核心) :"))
        if core=='p':
            prin(0,3+1)
        elif core in ['spigot','fabric','paper','forge']:
            break
        else:
            print('你输入的核心类型不受支持!你可以重新输入')
    while 1:
        ver=str(input("请输入你想要开设的服务器版本 [键入'p'来查询你选择的核心所支持的版本]:"))
        if ver=='p':
            if core=='spigot':
                prin(5+1,22+1)
            elif core=='fabric':
                prin(24+1,30+1)
            elif core=='paper':
                prin(45+1,59+1)
            elif core=='forge':
                prin(74,80)
        else:
            if core=='spigot':
                break
            elif core=='fabric':
                while 1:
                    fablod=str(input("Fabric Loader Version(加载器版本) [键入'p'来查询支持的版本]:"))
                    if fablod=='p':
                        prin(32+1,36+1)
                    else:
                        break
                while 1:
                    fabins=str(input("Installer Version(安装器版本) [键入'p'来查询支持的版本]:"))
                    if fabins=='p':
                        prin(38+1,43+1)
                    else:
                        break
                break
            elif core=='paper':
                while 1:
                    papsmv=str(input("paper核心具有小版本,请输入你想要的小版本号 [键入'p'来查询支持的版本]:"))
                    if papsmv=='p':
                        prin(61+1,71+1)
                    else:
                        break
                break
            elif core=='forge':
                while 1:
                    formv=str(input("forge核心具有小版本,请输入你想要的小版本号 [键入'p'来查询支持的版本]:"))
                    if formv=='p':
                        prin(82,84)
                    else:
                        break
                break
    bit=str(int(input('请输入你准备设置的服务器运行内存(输入整数,单位:GB):')))
    first(core,ver,fablod,fabins,papsmv,formv)
    clo("step.txt",'1',0)
    try:
        os.system(r'辅助启动脚本.exe')
    except:
        print('\n'+'[ERROR]Because:SeverCore-Download-ERROR')
        print('出现错误,本程序将于30秒后自动关闭')
        time.sleep(30)
elif int(linefl[0])==0 and usermode!='hd':
    bit='4'
    first('spigot','1.19.2',fablod,fabins,papsmv,formv)
    clo("step.txt",'1',0)
    try:
        os.system(r'辅助启动脚本.exe')
    except:
        print('\n'+'[ERROR]Because:SeverCore-Download-ERROR')
        print('出现错误,本程序将于30秒后自动关闭')
        time.sleep(30)
linefl=reset()
#2####ERROR
if int(linefl[0])==2:
    try:
        clo("myserver/begin.bat",'java -Xms'+str(bit)+'G -Xmx'+str(bit)+'G -jar SERVER.jar --nogui',0)    #!!
        clo("step.txt",'3',0)
    except:
        print('\n'+'[ERROR]Because:Bat-Build-ERROR')
        print('出现错误,本程序将于30秒后自动关闭')
        time.sleep(30)
    try:
        os.system(r'辅助启动脚本.exe')
    except:
        print('\n'+'[ERROR]Because:Java-Setting-ERROR')
        print('出现错误,本程序将于30秒后自动关闭')
        time.sleep(30)
linefl=reset()
#5
if int(linefl[0])==5:
    os.system(r'辅助启动脚本.exe')
linefl=reset()
#4
if int(linefl[0])==4:
    print('正在运行开服第四步-自动同意eula协议,为保证您知道其内容,此程序将向您展示'+'\n')
    try:
        cfile=open("myserver/eula.txt",'r')
    except:
        print('\n'+'[ERROR]Because:Eula-Reading-ERROR')
        print('出现错误,本程序将于30秒后自动关闭')
        time.sleep(30)
    line=cfile.readlines()
    print('\n')
    for mywifeissanbing in line:
        print(mywifeissanbing)
    print('\n')
    cfile.close
    time.sleep(3)
    input('展示完成,按下回车键(Enter)表示您同意eula服务器协议,程序将会自动修改:')
    m,lm=0,len(line)
    while 1:
        if m==(lm-1):
            clo("myserver/eula.txt",'eula=true',1)
            break
        elif m==0:
            clo("myserver/eula.txt",line[m],0)
        else:
            clo("myserver/eula.txt",line[m],1)
        m=m+1
    #fufile.flush
    #fufile.close
    clo("step.txt",'5',0)
print('服务器开设完毕,本程序将于10秒后自动关闭')
time.sleep(10)