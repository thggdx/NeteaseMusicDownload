import requests
import threading
from os import path as ospath,makedirs
from qrcode import QRCode as qr
from time import time
from hashlib import md5
from tqdm import tqdm
from mutagen import flac as mutagen_flac,id3 as mutagen_id3

cookie=""
COOKIE_FILE = ospath.dirname(ospath.abspath(__file__))+'/.NeteaseMusic_Cookie'
if 'temp' in COOKIE_FILE.lower():
    COOKIE_FILE = ospath.expanduser('~')+'/.NeteaseMusic_Cookie'

#获取时间戳
def timestamp():
    return str(int(time()))

#cookie保存和读取
def cookieSave(intput:str=""):
    global cookie
    with open(COOKIE_FILE, 'a+') as f:
        f.seek(0)
        if intput:
            f.truncate()
            f.write(intput)
            cookie = intput
            return True
        else:
            cookie = f.read().strip()
            if cookie:
                return True
            else:
                return False

#符号转换
def to_full_width(text):
    full_width_symbols = ''
    for char in text:
        if char in r'\/:*?"<>|':
            full_width_char = chr(ord(char) + 0xFEE0)
            full_width_symbols += full_width_char
        else:
            full_width_symbols += char
    return full_width_symbols

#API检查
def apiCheck(api:str):
    url=api+'/search?keywords=海阔天空'
    try:
        data=requests.get(url).json()
        if(data['code']==200 and data['result']['songs'][0]['name'] == "海阔天空"):
            return True
        else:
            raise Exception("API检查模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])
    except:
        raise Exception("API检查模块[Err]:API无效")

#二维码key获取
def qrcodeKeyGet(api:str):
    url=api+'/login/qr/key?timestamp='+timestamp()
    data=requests.get(url).json()
    if(data['code']==200):
        key=data['data']['unikey']
        return key
    else:
        raise Exception("二维码获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#二维码生成
def qrcodeGet(key:str,api:str):
    url=api+'/login/qr/create?timestamp='+timestamp()
    data={'key':key}
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        print(data['data']['qrurl'])
        qr().add_data(data['data']['qrurl'])
        qr().print_ascii(invert=True)
        return True
    else:
        raise Exception("二维码生成模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#二维码状态查询
def qrcodeCheck(key:str,api:str):
    url=api+'/login/qr/check'
    data1={'key':key}
    data=requests.post(url+'?timestamp='+timestamp(),data=data1).json()
    code=data['code']
    if(code==800):
        raise Exception("二维码状态查询模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])
    elif(code==801):
        return {'code':801,'status':'等待扫码'}
    elif(code==802):
        return {'code':802,'name':data['nickname'],'status':'等待确认'}
    elif(code==803):
        cookieSave(data['cookie'])
        return {'code':803,'status':'登录成功'}
    else:
        raise Exception("二维码状态查询模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#验证码获取
def captchaSent(phone:int,ctcode:int,api:str):
    url=api+'/captcha/sent?timestamp='+timestamp()
    data={
        'phone':str(phone),
        'ctcode':str(ctcode)
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return True
    else:
        raise Exception("验证码发送模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#验证码验证
def captchaCheck(phone:int,captcha:int,ctcode:int,api:str):
    url=api+'/captcha/verify?timestamp='+timestamp()
    data={
        'phone':str(phone),
        'captcha':str(captcha),
        'ctcode':str(ctcode)
    }
    data=requests.post(url,data=data).json()
    if(data['code']==503):
        return False
    elif(data['code']==200):
        return True
    else:
        raise Exception("验证码验证模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#验证码登录
def captchaLogin(phone:int,captcha:int,ctcode:int,api:str):
    url=api+'/login/cellphone?timestamp='+timestamp()
    data={
        'phone':str(phone),
        'captcha':str(captcha),
        'countrycode':str(ctcode)
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        cookieSave(data['cookie'])
        return {'name':data['profile']['nickname'],'id':data['profile']['userId'],'token':data['token']}
    else:
        raise Exception("验证码登录模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#密码登录
def passwordLogin(phone:int,password:str,ctcode:int,api:str):
    url=api+'/login/cellphone?timestamp='+timestamp()
    data={
        'phone':str(phone),
        'md5_password':md5(password.encode('utf-8')).hexdigest(),
        'countrycode':str(ctcode)
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        cookieSave(data['cookie'])
        return {'name':data['profile']['nickname'],'id':data['profile']['userId'],'token':data['token']}
    else:
        raise Exception("密码登录模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌单
def getPlaylist(id:int,api:str):
    url=api+'/playlist/detail?timestamp='+timestamp()
    data={
        'id':str(id),
        'cookie':cookie
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌单获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌曲信息
def getSongInfo(songlist:list,api:str):
    ids = ""
    for i in songlist:
        ids = ids+str(i)+","
    url=api+'/song/detail?timestamp='+timestamp()
    data={
        'ids':ids.rstrip(','),
        'cookie':cookie
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌曲信息获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌曲url
def getSongUrl(songlist:list,api:str):
    id = ""
    for i in songlist:
        id = id+str(i)+","
    url=api+'/song/url/v1?timestamp='+timestamp()
    data={
        'id':id.rstrip(','),
        'cookie':cookie,
        'level':'jymaster'
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌曲url获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#下载歌曲
def downloadSong(songUrl:list,savePath:str,numThreads:int=1,showProgress:bool=True):
    def download(i,semaphore):
        if i['url'] == None:
            failed.append({'name':i['name'],'id':i['id']})
            semaphore.release()
            return
        try:
            print("Downloading: " + i['name'] + "." +  i['type'])
            filePath = (savePath + to_full_width(i['name']) + "." + i['type'])
            with open(filePath, "wb") as file:
                response = requests.get(i['url'], stream=True)
                total_length = int(response.headers.get('content-length', 0))
                if total_length is None:
                    file.write(response.content)
                else:
                    if showProgress:
                        pbar=tqdm(total=total_length,unit='B',unit_scale=True)
                        for data in response.iter_content(chunk_size=4096):
                            file.write(data)
                            pbar.update(len(data))
                        pbar.close() 
                    else:
                        file.write(response.content)
            try:
                if "songTag" in i:
                    setSongTag(filePath,i['songTag'])
            except Exception as e:
                print("歌曲标签设置失败: "+str(e))
        except Exception as e:
            failed.append({'name':i['name'],'id':i['id'],'info':str(e)})
        semaphore.release()

    failed = []

    if not ospath.exists(savePath):
        makedirs(savePath)
    semaphore = threading.Semaphore(numThreads)
    threads = []
    for i in songUrl:
        semaphore.acquire()
        t = threading.Thread(target=download, args=(i, semaphore))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return failed

#设置歌曲标签
def setSongTag(filePath:str,songTag:dict):
    filetype = ospath.splitext(filePath)[1].lower()
    title = songTag['title']
    album = songTag['album']
    arist = []
    for i in songTag['artist']:
        arist.append(i['name'])
    if filetype == '.flac':
        audiofile = mutagen_flac.FLAC(filePath)
        audiofile['title'] = title
        audiofile['artist'] = arist
        audiofile['album'] = album
        if (('picture' in songTag)and(songTag['picture'] != None)):
            response = requests.get(songTag['picture'])
            picture = mutagen_flac.Picture()
            picture.type = 3
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = response.content
            audiofile.clear_pictures()
            audiofile.add_picture(picture)
    elif filetype == '.mp3':#TODO
        audiofile = mutagen_id3.ID3(filePath)
        if 'TIT2' in audiofile:
            audiofile['TIT2'].text = title
        else:
            audiofile.add(mutagen_id3.TIT2(encoding=3, text=title)) # type: ignore
        if 'TPE1' in audiofile:
            audiofile['TPE1'].text = arist
        else:
            audiofile.add(mutagen_id3.TPE1(encoding=3, text=arist)) # type: ignore
        if 'TALB' in audiofile:
            audiofile['TALB'].text = album
        else:
            audiofile.add(mutagen_id3.TALB(encoding=3, text=album)) # type: ignore
        if (('picture' in songTag)and(songTag['picture'] != None)):
            response = requests.get(songTag['picture'])
            picture = mutagen_id3.APIC(type=3, mime='image/jpeg', desc='Cover', data=response.content) # type: ignore
            audiofile.delall('APIC')
            audiofile.add(picture)
    else:
        raise Exception("歌曲标签设置模块[Err]:不支持的文件类型")
    audiofile.save()
    return True
    