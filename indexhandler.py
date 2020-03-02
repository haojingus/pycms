#coding=utf-8
import os.path
import sys
import json
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from datetime import datetime
from dbmanager import DbManager
from common import Common
import hashlib

from tornado.options import define, options
from pycket.session import SessionMixin  
from basehandler import BaseHandler

class IndexHandler(BaseHandler):


	def get(self):
		if self._checkSession():
			self.render('index.html',userinfo=self.userinfo)



