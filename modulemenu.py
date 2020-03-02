#coding=utf-8
import tornado.web
import os
import json

class MenuModule(tornado.web.UIModule):
	def render(self,userinfo):
		return self.render_string('module/admin_menu.html',projects=self.__load_projects(),userinfo=userinfo)

	def __load_projects(self):
		_cfg_file = './conf/userdb.json'
		if os.path.exists(_cfg_file)==False:
			return []
		else:
			fp = open(_cfg_file,'r')
			_db = json.load(fp)
			_projects = []
			for item in _db:
				_projects.append({'pid':item['pid'],'name':item['project']})
			return _projects

