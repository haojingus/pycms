#coding=utf-8
import os.path
import sys
import json
import copy
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from datetime import datetime
from dbmanager import DbManager
from common import Common
from error import Error
import hashlib

from modproject import ModProject
from modtemplate import ModTemplate
from modvariable import ModVariable
from modcomponent import ModComponent
from moddocument import ModDocument
from basehandler import BaseHandler
from modfield import ModField
from plugin import Plugin

from tornado.options import define, options
from pycket.session import SessionMixin  

class DemoHandler(BaseHandler):

	def get(self,input):
		""" get route

			处理所有/editor/下的get路由
		"""
		if input=='test1':
			self.test1()
			return
		a = "aa\\nbb"
		self.render('demo.html',a=a.replace('\\','\\\\'))

	def test1(self):
		if not self._checkToken():
			return
		self.write('ok')
		return

