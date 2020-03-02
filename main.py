#!/usr/local/bin/python3
#coding=utf-8
import os
import os.path
import sys
import json
import time
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import redis
import subprocess
import logging
import importlib

from datetime import datetime
from dbmanager import DbManager
from common import Common
from core import Core
from thirdparty import ThirdParty
from schema import Schema

from indexhandler import IndexHandler
from adminhandler import AdminHandler
from editorhandler import EditorHandler
from systemhandler import SystemHandler
from demohandler import DemoHandler
from apihandler import ApiHandler
from tornado.options import define, options
from pycket.session import SessionMixin

from modulemenu import MenuModule

define("port", default=8080, help="run on the given port", type=int)
define('debug', default=False, help='Set debug mode', type=bool)
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S')

# importlib.reload(sys)
#reload(sys)
#sys.setdefaultencoding('utf-8') 

class Application(tornado.web.Application):
	def __init__(self):
		self.version = "1.8.0"
		self.guid = Common.md5(str(int(round(time.time()*1000)))+str(os.getpid()))
		self.cfg = Common.loadConfig()
		self.core_pid = self.cfg['system']['pid']
		self.core = Core()
		self.core.set_env('root',os.path.split(os.path.realpath(__file__))[0])
		self.thirdparty = ThirdParty()
		self.thirdparty.load_all()
		self.curent_user = {}
		handlers = [
			(r"/", IndexHandler),
			(r"/admin/(\w+)", AdminHandler),
			(r"/editor/(\w+)",EditorHandler),
			(r"/demo/(\w*)",DemoHandler),
			(r"/system/(\w+)",SystemHandler),
			(r"/api/(.*)",ApiHandler)
		    ]
	 
		settings = dict(
			app_title=u"CMS",
			template_path=os.path.join(sys.path[0], "templates"),
			static_path=os.path.join(sys.path[0], "static"),
		    upload_path=os.path.join(sys.path[0], "upload"),
		    cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
			xsrf_cookies=False,
		    autoescape=None,
			pycket={
				'engine':'redis',
				'storage':{
				'host':self.cfg['redis']['host'],
				'port':self.cfg['redis']['port'],
				'db_sessions':10,
				'db_notifications':11,
				'max_connections':2**31,
				},
			},
			cookies={
				'expires_days':2,
			},
			ui_modules={'Menu':MenuModule}
		    )

		tornado.web.Application.__init__(self, handlers, **settings)
		print(str(datetime.now()),'init db')
		# Have one global connection to the blog DB across all handlers
		self.db = DbManager()
		self.db.initConn(self.cfg['db'])
		self.cache = redis.Redis(connection_pool = redis.ConnectionPool(host=self.cfg['redis']['host'],port=self.cfg['redis']['port'],db=1))
		self.cacheExpired = 3600
		print(str(datetime.now()),'build cache')
		#build system cache
		project_cfg = []
		for item in self.cfg['db']:
			if item['pid']!=0:
				project_cfg.append({'pid':item['pid'],'project':item['project'],'domain':item['domain']})
		self.cache.set('project_config',json.dumps(project_cfg,ensure_ascii=False))
		self.cache.set('lang',json.dumps(self.core.language_config))
		self.cache.set('system_fields',json.dumps(self.cfg['default_template_field'],ensure_ascii=False))
		#用于内部API调用的token
		self.cache.set('guid',self.guid)
		self.schema = Schema(self)
		self.schema.load_schema()
		#logging.info(str(self.cfg))
		#print self.cfg['db']
		#print self.cfg['fulltext']

def f10s():
	global app
	if 'onTimer' not in app.schema.schema_config:
		logging.warning('Schema config missed!')
		return
	for _timer_setting in app.schema.schema_config['onTimer']:
		#for _event_ontimer in proj['onTimer']:
		last_time = _timer_setting['last_call']
		print('EVENT_TIMER',last_time,_timer_setting['setting'])
		if Schema.check_timer(last_time,datetime.now(),_timer_setting['setting']):
			for _callback in _timer_setting['callback']:
				_func = Schema.func_parse(_callback['action'])
				token = app.cache.get('guid')
				print('python cli.py '+token+' '+_func['func_name']+' '+_func['params']+' '+Schema.env_encode(_callback['env'])+'>>schema.log')
				subprocess.Popen(['python cli.py '+token+' '+_func['func_name']+' '+_func['params']+' '+Schema.env_encode(_callback['env']) +'>>schema.log'],shell=True)
				print('CALLBACK OK!',_callback)
			_timer_setting['last_call'] = datetime.now()
	#print app.schema.schema_config
	pass

def main():
	tornado.options.parse_command_line()
	global app 
	app = Application()
	http_server = tornado.httpserver.HTTPServer(app)
	# http_server.listen(options.port)
	http_server.bind(options.port)
	http_server.start(2)
	_schema = Schema(app)
	tornado.ioloop.PeriodicCallback(f10s, 5000).start()
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	app = None
	main()

