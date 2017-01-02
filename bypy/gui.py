#!/usr/bin/env python
# coding=utf-8

# A simple GUI for bypy, using Tkinter
# Copyright 2013 Hou Tianze (GitHub: houtianze, Twitter: @ibic, G+: +TianzeHou)
# Licensed under the GPLv3
# https://www.gnu.org/licenses/gpl-3.0.txt

# from __future__ imports must occur at the beginning of the file
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import sys
import threading

vi = sys.version_info
if vi[0] == 2:
	import Tkinter as tk
	import tkFileDialog
	import tkMessageBox
	import ttk
elif vi[0] == 3:
	import tkinter as tk
	from tkinter import filedialog as tkFileDialog, messagebox as tkMessageBox, ttk

from . import const
from . import monkey
from .util import (get_pcs_path)
from .tkutil import (
	ColorMap, fgtag, bgtag,
	Stretch, GridStyle, MyLogText,
	centerwindow)
from .bypy import ByPy

GuiTitle = "Bypy GUI"

class RemoteListGui(tk.Toplevel):
	# remotepath is the partial path,
	# NOT including the '/apps/bypy' in front
	def __init__(self, master, byp, remotepath = ''):
		tk.Toplevel.__init__(self, master)

		self.byp = byp
		self.rpath = get_pcs_path(remotepath)
		self.result = ''

		self.transient(master)
		self.master = master
		title = 'Baidu: ' + self.rpath
		self.title(title)

		self.CreateWidgets()
		self.geometry('400x300+0+0')
		self.GetRemote()

		self.grab_set()

	def GetRemoteAct(self, r, args):
		self.wList.delete(0, tk.END)
		if self.rpath.strip('/') != const.AppPcsPath.strip('/'):
			self.wList.insert(tk.END, '..')
		try:
			j = r.json()
			for f in j['list']:
				fullpath = f['path']
				relpath = fullpath.split('/')[-1]
				self.wList.insert(tk.END,
					relpath + '/' if f['isdir'] else relpath)

			return const.ENoError
		except:
			return const.EException

	def GetRemote(self):
		pars = {
			'method' : 'list',
			'path' : self.rpath,
			'by' : 'name',
			'order' : 'asc' }

		result = self.byp._ByPy__get(
			const.PcsUrl + 'file', pars, self.GetRemoteAct)

		if result == const.ENoError:
			self.title(self.rpath)
		else:
			if self.rpath.strip('/') == const.AppPcsPath.strip('/'):
				err = "Can't retrieve Baidu PCS directories!\n" + \
					"Maybe the network is down?\n" + \
					"You can still manually input the remote path though" + \
					"(But, I doubt it will work)"
				tkMessageBox.showerror(GuiTitle, err)
				self.Bye()
			else:
				self.rpath = const.get_pcs_path('')
				self.GetRemote()

	def Bye(self, result = ''):
		self.result = result
		self.master.focus_set()
		self.destroy()

	def Delete(self, selected):
		if tkMessageBox.askyesno(
			title = GuiTitle,
			message = "Are you sure you want to delete '{}' at Baidu?".format(selected),
			parent = self):
			rpath = '/'.join([self.rpath, selected])
			r = self.byp._ByPy__delete(rpath)
			if r == const.ENoError:
				self.wList.delete(tk.ANCHOR)
			else:
				tkMessageBox.showerror(
					title = GuiTitle,
					message = "Fail to delete '{}' at Baidu".format(selected),
					parent = self)

	def Select(self, event):
		if event.widget == self.wOK:
			self.Bye(self.rpath[len(const.AppPcsPath):])
		elif event.widget == self.wList:
			selected = ''
			iet = int(event.type) # i don't know why, but it seems needed
			if iet == 4: # mouse event. mouse is special or not?
				selected = self.wList.get(self.wList.nearest(event.y))
			elif iet == 2: # KeyPress
				selected = self.wList.get(tk.ACTIVE)

			if iet == 4 or \
				(iet == 2 and event.keysym == 'Return'):
				if selected[-1] == '/':
					self.rpath = '/'.join([self.rpath, selected[:-1]])
					self.GetRemote()
				elif selected == '..':
					self.rpath = '/'.join(self.rpath.split('/')[:-1])
					self.GetRemote()
				else:
					self.Bye('/'.join([self.rpath, selected])[len(const.AppPcsPath):])
			elif iet == 2 and event.keysym == 'Delete':
				# don't handlle this, not so rational usage
				if selected != '..':
					self.Delete(selected)

	def CreateWidgets(self):
		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(0, weight = 1)
		self.wList = tk.Listbox(self)
		self.wList.grid(sticky = Stretch, **GridStyle)
		self.wList.bind('<Double-Button-1>', self.Select)
		self.wList.bind('<Return>', self.Select)
		self.wList.bind('<Delete>', self.Select)
		self.wOK = tk.Button(self, text = 'OK', default = tk.ACTIVE)
		self.wOK.grid(row = 1, column = 0, sticky = tk.E + tk.W, **GridStyle)
		self.wOK.bind('<Button-1>', self.Select)
		self.wOK.bind('<Return>', self.Select)

		self.wList.focus_set()

		self.protocol("WM_DELETE_WINDOW", lambda: ())

