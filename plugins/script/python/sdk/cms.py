import sys
import os

class CmsSDK:
	
	conf = None
	taskid = ''

	def __init__(self):
		filepath,tmp = os.path.split(os.path.realpath(__file__))
		if filepath.find('plugins')<0:
			print 'error',filepath
			exit(1)
		print filepath
		filepath = filepath[:filepath.find('plugins')]+'conf/config.json'
		fp=open(filepath,'r')
		self.__class__.conf = fp.read()
		fp.close()
		print self.conf
	
	def get_data_result(self):
		return {'code':1} 
