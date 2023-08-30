import requests
from os import path as ospath
from qrcode import QRCode as qrcode
from time import time
from hashlib import md5
from mutagen import flac as mutagen_flac,id3 as mutagen_id3

COOKIE=""

#获取时间戳
def timestamp() -> str:
    return str(int(time()))

#cookie保存和读取
def cookieSave(COOKIE_FILE:str, intput:str="") -> bool:
    global COOKIE
    with open(COOKIE_FILE, 'a+') as f:
        f.seek(0)
        if intput:
            f.truncate()
            f.write(intput)
            COOKIE = intput
            return True
        else:
            COOKIE = f.read().strip()
            if COOKIE:
                return True
            else:
                return False

#符号转换
def to_full_width(text) -> str:
    full_width_symbols = ''
    for char in text:
        if char in r'\/:*?"<>|':
            full_width_char = chr(ord(char) + 0xFEE0)
            full_width_symbols += full_width_char
        else:
            full_width_symbols += char
    return full_width_symbols

#API检查
def apiCheck(api:str) -> bool:
    url=api+'/search?keywords=海阔天空'
    try:
        data=requests.get(url).json()
        if(data['code']==200 and data['result']['songs'][0]['name'] == "海阔天空"):
            return True
    except:
        return False
        

#二维码key获取
def qrcodeKeyGet(api:str) -> str:
    url=api+'/login/qr/key?timestamp='+timestamp()
    data=requests.get(url).json()
    if(data['code']==200):
        key=data['data']['unikey']
        return key
    else:
        raise Exception("二维码获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#二维码生成
def qrcodeGet(key:str,api:str) -> bool:
    url=api+'/login/qr/create?timestamp='+timestamp()
    data={'key':key}
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        print(data['data']['qrurl'])
        qr=qrcode()
        qr.add_data(data['data']['qrurl'])
        qr.print_ascii(invert=True)
        return True
    else:
        raise Exception("二维码生成模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#二维码状态查询
def qrcodeCheck(key:str,api:str) -> dict:
    url=api+'/login/qr/check'
    data={'key':key}
    data=requests.post(url+'?timestamp='+timestamp(),data=data).json()
    if(data['code'] in [801,802,803]):
        return data
    else:
        raise Exception("二维码状态查询模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#验证码获取
def captchaSent(phone:int,ctcode:int,api:str) -> bool:
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
def captchaCheck(phone:int,captcha:int,ctcode:int,api:str) -> bool:
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
def captchaLogin(phone:int,captcha:int,ctcode:int,api:str) -> dict:
    url=api+'/login/cellphone?timestamp='+timestamp()
    data={
        'phone':str(phone),
        'captcha':str(captcha),
        'countrycode':str(ctcode)
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("验证码登录模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#密码登录
def passwordLogin(phone:int,password:str,ctcode:int,api:str) -> dict:
    url=api+'/login/cellphone?timestamp='+timestamp()
    data={
        'phone':str(phone),
        'md5_password':md5(password.encode('utf-8')).hexdigest(),
        'countrycode':str(ctcode)
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("密码登录模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌单
def getPlaylist(id:int,api:str) -> dict:
    url=api+'/playlist/detail?timestamp='+timestamp()
    data={
        'id':str(id),
        'cookie':COOKIE
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌单获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌曲信息
def getSongInfo(songlist:list,api:str) -> dict:
    ids = ""
    for i in songlist:
        ids = ids+str(i)+","
    url=api+'/song/detail?timestamp='+timestamp()
    data={
        'ids':ids.rstrip(','),
        'cookie':COOKIE
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌曲信息获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌词
def getLyric(id:int,api:str) -> dict:
    url=api+'/lyric?id='+str(id)
    data=requests.get(url).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌词获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#获取歌曲url
def getSongUrl(songlist:list,api:str) -> dict:
    id = ""
    for i in songlist:
        id = id+str(i)+","
    url=api+'/song/url/v1?timestamp='+timestamp()
    data={
        'id':id.rstrip(','),
        'cookie':COOKIE,
        'level':'jymaster'
    }
    data=requests.post(url,data=data).json()
    if(data['code']==200):
        return data
    else:
        raise Exception("歌曲url获取模块[Err]:[code]"+str(data['code'])+"[msg]"+data['message'])

#设置歌曲标签
def setSongTag(filePath:str,songTag:dict) -> bool:
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
        if (('lyric' in songTag)and(songTag['lyric'] != None)):
                audiofile['lyrics'] = songTag['lyric']
        if (('picture' in songTag)and(songTag['picture'] != None)):
            response = requests.get(songTag['picture'])
            picture = mutagen_flac.Picture()
            picture.type = 3
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = response.content
            audiofile.clear_pictures()
            audiofile.add_picture(picture)
    elif filetype == '.mp3':
        audiofile = mutagen_id3.ID3(filePath)
        if 'TIT2' in audiofile:
            audiofile['TIT2'].text = title
        else:
            audiofile.add(mutagen_id3.TIT2(encoding=3, text=title))
        if 'TPE1' in audiofile:
            audiofile['TPE1'].text = arist
        else:
            audiofile.add(mutagen_id3.TPE1(encoding=3, text=arist))
        if 'TALB' in audiofile:
            audiofile['TALB'].text = album
        else:
            audiofile.add(mutagen_id3.TALB(encoding=3, text=album))
        if (('lyric' in songTag)and(songTag['lyric'] != None)):
                audiofile['USLT'] = mutagen_id3.USLT(encoding=3, text=songTag['lyric'])
        if (('picture' in songTag)and(songTag['picture'] != None)):
            response = requests.get(songTag['picture'])
            picture = mutagen_id3.APIC(type=3, mime='image/jpeg', desc='Cover', data=response.content)
            audiofile.delall('APIC')
            audiofile.add(picture)
    else:
        raise Exception("歌曲标签设置模块[Err]:不支持的文件类型")
    audiofile.save()
    return True

class songFile:#TODO
    def __init__(self, filePath:str, id:int = None, url:str = None, songTag:dict = None) -> None:
        self.filePath = filePath
        self.id = id
        self.url = url
        self.songTag = songTag
        self.fileName = ospath.splitext(filePath)[0].split('\\')[-1].split('/')[-1]
        self.fileType = ospath.splitext(filePath)[1].lstrip('.').lower()

    def download(self) -> bool:
        if self.url:
            with open(self.filePath, "wb") as file:
                response = requests.get(self.url, stream=True)
                file.write(response.content)
            return True
        return False

    def setTag(self) -> bool:
        if self.songTag:
            return setSongTag(self.filePath,self.songTag)
        return False