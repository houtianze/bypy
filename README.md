bypy - Python client for Baidu Yun (Personal Cloud Storage) 百度云/百度网盘Python客户端
====================================================================================

[![alt text](https://img.shields.io/pypi/v/bypy.svg "PyPi Version")](https://pypi.python.org/pypi/bypy)
[![alt text](https://img.shields.io/pypi/dm/bypy.svg "PyPi Downloads")](https://pypi.python.org/pypi/bypy)
[![alt text](https://travis-ci.org/houtianze/bypy.svg "Build status")](https://travis-ci.org/houtianze/bypy)
[![Coverage Status](https://coveralls.io/repos/houtianze/bypy/badge.svg?branch=master&service=github)](https://coveralls.io/github/houtianze/bypy?branch=master)
[![Code Climate](https://codeclimate.com/github/houtianze/bypy/badges/gpa.svg)](https://codeclimate.com/github/houtianze/bypy)
[![Join the chat at https://gitter.im/houtianze/bypy](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/houtianze/bypy?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

极简说明
-------

- 安装: `pip install bypy`
- 运行: `bypy`

TL;DR
-----

- To install: `pip install bypy`
- To use: `bypy`

**此项目已经进入维护状态：不会再有新的功能加入，只有在发现重大bug情况下才会有 _可能_ 更新。**

**This is project is now in "maintenance" mode: NO new features will be added, and _may_ be updated only if critical bugs are found.**

---

**如果有人想帮助搭国内建授权服务器的话，请按以下步骤进行:**

1. Clone <https://github.com/houtianze/bypyoauth> 并用任意值配置好环境变量后成功运行服务
2. Fork 此repo，并把你的新服务器地址加到这里 <https://github.com/houtianze/bypy/blob/master/bypy/res/auth.json>
3. 创建拉取请求，然后通过 [![Join the chat at https://gitter.im/houtianze/bypy](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/houtianze/bypy?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) 或者在拉取请求里留下你的联系方式
4. 我测试新服务器可以使用后，通过Gitter/邮件把Secret Key发给你，你用正确的配置启动授权服务器
5. 新的授权服务器配置好后我合并拉取请求
6. 谢谢。

---

中文说明 (English readme is at the bottom)
-----------------------------------------

- 最新: 目录上传/下载/同步加入了多进程支持（`--processes`）

---
这是一个百度云/百度网盘的Python客户端。主要的目的就是在Linux环境下（Windows下应该也可用，但没有仔细测试过）通过命令行来使用百度云盘的2TB的巨大空间。比如，你可以用在Raspberry Pi树莓派上。它提供文件列表、下载、上传、比较、向上同步、向下同步，等操作。

**由于百度PCS API权限限制，程序只能存取百度云端`/apps/bypy`目录下面的文件和目录。**

**（已解决）~~据说百度PCS API最多返回目录下1000个文件（ #285 )，如果属实，百度云盘上若有超过1000个文件的目录，将有一部分文件无法被看到 / 下载~~**

**特征: 支持Unicode/中文；失败重试；递归上传/下载；目录比较; 哈希缓存。**

界面是英文的，主要是因为这个是为了Raspberry Pi树莓派开发的。

程序依赖
------

**重要：需要把系统的区域编码设置为UTF-8。（参见：<http://perlgeek.de/en/article/set-up-a-clean-utf8-environment>)**

安装
---

- 通过`pip`来安装：`pip install bypy` （支持Python 2.7+, 3.3+)

运行
---

- 作为独立程序: 运行 `bypy` (或者`python -m bypy`，或者`python3 -m bypy`）

  可以看到命令行支持的全部命令和参数。
- 作为一个包，在代码中使用: `import bypy`

简单的图形界面：
运行 `bypygui`

基本操作
------

显示使用帮助和所有命令（英文）:

```bash
bypy
```

第一次运行时需要授权，只需跑任何一个命令（比如 `bypy info`）然后跟着说明（登陆等）来授权即可。授权只需一次，一旦成功，以后不会再出现授权提示.

更详细的了解某一个命令：

```bash
bypy help <command>
```

显示在云盘（程序的）根目录下文件列表：

```bash
bypy list
```

把当前目录同步到云盘：

```bash
bypy syncup
```

or

```bash
bypy upload
```

把云盘内容同步到本地来：

```bash
bypy syncdown
```

or

```bash
bypy downdir /
```

**比较本地当前目录和云盘（程序的）根目录（个人认为非常有用）：**

```bash
bypy compare
```

更多命令和详细解释请见运行`bypy`的输出。

调试
---

- 运行时添加`-v`参数，会显示进度详情。
- 运行时添加`-d`，会显示一些调试信息。
- 运行时添加`-ddd`，还会会显示HTTP通讯信息（**警告：非常多**）

整合测试（15 - 30分钟）
-------------------

- 在主目录下跑：`python -m bypy.test`

直接在Python程序中调用
-------------------

```python
from bypy import ByPy
bp=ByPy()
bp.list() # or whatever instance methods of ByPy class
```

经验分享
-------

请移步至[wiki](../../wiki)，方便分享/交流。

授权许可
-------

请阅: [LICENSE](LICENSE)

---

PCS API文档（已失效）: <http://developer.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list> (以前保存的离线版： [baidudoc](baidudoc) directory)

---

Introduction
------------

- Latest feature: Multiprocessing added to directory upload / download / sync（`--processes`）

---
This is a Python client for Baidu Yun (a.k.a PCS - Personal Cloud Storage), an online storage website offering 2 TB (fast) free personal storage. This main purpose is to be able to utilize this storage service under Linux environment (console), e.g. Raspberry Pi.

**Due to Baidu PC permission restrictions, this program can only access your `/apps/bypy` directory at Baidu PCS**

**(Fixed) ~~It's said the Baidu PCS API won't return more than 1000 items inside a directory ( #285 )，if this is true，you won't be able to see / download some files if you have a directory with more than 1000 files on Baidu Cloud~~**

**Features: Unicode / Chinese support; Retry on failures; Recursive down/up-load; Directory comparison; Hash caching.**

Prerequisite
------------

**Important: You need to set you system locale encoding to UTF-8 for this to work (You can refer here: <http://perlgeek.de/en/article/set-up-a-clean-utf8-environment>)**

Installation
------------

- `pip install bypy` (Supports Python 2.7+, 3.3+)

Usage
-----

- Standalone program
  - Simply run `bypy`  (or `python -m bypy`, or `python3 -m bypy`）
  You will see all the commands and parameters it supports

- As a package in your code
  - `import bypy`

Simple GUI:
Run `bypygui`

Getting started
---------------

To get help and a list of available commands:

```bash
bypy
```

To authorize for first time use, run any commands e.g. `bypy info` and follow the instructions (login etc). This is a one-time requirement only.

To get more details about certain command:

```bash
bypy help <command>
```

List files at (App's) root directory at Baidu PCS:

```bash
bypy list
```

To sync up to the cloud (from the current directory):

```bash
bypy syncup
```

or

```bash
bypy upload
```

To sync down from the cloud (to the current directory):

```bash
bypy syncdown
```

or

```bash
bypy downdir /
```

**To compare the current directory to (App's) root directory at Baidu PCS (which I think is very useful):**

```bash
bypy compare
```

To get more information about the commands, check the output of `bypy`.

Debug
-----

- Add in `-v` parameter, it will print more details about the progress.
- Add in `-d` parameter, it will print some debug messages.
- Add in `-ddd`, it will display HTTP messages as well (**Warning: A lot**）

Integration Test (15-30min)
--------------------------

- (In the project root directory) run: `python -m bypy.test`

To call from Python code
------------------------

```python
from bypy import ByPy
bp=ByPy()
bp.list() # or whatever instance methods of ByPy class
```

Tips / Sharing
--------------

Please go to [wiki](../../wiki)

License
---

Please refer to [LICENSE](LICENSE)

---

PCS API Document (link dead 404): <http://developer.baidu.com/wiki/index.php?title=docs/pcs/rest/file_data_apis_list> (Offline pdf retrieved before: [baidudoc](baidudoc) directory)
