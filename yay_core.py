# Copyright (c) 2009 John (Jack) Angers, jacktasia@gmail.com
# Licensed under the terms of the MIT License (see LICENSE.txt)

import sys
import java.awt as awt
import javax.swing as swing
import java.lang as lang
import java.lang.System as System
import java.io.File as File

import threading
import dircache
import os
import pickle
import math

import logger
LOG = logger.yay_logger()

# used in reloadTime filter so only image files are "seen"/counted
def img_only(f):
	exts = ['png','jpg','gif','jpeg','bmp']
	e = f.split('.')
	ext = e[len(e)-1].lower()
	if ext in exts:
		return True

class YayCore(threading.Thread):
	def start_config(self):
		os_name =  System.getProperty('os.name')
		self.os_sep = File.separator	
		self.has_dir = True
		self.ticks = 30 #default
		self.first_start = False
		self.has_started = False
		app_name = 'Yay'
		filename = 'config.pkl'
		LOG.debug('Operating System: %s.' % os_name)
		if os_name.find('Windows') != -1:
		    self.config_dir = os.environ["APPDATA"] + self.os_sep + app_name + self.os_sep
		    self.os = 'win'
		else:
		    self.config_dir = os.path.expanduser("~") + self.os_sep + '.' + app_name + self.os_sep
		    self.os = 'other'
		self.config_path = self.config_dir + filename #'server_config.ini'
		self.dir = ''
		if not os.path.exists(self.config_dir):
			self.first_start = True
			os.makedirs(self.config_dir)
			self.has_dir = False
			self.create_config_file()
		else:
			try:
				f = open(self.config_path,'rb')
			except IOError:
				LOG.debug('Config file doesn\'t exist, creating it.')
				self.first_start = True
				self.create_config_file()
	
		self.dir = self.get_config('browse_folder')
		self.ticks = self.get_config('speed')
		
		if self.dir == '':
			## this should be a dialog alert...
			LOG.debug('Exitting program.')
			#sys.exit()
			System.exit(0)
		else:
			LOG.debug('Image folder: %s.' % self.dir)


		self._stopevent = threading.Event()
		self._sleepperiod = 1.0
		
		threading.Thread.__init__(self,name='GoGo')
		self.file_count = 0;
		self.countsec = 0
		self.is_paused = True
		self.loadup()		
		self.last_off()
		self.updateLabel()

	def create_config_file(self):
		self.set_dir()
		self.set_speed(self.ticks)

	def get_has_dir(self):
		return self.has_dir

	## need like a set_config...so we can have like config['pause_time']
	def set_dir(self):
		dir = self.getDirectory()
		self.set_config('browse_folder',dir)
		self.has_dir = True
		old_dir = self.dir
		self.dir = dir 
		self.loadup()
		if dir != old_dir:
			self.do_change()

	def set_speed(self,s):
		self.set_config('speed',s)
		self.ticks = s
		self.updateLabel()

	def set_config(self,n,v):
		if not self.first_start:
			config = self.get_config()			
		else:
			config = {}
			self.first_start = False
		config[n] = v
		output = open(self.config_path,'wb')
		pickle.dump(config,output)
		output.close()

	def get_config(self,n=None):
		f = open(self.config_path,'rb')
		config = pickle.load(f)
		f.close()
		if n is not None:
			return config[n]
		else:
			return config
	
	def get_dir(self):
		return self.get_config('browse_folder')

	def set_ticks(self,ticks):
		self.ticks = ticks

	def goto_img(self,i):
		if i >= 0 and i < self.workingdir_size + 1:
			self.file_count = i - 1
			self.do_change()
			
	def prune(self):
		was_playing = False
		if not self.is_paused:
			self.do_pause()
			was_playing = True
			
		if not os.path.exists(self.dir + '_pruned'):
			os.makedirs(self.dir + '_pruned')
		os.rename(self.dir + self.workingdir[self.file_count],
				  self.dir + '_pruned/' +  self.workingdir[self.file_count])
		self.reloadTime()
		if was_playing:
			self.do_start()
		self.do_change()
		  

	def last_off(self):
		#this finds out the current desktop and if is the current selected folder...
		cur_path = os.popen("gconftool-2 --get /desktop/gnome/background/picture_filename").read().strip()
		count = 0;
		found = -1
		b = cur_path.split('/')
		cur_path = b[len(b)-1]
		for a in self.workingdir:
			if a == cur_path:
				found = count
				break
			count += 1
		if found == -1:
			found = 0
		self.file_count = found
		self.do_change()

	def doStart(self):
		if not self.has_started:
			self.has_started = True
			self.start()
		self.do_change()
		
	def pause(self):
		if not self.is_paused:
			self.is_paused = True
		else:
			self.is_paused = False

	def run(self):
		while not self._stopevent.isSet():
			self.countsec +=1
			self.updateTicker()
			if self.countsec > self.ticks and not self.is_paused:
				self.next()
				self.countsec = 0
			elif self.is_paused:
				self.countsec = 0
			self._stopevent.wait(self._sleepperiod)
		
	def loadup(self):
		self.file_count = 0
		self.reloadTime()

	def reloadTime(self):
		try:
			self.workingdir = filter(img_only,dircache.listdir(self.dir))
			self.workingdir_size = len(self.workingdir)
		except OSError:
			self.showDialogError("Path doesn't seem to exist. Unattached Network or External Drive? Pick one")
			self.set_dir()
			return
			
		msg = "Selected image directory has no images! Please pick again."
		if self.workingdir_size == 0:
			self.showDialogError(msg)
			self.set_dir()
		self.updateLabel()

	def last(self):
		if self.file_count-1 >= 0:
			self.file_count -= 1
		else:
			self.file_count = self.workingdir_size -1
		self.do_change()
			
	def do_change(self):
		self.updateLabel()
		self.countsec = 0
		## TODO do the check in __init__ and then import correct change_desktop
		if self.os == 'win':
			import yay_windows
			yay_windows.change_desktop(self.dir + self.workingdir[self.file_count])
		else:
			import yay_gnome
			yay_gnome.change_desktop(self.dir + self.workingdir[self.file_count])
		LOG.debug('Setting next background image: %s.' % self.workingdir[self.file_count])
		

	def next(self):
		if self.file_count+1 < self.workingdir_size:
			self.file_count += 1
		else:
			self.loadup()
		self.do_change()
	
	def updateLabel(self):
		b = str(self.dir).split(self.os_sep)
		r = b[len(b)-2]
		self.lblDirectory.setText(r + "  ")
		m = str(self.file_count+1) + "/" + str(self.workingdir_size)
		self.lblStatus.setText(m)
		self.lblCurrent.setText(self.workingdir[self.file_count] + "  ")

	def updateTicker(self):
		self.countMenu.setText(str((self.ticks - self.countsec)+1))
		self.countMenu.updateUI()
		
	def join(self,timeout=None):
		LOG.debug('Hrm.')
