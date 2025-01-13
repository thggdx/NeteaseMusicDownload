import logging
import threading
from getpass import getpass
from json import dump as jsondump
from json import load as jsonload
from os import getcwd, makedirs
from os import path as ospath
from time import localtime, sleep, strftime
from webbrowser import open as openweb

from browser_cookie3 import load as browser_cookie_load
from rich.progress import Progress

import API

DEBUG = False  # 调试模式开关(!警告!: 开启后日志中可能会记录部分敏感信息!)

progress = Progress()
task_id = None
lyricType = ''
fail = []


def log_init():
    LOGS_PATH = ospath.dirname(ospath.abspath(__file__)) + '/logs/'
    makedirs(LOGS_PATH) if not ospath.exists(LOGS_PATH) else None
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) if DEBUG else logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOGS_PATH + strftime('%Y-%m-%d_%H-%M-%S', localtime()) + '.log', encoding='utf-8', mode='w')
    fh.setLevel(logging.DEBUG) if DEBUG else fh.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] : %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def task(songFile, semaphore):
    global fail
    try:
        if songFile.download():
            PathData['songs'].append(songFile.id)
            if lyricType != 'n':
                lyric = API.getLyric(songFile.id, api)
                if lyric and ('lrc' in lyric):
                    lyric = lyric['lrc']['lyric']
                    if lyricType == '1':
                        with open(ospath.splitext(songFile.filePath)[0] + '.lrc', 'w', encoding='utf-8') as f:
                            f.write(lyric)
                    elif lyricType == '2':
                        songFile.songTag['lyric'] = lyric
            songFile.setTag()
    except Exception as e:
        fail.append({'id': songFile.id, 'Exception': e})
    finally:
        progress.update(task_id, advance=1)
        semaphore.release()


