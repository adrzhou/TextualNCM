# TextualNCM
一款用 Python 3 编写，基于 [Textual][1] 和 [pyncm][2] 开发的网易云音乐命令行客户端

## 依赖
音频文件的播放借助 [VLC media player][8] 完成  
使用本软件之前请安装 VLC media player

## 安装

您可以通过安装发行版本或运行源代码来使用本程序

### 发行版本

目前只推出了适用于`Windows 10` 64位操作系统和`GNU/Linux`的发行版本  
请前往 [Releases][3] 页面下载压缩包

### 源代码

任何安装了 Python 3.8+ 的设备都可以运行此程序  
除此之外，您还需要安装一下外部库

| 名称 | 安装命令 |
|---|---|
|[Textual][1]| `pip install textual` |
|[requests][4]| `pip install requests` |
|[Flask][5]| `pip install flask` |
|[python-vlc][7]| `pip install python-vlc` |
|[adrzhou/pyncm][6]| * |

*注: 此为 [mos9527/pyncm][2] 的 fork，请复制代码仓库至本地后用此命令安装
`python setup.py install`

[1]: https://textual.textualize.io/
[2]: https://github.com/mos9527/pyncm
[3]: https://github.com/adrzhou/TextualNCM/releases/
[4]: https://pypi.org/project/requests/
[5]: https://flask.palletsprojects.com/en/2.2.x/
[6]: https://github.com/adrzhou/pyncm
[7]: https://pypi.org/project/python-vlc/
[8]: https://www.videolan.org/vlc/
