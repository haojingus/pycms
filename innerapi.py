#coding=utf-8
import requests
import copy
import logging
from error import Error
from schema import Schema
from common import Common

class InnerAPI(object):

	token = ''
	host = '127.0.0.1'
	port = 8080
	prefix_url = ''

	def __init__(self,token):
		self.__class__.token = token
		self.__class__.prefix_url = 'http://'+self.host+('' if self.port==80 else ':'+str(self.port))
		self.__class__._env = {}

	def set_env(self,env):
		self._env = Schema.env_decode(env)
		logging.info("ENV:"+str(self._env))

	def publish_local(self,*params):
		print('run publish')
		if ('pid' not in self._env) or ('tid' not in self._env):
			logging.warning('ENV variable missed')
			return
		pid = 0
		tid = 0
		try:			
			pid = int(self._env['pid'])
			tid = int(self._env['tid'])
		except Exception as e:
			logging.warning('ENV variable type error')
			return

		url = self.prefix_url+'/admin/task?action=create'
		#print params
		did_set = ','.join(list(params))
		r = requests.post(self.prefix_url+'/admin/task?action=batchpub', data={'token':self.token,'type':'script','pid':pid,'tid':tid,'did_set':did_set,'preview':'N'})
		logging.info('System Callback:'+str(r.text))
		return


	def query(self,pid,sql):
		r = requests.post(self.prefix_url+'/api/sql?action=query',data={'token':self.token,'pid':pid,'sql':sql})
		return r.text

	


