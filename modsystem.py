#coding=utf-8
import pymysql
import logging
import os
import json
import copy

from error import Error
from common import Common

class ModSystem(object):
	"""CMS system access class

	CMS系统访问类
	"""

	db = None
	core = None
	conf = None

	def __init__(self,webapp):
		"""Init ModField Class
		"""
		self.__class__.db = webapp.db
		self.__class__.core = webapp.core
		self.__class__.conf = webapp.cfg['system']

	def execute_sql(self,pid,sql):
		"""
		run sql

		"""
