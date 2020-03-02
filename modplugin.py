#coding=utf-8
import json
import logging
import os
from error import Error
from common import Common

class ModPlugin(object):

	core = None

	def __init__(self,webapp):
		self.__class__.core = webapp.core
		pass

	def create_plugin(self,kwargv):
		"""create plugin
		创建模板域插件
		
		Argv:
			kwargv:
			name:名称
			cname:中文名
			field_type:模板域类型
			type:I/O类型
			order:排序
		Returns:
		"""
		config = {'name':kwargv['name'],
				'cname':kwargv['cname'],
				'field_type':kwargv['field_type'],
				'type':kwargv['type'],
				'order':kwargv['order']
				}
		path = './plugins/fieldtype/'+config['name'].lower()
		if not os.path.exists(path):
			os.makedirs(path)
		#create config.json
		file_path = path+'/config.json'
		self.__build_file(file_path,json.dumps(config,ensure_ascii=False))
		#create form.html form.js form.css
		for item in ('html','css','js'):
			file_path = path+'/form.'+item
			self.__build_file(file_path,kwargv[item])
		#create from_submit.js
		file_path = path + '/form_submit.js'
		self.__build_file(file_path,kwargv['form_submit'])
		#create test data
		file_path = path + '/developer.test'
		self.__build_file(file_path,kwargv['debug_input'])
		file_path = path + '/user.test'
		self.__build_file(file_path,kwargv['debug_value'])
		return Error.SUCC


	def get_test_data(self,field_type):
		detail = self.core.get_field_detail(field_type)
		if detail is None:
			return Error.PLUGINERR
		path = './plugins/fieldtype/'+detail['name'].lower()
		print(path)
		dev = Common.get_file_content(path+'/developer.test',default='')
		usr = Common.get_file_content(path+'/user.test',default='')
		print('[USER]',usr+'@')
		return dev,usr

	def __build_file(self,path,content):
		"""
		build file for content

		Args:
			path:路径
			content:文件内容
		Returns:
		"""
		fp = open(path,'w')
		fp.write(content)
		fp.close()
		return
