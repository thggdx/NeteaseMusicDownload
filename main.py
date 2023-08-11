import API
import threading
from os import getcwd,makedirs,path as ospath
from time import sleep
from getpass import getpass
from rich.progress import Progress

print("当前工作路径"+getcwd())
api=input("请输入API地址(可跳过):").rstrip('/')
api=api if api else "https://ncm-api.thggdx.eu.org"
progress=Progress()
task_id=None
lyricType=""
faile=[]

def task(songFile,semaphore):
    global faile
    try:
        songFile.download()
        if lyricType != "n":
            lyric=API.getLyric(songFile.id,api)
            if lyric and('lrc' in lyric): 
                lyric=lyric['lrc']['lyric']
                if lyricType=="1":
                    with open(ospath.splitext(songFile.filePath)[0]+'.lrc','w',encoding='utf-8') as f:
                        f.write(lyric)
                elif lyricType=="2":
                    songFile.songTag['lyric']=lyric
        songFile.setTag()
    except Exception as e:
        faile.append({"id":songFile.id,"Exception":e})
    finally:
        progress.update(task_id,advance=1)
        semaphore.release()

def main():
    global lyricType
    global progress
    global task_id
    global faile
    if API.apiCheck(api):
        if not API.cookieSave():
            while True:
                print("未登录，请选择登陆方式\n1:扫码登陆\n2:手机密码登陆\n3:手机验证码登陆")
                loginType=input("请输入登陆方式:")
                if loginType not in ["1","2","3"]:
                    print("输入错误")
                    continue
                break
            if loginType=="1":
                key=API.qrcodeKeyGet(api)
                API.qrcodeGet(key,api)
                stats=True
                while True:
                    sleep(1)
                    status=API.qrcodeCheck(key,api)
                    if(status['code']==801):
                        continue
                    elif(status['code']==802):
                        if stats:
                            print("User: "+status['name']+" 已扫码,请在手机上确认登录")
                            print(status['status'])
                            stats=False
                        continue
                    elif(status['code']==803):
                        print(status['status'])
                        break
            else:
                ctcode=input("请输入手机号国家代码(默认86):")
                ctcode=ctcode if ctcode else "86"
                phone=input("请输入手机号:")
                if loginType=="2":
                    password=getpass("请输入密码:")
                    data=API.passwordLogin(phone,password,ctcode,api)
                    print("name: "+str(data['name'])+"\nid: "+str(data['id']))
                if loginType=="3":
                    API.captchaSent(phone,ctcode,api)
                    print("验证码已发送至+"+ctcode+" "+phone)
                    for i in range(3):
                        captcha=input("请输入验证码:")
                        if API.captchaCheck(phone,captcha,ctcode,api):
                            data=API.captchaLogin(phone,captcha,ctcode,api)
                            print("name: "+str(data['name'])+"\nid: "+str(data['id']))
                            break
                        else:
                            if i==2:
                                raise Exception("验证码错误次数过多,程序退出")
                            print("验证码错误,请重新输入")

        id=input("请输入歌单id:")
        PlaylistData=API.getPlaylist(id,api)
        if not PlaylistData:
            raise Exception("获取歌单信息失败")
        print("歌单: "+PlaylistData['playlist']['name'])
        songlist=[]
        id_name={}
        for i in PlaylistData['playlist']['tracks']:
            songlist.append(i['id'])
            id_name[i['id']]=i['name']
        print("歌单歌曲数量:"+str(len(songlist)))

        savePath=input("请输入保存路径(默认路径: "+(getcwd()+'\\songs\\')+"):")
        savePath=savePath if savePath else (getcwd()+'\\songs\\')
        makedirs(savePath) if not ospath.exists(savePath) else None
        lyricType=input("是否下载歌词(Y/n):").lower()
        if lyricType != "n":
            lyricType=input("请选择歌词保存方式:\n1:独立文件\n2:歌曲内嵌\n(默认:1):")
            if lyricType not in ["1","2"]:
                lyricType="1"
        numThreads=input("请输入下载线程数(默认1):")
        numThreads=int(numThreads) if numThreads else 1

        songInfo=API.getSongInfo(songlist,api)
        if not songInfo:
            raise Exception("获取歌曲信息失败")

        songInfo_dict={j['id']: i for i, j in enumerate(songInfo['songs'])}

        songUrl=API.getSongUrl(songlist,api)
        if not songUrl:
            raise Exception("获取歌曲下载地址失败")

        songFile_list=[]
        for i in songUrl['data']:
            songFile_list.append(API.songFile(savePath+API.to_full_width(id_name[i['id']])+'.'+i['type'],i['id'],i['url'],{"title":songInfo['songs'][songInfo_dict[i['id']]]['name'],"artist":songInfo['songs'][songInfo_dict[i['id']]]['ar'],"album":songInfo['songs'][songInfo_dict[i['id']]]['al']['name'],"picture":songInfo['songs'][songInfo_dict[i['id']]]['al']['picUrl']}))

        threads=[]
        semaphore=threading.Semaphore(numThreads)
        task_id = progress.add_task("Downloading...",total=len(songFile_list))
        progress.start()
        for i in songFile_list:
            semaphore.acquire()
            t = threading.Thread(target=task,args=(i,semaphore))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        progress.stop()

        while faile:#TODO
            for i in faile:
                print(id_name[i['id']]+"下载失败;"+str(i['Exception']))
            if not input("是否重试(Y/n):").lower()=="n":
                songlist=[]
                songFile_list=[]
                for i in faile:
                    songlist.append(i['id'])
                faile=[]
                songUrl=API.getSongUrl(songlist,api)
                for i in songUrl['data']:
                    songFile_list.append(API.songFile(savePath+API.to_full_width(id_name[i['id']])+'.'+i['type'],i['id'],i['url'],{"title":songInfo['songs'][songInfo_dict[i['id']]]['name'],"artist":songInfo['songs'][songInfo_dict[i['id']]]['ar'],"album":songInfo['songs'][songInfo_dict[i['id']]]['al']['name'],"picture":songInfo['songs'][songInfo_dict[i['id']]]['al']['picUrl']}))
            else:
                break
        print("下载完成")

try:
    main()        
except Exception as e:
    raise(e)
