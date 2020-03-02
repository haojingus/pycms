#coding=utf-8
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
from pycket.session import SessionMixin
from error import Error
from common import Common
from acl import ACL
import json

class BaseHandler(tornado.web.RequestHandler,SessionMixin):
	userinfo = {}

	def _checkSession(self):
		#方法API化后的token检查
		if self.get_argument('token','')!='':
			if self._checkToken():
				self.application.curent_user['username'] = 'system'
				return True
			else:
				self.write(json.dumps(Error.CGITOKENERROR))
				return False
		userinfo = self.session.get('userinfo')
		if userinfo is None or userinfo=="":
			self.set_status(302)
			self.set_header('Location','/system/user?action=welcome&code=201')
			self.finish()
			return False 
		else:
			self.userinfo = json.loads(self.session.get('userinfo'))
			self.application.curent_user = self.userinfo
			return True

	def _checkACL(self,mod,action):
		pid = self.get_argument('pid','0')
		tid = self.get_argument('tid','0')
		#print self.session.get('userinfo')
		acl = json.loads(self.session.get('userinfo'))['acl']
		acl_code = self.__get_acl_code(mod,action)
		#print "ACL:",acl,acl_code
		#无ACL的直接跳出
		if acl_code==0:
			return True

		#超级管理员跳出
		pacl = Common.collection_find(acl,lambda s:s['pid']==0)
		if pacl is not None:
			return True

		#项目鉴权
		pacl = Common.collection_find(acl,lambda s:s['pid']==int(pid))
		#print 'PACL',pacl,acl_code
		if pacl is None:
			self.__go_to(Error.ACLERROR)
			return False
		tacl = Common.collection_find(pacl['acl'],lambda s:s['tid']==0)
		if tacl is None:
			tacl = Common.collection_find(pacl['acl'],lambda s:s['tid']==int(tid))
			print('TACL',tid)
			if tacl is None:
				self.__go_to(Error.ACLERROR)
				return False
			else:
				print('TACL:',tacl,acl_code)
				if (tacl['acl']&acl_code)==acl_code:
					return True
				else:
					self.__go_to(Error.ACLERROR)
					return False
		else:
			if (tacl['acl']&acl_code)==acl_code:
				return True
			else:
				self.__go_to(Error.ACLERROR)
				return False

	def _checkToken(self):
		"""only use for inner call
		
		仅用于CMS内部调用鉴定
		"""
		token = self.get_argument('token','')
		if not self.application.cache.exists('guid'):
			self.write(json.dumps(Error.SYSTEMCONFIGMISS))
			return False
		guid = self.application.cache.get('guid')
		print(token,guid)
		if token!=guid:
			self.write(json.dumps(Error.CGITOKENERROR))
			return False
		else:
			return True

	def render_ex(self,template,**kwargv):
		kwargv['userinfo'] = self.userinfo
		self.render(template,**kwargv)


	def __get_acl_code(self,mod,action):
		if mod in ('project','user','plugin') and action in ('add','update'):
			return ACL.SYS_M
		if mod in ('template') and action in ('add','update'):
			return ACL.TEMP_E
		if mod in ('field') and action in ('add','update','list'):
			return ACL.TEMP_D
		if mod in ('document') and action in ('add','update'):
			return ACL.DOC_E
		if mod in ('task','document') and action in ('create','batchpub'):
			return ACL.DOC_P
		if mod in ('document','template','field') and action in ('remove','enable'):
			return ACL.SYS_M
		return 0

	def __go_to(self,err):
		self.set_status(302)
		self.set_header('Location','/system/error?code='+str(err['code'])+'&errmsg='+err['errmsg'])