class BypyGui(tk.Frame):
	# function remapping / hijacking
	# pr and prcolor functions in console and GUI are different:
	#   in console: pr is the foundamental function, prcolor calls it
	#   in GUI: prcolor is the foundamental fucntion, pr calls it
	def __init__(self, master = None):
		tk.Frame.__init__(self, master)

		self.master.title(GuiTitle)
		self.grid(sticky = Stretch)

		self.byp = None

		self.threadrunning = False

		self.localPath = tk.StringVar()
		self.localPath.set('/tmp')
		self.remotePath = tk.StringVar()
		self.bLog = tk.IntVar()
		self.bLog.set(1)
		self.bSyncDelete = tk.IntVar()
		self.bSyncDelete.set(0)
		self.progress = tk.IntVar()
		self.progress.set(0)
		self.maxProgress = 1000

		self.CreateWidgets()

		monkey.setgui(self)

		self.initbypy()

	def CreateWidgets(self):
		self.master.grid_columnconfigure(0, weight = 1)
		self.master.grid_rowconfigure(1, weight = 1)
		self.grid_columnconfigure(1, weight = 1)
		self.grid_rowconfigure(4, weight = 1)

		z = tk.Label(self, text = 'Baidu: ' + const.AppPcsPath)
		z.grid(row = 0, column = 0, **GridStyle)
		self.wRemotePath = tk.Entry(self, textvariable = self.remotePath)
		self.wRemotePath.grid(row = 0, column = 1, sticky = Stretch, **GridStyle)
		self.wRemoteSelect = tk.Button(self, text = 'R', underline = 0)
		self.wRemoteSelect.grid(row = 0, column = 2, **GridStyle)
		self.wRemoteSelect.bind('<Button-1>', self.selectremotepath)
		self.bind_all('<Alt-r>', self.selectremotepath)

		z = tk.Label(self, text = 'Local 本地')
		z.grid(**GridStyle)
		self.wLocalPath = tk.Entry(self, textvariable = self.localPath)
		self.wLocalPath.grid(row = 1, column = 1, sticky = Stretch, **GridStyle)
		self.wLocalSelect = tk.Button(self, text = 'L', underline = 0)
		self.wLocalSelect.grid(row = 1, column = 2, **GridStyle)
		self.wLocalSelect.bind('<Button-1>', self.selectlocalpath)
		self.bind_all('<Alt-l>', self.selectlocalpath)

		self.OpFrame = tk.Frame(self)
		self.OpFrame.grid(row = 2, columnspan = 3, sticky = Stretch, **GridStyle)
		self.OpFrame.grid_columnconfigure(0, weight = 1)
		self.OpFrame.grid_columnconfigure(1, weight = 1)
		self.OpFrame.grid_columnconfigure(2, weight = 1)
		self.OpFrame.grid_columnconfigure(3, weight = 1)
		self.OpFrame.grid_columnconfigure(3, weight = 1)
		self.OpFrame.grid_columnconfigure(4, weight = 1)

		self.wSyncUp = tk.Button(self.OpFrame, text = 'Sync Up 上传同步', underline = 5)
		self.wSyncUp.grid(sticky = Stretch, **GridStyle)
		self.wSyncUp.bind('<Button-1>', self.startsyncup)
		self.bind_all('<Alt-u>', self.startsyncup)

		self.wUpload = tk.Button(self.OpFrame, text = 'Upload 上传')
		self.wUpload.grid(row = 0, column = 1, sticky = Stretch, **GridStyle)
		self.wUpload.bind('<Button-1>', self.startupload)

		self.wSyncDown = tk.Button(self.OpFrame, text = 'Sync Down 下载同步', underline = 5)
		self.wSyncDown.grid(row = 0, column = 2, sticky = Stretch, **GridStyle)
		self.wSyncDown.bind('<Button-1>', self.startsyncdown)
		self.bind_all('<Alt-d>', self.startsyncdown)

		self.wDownload = tk.Button(self.OpFrame, text = 'Download 下载')
		self.wDownload.grid(row = 0, column = 3, sticky = Stretch, **GridStyle)
		self.wDownload.bind('<Button-1>', self.startdownload)

		self.wSyncDelete = tk.Checkbutton(self.OpFrame, text = 'Sync Del 同步删除', underline = 7, variable = self.bSyncDelete)
		self.wSyncDelete.configure(foreground = 'red')
		self.wSyncDelete.grid(row = 0, column = 4, sticky = Stretch, **GridStyle)
		self.bind_all('<Alt-l>', lambda e: self.bSyncDelete.set(1 if self.bSyncDelete.get() == 0 else 0))
		self.wEnableLog = tk.Checkbutton(self.OpFrame, text = 'Log 日志', underline = 2, variable = self.bLog)
		self.wEnableLog.grid(row = 0, column = 5, sticky = Stretch, **GridStyle)
		self.bind_all('<Alt-g>', lambda e: self.bLog.set(1 if self.bLog.get() == 0 else 0))

		self.wCompare = tk.Button(self.OpFrame, text = 'Compare Dir 比较目录')
		self.wCompare.grid(row = 1, column = 0, sticky = Stretch, **GridStyle)
		self.wCompare.bind('<Button-1>', self.startcompare);

		self.wProgressBar = ttk.Progressbar(
			self, maximum = self.maxProgress, variable = self.progress,
			mode = 'determinate')
		self.wProgressBar.grid(row = 3, column = 0, columnspan = 3, sticky = Stretch, **GridStyle)
		self.wLog = MyLogText(self)
		self.wLog.grid(row = 4, column = 0, columnspan = 3, sticky = Stretch, **GridStyle)

		self.wClearLog = tk.Button(self.OpFrame, text = 'Clear Log 清空日志')
		self.wClearLog.grid(row = 1, column = 5, sticky = Stretch, **GridStyle)
		self.wClearLog.bind('<Button-1>',
			lambda e: self.wLog.delete('1.0', tk.END))

		#self.wLog.tag_add(fgtag(''))
		#self.wLog.tag_add(bgtag(''))
		for k, v in ColorMap.items():
			ft = fgtag(v)
			bt = bgtag(v)
			#self.wLog.tag_add(ft)
			self.wLog.tag_config(ft, foreground = v)
			#self.wLog.tag_add(bt)
			self.wLog.tag_config(bt, background = v)

		centerwindow(self.master)

	def initbypy(self):
		self.byp = ByPy(verbose = 1)

	def selectlocalpath(self, *args):
		self.localPath.set(
			tkFileDialog.askopenfilename(
				title = "Please select a local file " + \
					"(remove the file name later if you " + \
					"want to select a directory)",
				initialdir = self.wLocalPath,
				parent = self))

	def selectremotepath(self, *args):
		remoteList = RemoteListGui(self, self.byp, self.remotePath.get())
		centerwindow(remoteList)
		remoteList.wait_window(remoteList)
		self.remotePath.set(remoteList.result)

	def syncupproc(self, lpath, rpath, delete):
		self.byp.syncup(lpath, rpath, delete)
		self.threadrunning = False

	def startsyncup(self, *args):
		if not self.threadrunning:
			self.threadrunning == True
			threading.Thread(target = self.syncupproc,
				args = (
					self.localPath.get(),
					self.remotePath.get(),
					self.bSyncDelete.get())).start()

	def uploadproc(self, lpath, rpath):
		self.byp.upload(lpath, rpath)
		self.threadrunning = False

	def startupload(self, *args):
		if not self.threadrunning:
			self.threadrunning == True
			threading.Thread(target = self.uploadproc,
				args = (
					self.localPath.get(),
					self.remotePath.get())).start()

	def syncdownproc(self, rpath, lpath, delete):
		self.byp.syncdown(rpath, lpath, delete)
		self.threadrunning = False

	def startsyncdown(self, *args):
		if not self.threadrunning:
			self.threadrunning == True
			threading.Thread(target = self.syncdownproc,
				args = (
					self.remotePath.get(),
					self.localPath.get(),
					self.bSyncDelete.get())).start()

	def downloadproc(self, rpath, lpath):
		if len(rpath) == 0 or rpath[-1] == '/':
			self.byp.downdir(rpath, lpath)
		else:
			self.byp.downfile(rpath, lpath)
		self.threadrunning = False

	def startdownload(self, *args):
		if not self.threadrunning:
			self.threadrunning == True
			threading.Thread(target = self.downloadproc,
				args = (
					self.remotePath.get(),
					self.localPath.get())).start()

	def compareproc(self, rpath, lpath):
		self.byp.compare(rpath, lpath)
		self.threadrunning = False

	def startcompare(self, *args):
		if not self.threadrunning:
			self.threadrunning == True
			threading.Thread(target = self.compareproc,
				args = (
					self.remotePath.get(),
					self.localPath.get())).start()

def main():
	tkRoot = tk.Tk()
	ui = BypyGui(tkRoot)
	ui.mainloop()

if __name__ == '__main__':
	main()

def unused():
	''' just prevent unused warnings '''
	tkMessageBox.showinfo('')

# vim: tabstop=4 noexpandtab shiftwidth=4 softtabstop=4 ff=unix fileencoding=utf-8