def main():
    global api
    global lyricType
    global progress
    global task_id
    global fail
    global PathData

    print('当前工作路径: ' + getcwd())
    logger.info('当前工作路径: ' + getcwd())
    api = input('请输入API地址(可跳过):').rstrip('/')
    api = api if api else 'https://ncm-api.thggdx.eu.org'
    logger.info('API地址: ' + api)
    COOKIE_FILE = ospath.dirname(ospath.abspath(__file__)) + '/.NeteaseMusic_Cookie'
    if 'temp' in COOKIE_FILE.lower():
        COOKIE_FILE = ospath.expanduser('~') + '/.NeteaseMusic_Cookie'
    logger.debug('COOKIE_FILE: ' + COOKIE_FILE)

    if not API.apiCheck(api):
        logger.error('API无效')
        raise Exception('API无效')
    if not API.cookieSave(COOKIE_FILE):
        logger.info('未登录')
        while True:
            print('未登录，请选择登陆方式\n1:扫码登陆\n2:手机密码登陆\n3:手机验证码登陆\n4:从浏览器导入cookie')
            loginType = input('请输入登陆方式:')
            if loginType not in ['1', '2', '3', '4']:
                print('输入错误')
                continue
            break
        if loginType == '1':
            logger.info('登陆方式: 扫码登陆')
            key = API.qrcodeKeyGet(api)
            logger.debug('二维码key: ' + key)
            API.qrcodeGet(key, api)
            stats = True
            while True:
                sleep(1)
                data = API.qrcodeCheck(key, api)
                if data['code'] == 801:
                    continue
                elif data['code'] == 802:
                    if stats:
                        print('User: ' + data['nickname'] + ' 已扫码,请在手机上确认登录')
                        stats = False
                    continue
                elif data['code'] == 803:
                    API.cookieSave(COOKIE_FILE, data['cookie'])
                    print('登陆成功')
                    logger.info('登陆成功')
                    break
        elif loginType == '4':
            logger.info('登陆方式: 从浏览器导入cookie')
            cookies = browser_cookie_load(domain_name='music.163.com')
            cookie = ''
            for i in cookies:
                if i.name == 'MUSIC_U':
                    cookie = i.value
                    break
            if cookie:
                API.cookieSave(COOKIE_FILE, ('MUSIC_U=' + cookie))
                data = API.getAccountInfo(api)
                print('name: ' + data['profile']['nickname'] + '\nid: ' + str(data['profile']['userId']) + '\n登录成功')
                logger.info('登录成功')
            else:
                print('未登录,请在浏览器中登录后重试')
                logger.warning('未从浏览器中获取到cookie')
                openweb('music.163.com/login')
                exit()
        else:
            ctcode = input('请输入手机号国家代码(默认86):')
            ctcode = ctcode if ctcode else '86'
            phone = input('请输入手机号:')
            if loginType == '2':
                logger.info('登陆方式: 手机密码登陆')
                password = getpass('请输入密码:')
                data = API.passwordLogin(phone, password, ctcode, api)
                API.cookieSave(COOKIE_FILE, data['cookie'])
                print('name: ' + data['profile']['nickname'] + '\nid: ' + str(data['profile']['userId']) + '\n登录成功')
                logger.info('登录成功')
            if loginType == '3':
                logger.info('登陆方式: 手机验证码登陆')
                API.captchaSent(phone, ctcode, api)
                print('验证码已发送至+' + ctcode + ' ' + phone)
                for i in range(3):
                    captcha = input('请输入验证码:')
                    if API.captchaCheck(phone, captcha, ctcode, api):
                        data = API.captchaLogin(phone, captcha, ctcode, api)
                        API.cookieSave(COOKIE_FILE, data['cookie'])
                        print('name: ' + data['profile']['nickname'] + '\nid: ' + str(data['profile']['userId']) + '\n登录成功')
                        logger.info('登录成功')
                        break
                    else:
                        if i == 2:
                            logger.error('验证码错误次数过多,程序退出')
                            raise Exception('验证码错误次数过多,程序退出')
                        print('验证码错误,请重新输入')

    id = input('请输入歌单id:')
    logger.info('歌单id: ' + str(id))
    PlaylistData = API.getPlaylist(id, api)
    if not PlaylistData:
        logger.error('获取歌单信息失败')
        raise Exception('获取歌单信息失败')
    print('歌单: ' + PlaylistData['playlist']['name'])
    songlist = []
    for i in PlaylistData['playlist']['trackIds']:
        songlist.append(i['id'])
    print('歌单歌曲数量:' + str(len(songlist)))

    savePath = input('请输入保存路径(默认路径: ' + (getcwd() + '/' + PlaylistData['playlist']['name'] + '/') + '):')
    savePath = savePath if savePath else (getcwd() + '/' + PlaylistData['playlist']['name'] + '/')
    savePath = savePath if savePath.endswith(('/', '\\')) else savePath + '/'
    logger.debug('保存路径: ' + savePath)

    if ospath.exists(savePath) and ospath.isdir(savePath):
        if ospath.exists(savePath + '/PathData.json') and ospath.getsize(savePath + '/PathData.json') > 0:
            with open(savePath + '/PathData.json', 'r') as f:
                PathData = jsonload(f)
        else:
            PathData = {'songs': []}
    else:
        makedirs(savePath)
        PathData = {'songs': []}

    songlist = list(set(songlist) - set(PathData['songs']))
    if not songlist:
        logger.info('歌单中歌曲均已存在')
        print('歌单中歌曲均已存在')
        return
    logger.info('待下载歌曲数量: ' + str(len(songlist)))
    print('待下载歌曲数量:' + str(len(songlist)))

    lyricType = input('是否下载歌词(Y/n):').lower()
    if lyricType != 'n':
        lyricType = input('请选择歌词保存方式:\n1:独立文件\n2:歌曲内嵌\n(默认:1):')
        if lyricType not in ['1', '2']:
            lyricType = '1'
    logger.info('歌词保存方式: ' + lyricType)
    numThreads = input('请输入下载线程数(默认1):')
    numThreads = int(numThreads) if numThreads else 1
    logger.info('下载线程数: ' + str(numThreads))

    songInfo = API.getSongInfo(songlist, api)
    if not songInfo:
        logger.error('获取歌曲信息失败')
        raise Exception('获取歌曲信息失败')

    id_name = {}
    songInfo_dict = {}
    for i, j in enumerate(songInfo['songs']):
        songInfo_dict[j['id']] = i
        id_name[j['id']] = j['name']

    songUrl = API.getSongUrl(songlist, api)
    if not songUrl:
        logger.error('获取歌曲下载地址失败')
        raise Exception('获取歌曲下载地址失败')

    songFile_list = []
    for i in songUrl['data']:
        if not i['url']:
            pass
        else:
            songFile_list.append(
                API.SongFile(
                    savePath + API.to_full_width(id_name[i['id']]) + '.' + i['type'],
                    i['id'],
                    i['url'],
                    {
                        'title': songInfo['songs'][songInfo_dict[i['id']]]['name'],
                        'artist': songInfo['songs'][songInfo_dict[i['id']]]['ar'],
                        'album': songInfo['songs'][songInfo_dict[i['id']]]['al']['name'],
                        'picture': songInfo['songs'][songInfo_dict[i['id']]]['al']['picUrl'] + '?param=3000y3000',
                    },
                )
            )

    threads = []
    semaphore = threading.Semaphore(numThreads)
    task_id = progress.add_task('Downloading...', total=len(songFile_list))
    progress.start()
    for i in songFile_list:
        semaphore.acquire()
        t = threading.Thread(target=task, args=(i, semaphore))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    progress.stop()

    while fail:  # TODO
        for i in fail:
            print(id_name[i['id']] + ' 下载失败;' + str(i['Exception']))
        if not input('是否重试(Y/n):').lower() == 'n':
            songlist = []
            songFile_list = []
            for i in fail:
                songlist.append(i['id'])
            fail = []
            songUrl = API.getSongUrl(songlist, api)
            for i in songUrl['data']:
                songFile_list.append(
                    API.SongFile(
                        savePath + API.to_full_width(id_name[i['id']]) + '.' + i['type'],
                        i['id'],
                        i['url'],
                        {
                            'title': songInfo['songs'][songInfo_dict[i['id']]]['name'],
                            'artist': songInfo['songs'][songInfo_dict[i['id']]]['ar'],
                            'album': songInfo['songs'][songInfo_dict[i['id']]]['al']['name'],
                            'picture': songInfo['songs'][songInfo_dict[i['id']]]['al']['picUrl'] + '?param=3000y3000',
                        },
                    )
                )
        else:
            break

    with open(savePath + '/PathData.json', 'w') as f:
        PathData['changeTime'] = strftime('%Y-%m-%d %H:%M:%S', localtime())
        jsondump(PathData, f)

    logger.info('下载完成')
    print('下载完成')


try:
    logger = log_init()
    main()
    logger.info('程序正常退出')
except Exception as e:
    logger.exception('An error occurred: %s', e)
    logger.error('程序异常退出')
    print(str(e) + '\n程序异常退出')
