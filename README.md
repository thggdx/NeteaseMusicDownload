# NeteaseMusicDownload

**一个用于批量下载网易云音乐歌单中歌曲的py脚本**

依赖[网易云音乐API](https://github.com/Binaryify/NeteaseCloudMusicApi "Binaryify/NeteaseCloudMusicApi")
***
## 运行
```
git clone https://github.com/thggdx/NeteaseMusicDownload.git
cd NeteaseMusicDownload
pip install -r requirements.txt
python ./main.py
```
## 功能/特性
>* 手机号验证码登录
>* 手机号密码登录
>* 扫码登陆
>* 从浏览器获取cookie
>* 登录后Cookie保存(记住登录状态)
>* 多线程批量下载歌单中歌曲
>* 歌曲标签设置(歌曲封面,名称,作者,专辑)
>* 歌词下载(独立文件\歌曲内嵌)
## requirements
```
qrcode
requests
mutagen
rich
```
脚本功能还在完善,欢迎各位大佬指出错误和pr