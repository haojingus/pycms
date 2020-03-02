#coding=utf-8
import re
import logging
import json
import copy

from core import Core
from error import Error
from modfield import ModField
from moddocument import ModDocument
from plugins.fieldtype.algorithm import Algorithm

class Plugin(object):

	core = None
	db = None
	app = None

	def __init__(self,webapp):
		self.core = webapp.core
		self.__class__.db = webapp.db 
		self.__class__.app = webapp
		pass

	def compile(self):
		return ''

	def make_field_html(self,pid,tid,fid):
		"""make field html by algorithm
		unused
		生成模板域对应的vue版本html和用户数据js，这里不生成vue_develop_data

		Args:
			pid:项目id
			tid:模板id
			fid:模板域id
			did:文档id
		Returns:
			{'form_html':value,'form_submit':value}
		"""
		_f = ModField(self.app)
		n,data = _f.get_field_list(pid,tid,fid,detail=True)
		if n<1:
			logging.warning('can not find the field')
			return Error.DBEMPTYERR
		#获取模板域信息
		_field_data = data[0]
		_field_data['field_value'] = data[0]['default_value']
		_field_data['algorithm'] = Algorithm.parse_algorithm(data[0]['algorithm'])

		#动态加载插件，处理算法单元，获取数据源
		#version 1.0不要了，1.1升级成vue了
		'''
		_field_cfg = self.core.get_field_detail(_field_data['field_type'])
		_imp_class = _field_cfg['class_name']
		_dynamic_module = getattr(getattr(__import__('plugins.fieldtype.'+_field_cfg['name']),'fieldtype'),_field_cfg['name'].lower())
		_dynamic_class = getattr(_dynamic_module,_field_cfg['class_name'])
		_plugin = _dynamic_class(self.app,_field_data)
		return _plugin.render_plugin()
		'''
		#version 1.1 vue版本
		_field_cfg = self.core.get_field_detail(_field_data['field_type'])
		if _field_cfg is None:
			return {'form_html':u"<h6>不支持的插件类型</h6>",'form_submit':"",'form_js':"",'form_css':""}
		else:
			_input_html = _field_cfg['html'].replace('{$field_id}',str(_field_data['field_id'])).replace('{$field_name}',_field_data['field_name'])
			_input_submit_js = _field_cfg['submit'].replace('{$field_id}',str(_field_data['field_id']))
			_input_js = _field_cfg['js'].replace('{$field_id}',str(_field_data['field_id']))
			return {'form_html':_input_html,'form_submit':_input_submit_js,'form_js':_input_js,'form_css':_field_cfg['css'],'default_value':_field_data['field_value']}

