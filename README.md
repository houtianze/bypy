bypy - Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘Python客户端

====
[![alt text](https://img.shields.io/pypi/v/bypy.svg "PyPi Version")](https://pypi.python.org/pypi/bypy)
[![alt text](https://img.shields.io/pypi/dm/bypy.svg "PyPi Downloads")](https://pypi.python.org/pypi/bypy)
[![alt text](https://travis-ci.org/houtianze/bypy.svg "Build status")](https://travis-ci.org/houtianze/bypy)
[![Coverage Status](https://coveralls.io/repos/houtianze/bypy/badge.svg?branch=master&service=github)](https://coveralls.io/github/houtianze/bypy?branch=master)
[![Code Climate](https://codeclimate.com/github/houtianze/bypy/badges/gpa.svg)](https://codeclimate.com/github/houtianze/bypy)
[![Join the chat at https://gitter.im/houtianze/bypy](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/houtianze/bypy?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

===

中文说明 (English readme is at the bottom)
---
这是一个百度云/百度网盘的Python客户端。主要的目的就是在Linux环境下（Windows下应该也可用，但没有仔细测试过）通过命令行来使用百度云盘的2TB的巨大空间。比如，你可以用在Raspberry Pi树莓派上。它提供文件列表、下载、上传、比较、向上同步、向下同步，等操作。

**由于百度PCS API权限限制，程序只能存取百度云端`/apps/bypy`目录下面的文件和目录。**

**特征: 支持Unicode/中文；失败重试；递归上传/下载；目录比较; 哈希缓存。**

界面是英文的，主要是因为这个是为了Raspberry Pi树莓派开发的。

程序依赖
---
**重要：想要支持中文，你要把系统的区域编码设置为UTF-8。（参见：http://perlgeek.de/en/article/set-up-a-clean-utf8-environment)**

安装
---
- 稳定版：直接通过`pip`来安装：`sudo pip install bypy` （支持Python 2.7+, 3.3+)
- 开发版：`git clone`到任意目录。（为了运行方便，可以把`bypy.py`和`bypygui.pyw`拷贝至`/usr/bin/`目录

运行
---
- 作为独立程序
  - 稳定版（`pip`安装的）：运行 `bypy` (或者`python -m bypy`，或者`python3 -m bypy`）
  - 开发版(`git clone`的）：进入clone目录，运行`./bypy` (或者`python ./bypy`，或者`python3 ./bypy`）

  可以看到命令行支持的全部命令和参数。
- 作为一个包，在代码中使用
  - `import bypy`


简单的图形界面：
`./bypygui.pyw`

要找多线程图形界面的，这个貌似不错：[bcloud](../../../../LiuLang/bcloud)

基本操作
---
显示使用帮助和所有命令（英文）:
```
bypy.py
```

第一次运行时需要授权，只需跑任何一个命令（比如 `bypy.py info`）然后跟着说明（登陆等）来授权即可。授权只需一次，一旦成功，以后不会再出现授权提示.

更详细的了解某一个命令：
```
bypy.py help <command>
```

显示在云盘（程序的）根目录下文件列表：
```
bypy.py list
```

把当前目录同步到云盘：
```
bypy.py syncup
```
or
```
bypy.py upload
```

把云盘内容同步到本地来：
```
bypy.py syncdown
```
or
```
bypy.py downdir /
```

**比较本地当前目录和云盘（程序的）根目录（个人认为非常有用）：**
```
bypy.py compare
```

更多命令和详细解释请见运行`bypy.py`的输出。

调试
---
- 运行时添加`-v`参数，会显示进度详情。
- 运行时添加`-d`，会显示一些调试信息。
- 运行时添加`-ddd`，还会会显示HTTP通讯信息（**警告：非常多**）


经验分享
---
请移步至[wiki](../../wiki)，方便分享/交流。

===
Introduction
---
This is a Python client for Baidu Yun (a.k.a PCS - Personal Cloud Storage), an online storage website offering 2 TB (fast) free personal storage. This main purpose is to be able to utilize this stoarge service under Linux environment (console), e.g. Raspberry Pi.

**Due to Baidu PC permission restrictions, this program can only access your `/apps/bypy` directoy at Baidu PCS**

**Features: Unicode / Chinese support; Retry on failures; Recursive down/up-load; Directory comparison; Hash caching.**

Prerequisite
---
**Important: You need to set you system locale encoding to UTF-8 for this to work (You can refere here: http://perlgeek.de/en/article/set-up-a-clean-utf8-environment)**

**Important: You need to install the [Python Requests library](http://www.python-requests.org/).** In Debian / Ubuntu / Raspbian, you just run the following command:
```
sudo pip install requests
```

Installation
---
- Stable Release: `sudo pip install bypy` (Supports Python 2.7+, 3.3+)
- Development Version: `git clone` to any directory. (You can copy `bypy.py` and `bypygui.pyw` to `/usr/bin/` for easier command execution)


Usage
---
- Standalone program
  - Stable Release (installed by `pip`): Simply run `bypy`  (or `python -m bypy`, or `python3 -m bypy`）
  - Deveopment Version: cd to the directory where it is cloned, and run:`./bypy.py`  (or `python -m bypy`, or `python3 -m bypy`）
  You will see all the commands and parameters it supports

- As a package in your code
  - `import bypy`

Simple GUI:
`./bypygui.pyw`

For advanced GUI with parallel downloading capbility, this seems a good choice: [bcloud](../../../../LiuLang/bcloud)

Getting started
---
To get help and a list of available commands:
```
bypy.py
```

To authorize for first time use, run any commands e.g. `bypy.py info` and follow the instructiongs (login etc). This is a one-time requirement only.

To get more details about certain command:
```
bypy.py help <command>
```

List files at (App's) root directory at Baidu PCS:
```
bypy.py list
```

To sync up to the cloud (from the current directory):
```
bypy.py syncup
```
or
```
bypy.py upload
```

To sync down from the cloud (to the current directory):
```
bypy.py syncdown
```
or
```
bypy.py downdir /
```

**To compare the current directory to (App's) root directory at Baidu PCS (which I think is very useful):**
```
bypy.py compare
```

To get more information about the commands, check the output of `bypy.py`.

Debug
---
- Add in `-v` parameter, it will print more details about the progress.
- Add in `-d` parameter, it will print some debug messages.
- Add in `-ddd`, it will display HTTP messages as well (**Warning: A lot**）

Tips / Sharing
---
Please go to [wiki](../../wiki)

===
Copyright 2015: Hou Tianze (GitHub: houtianze)
License: MIT
