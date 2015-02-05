bypy-plus
====

Forked from [houtianze/bypy](https://github.com/houtianze/bypy)

Copyright 2013 Hou Tianze (GitHub: houtianze, Twitter: @ibic, G+: +TianzeHou)

### Introduction

百度云/百度网盘的Python客户端.

A Python client for Baidu  Personal Cloud Storage.

This program uses the REST APIs to access the files at Baidu PCS. You can list, download, upload, compare, sync-up/down, etc.

### Features

#### Enhancement

* PyCurl supporting

#### Original

* Full Unicode support
	* To support Chinese charactors, please set your locale to UTF-8
* Retry on failure
* Recursive down/up-load
* Directory comparison
* Hash caching

### Dependencies

* python2-pycurl
* python2-requests

### Usage

#### Get help and a list of available commands

	bypy
	bypy help <command>

#### Authorize

To authorize for first time use, run any commands e.g. `bypy info` and follow the instructiongs (login etc). This is a one-time requirement only.

#### List files at (App's) root directory at Baidu PCS

	bypy list

#### Sync up to the cloud (from the current directory)

	bypy syncup

or

	bypy upload

#### Sync down from the cloud (to the current directory)

	bypy syncdown

or

	bypy downdir /

#### Compare the current directory to (App's) root directory at Baidu PCS

	bypy compare

#### Debug

Add in "-v" parameter, the program will print more details about the progress.
Add in "-d" parameter, the program will print some debug messages.

### Tips

If you encounter `UnicodeDecodeError` while syncing up/down a directory, it's probably due the encoding of the directory / file names not being UTF-8 (especially if these files are copied from Windows to Unix / Linux). You can fix this using the `convmv` utility (to be issued in the directory to sync)

	convmv -f GBK -t UTF-8 -r * (to see what renamings are going to happen)
	convmv -f GBK -t UTF-8 --notest -r * (performing the actual renaming)


About a bug of Baidu that's affecting syncup. Basically: After a big file uploaded using slices and then combined, Baidu will return the wrong MD5. This will affect comparision (as MD5 is used to assert if the files local and remote are equal), thus will force syncup / syncdown transfer a second time.

Workaround: syncup twice (For the second time, the big files are "rapidly uploaded", which is very fast. Small files that are the same will be skipped. After this, Baidu will return the correct MD5)
