import API
from os import getcwd
from time import sleep
from getpass import getpass

print("当前工作路径"+getcwd())
api=input("请输入API地址(可跳过):").rstrip('/')
api=api if api else "https://ncm-api.thggdx.eu.org"

try:
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
                    data=API.passwordLogin(phone,password,ctcode,api) # type: ignore
                    print("name: "+str(data['name'])+"\nid: "+str(data['id']))
                if loginType=="3":
                    API.captchaSent(phone,ctcode,api) # type: ignore
                    print("验证码已发送至+"+ctcode+" "+phone)
                    for i in range(3):
                        captcha=input("请输入验证码:")
                        if API.captchaCheck(phone,captcha,ctcode,api): # type: ignore
                            data=API.captchaLogin(phone,captcha,ctcode,api) # type: ignore
                            print("name: "+str(data['name'])+"\nid: "+str(data['id']))
                            break
                        else:
                            if i==2:
                                raise Exception("验证码错误次数过多,程序退出")
                            print("验证码错误,请重新输入")

        id=input("请输入歌单id:")
        PlaylistData=API.getPlaylist(id,api) # type: ignore
        if not PlaylistData:
            exit()

        songlist=[]
        id_name={}
        for i in PlaylistData['playlist']['tracks']:
            songlist.append(i['id'])
            id_name[i['id']]=i['name']
        print("歌单歌曲数量:"+str(len(songlist)))
        
        numThreads=int(input("请输入下载线程数(默认1):"))

        songInfo=API.getSongInfo(songlist,api)
        if not songInfo:
            raise Exception("获取歌曲信息失败")
        
        songInfo_dict={j['id']: i for i, j in enumerate(songInfo['songs'])}

        songUrl=API.getSongUrl(songlist,api)
        if not songUrl:
            raise Exception("获取歌曲下载地址失败")
            
        songDownloadlist=[]
        for i in songUrl['data']:
            songDownloadlist.append({"id":i['id'],"name":id_name[i['id']],"type":i['type'],"url":i['url'],"songTag":{"title":songInfo['songs'][songInfo_dict[i['id']]]['name'],"artist":songInfo['songs'][songInfo_dict[i['id']]]['ar'],"album":songInfo['songs'][songInfo_dict[i['id']]]['al']['name'],"picture":songInfo['songs'][songInfo_dict[i['id']]]['al']['picUrl']}})

        data=API.downloadSong(songDownloadlist,getcwd()+"\\songs\\",numThreads,False)
        
        while data:
            for i in data:
                print(i['name']+"下载失败")
            print("是否重试?")
            if not input("Y/n:").lower()=="n":
                songlist=[]
                for i in data:
                    songlist.append(i['id'])
                songUrl=API.getSongUrl(songlist,api)
                songDownloadlist=[]
                for i in songUrl['data']:
                    songDownloadlist.append({"id":i['id'],"name":id_name[i['id']],"type":i['type'],"url":i['url']})
                data=API.downloadSong(songDownloadlist,getcwd()+"\\songs\\",numThreads,False)
            else:
                break

        print("下载完成")
        
except Exception as e:
    print(e)
