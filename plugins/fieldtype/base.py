#coding=utf-8
import re
import logging
import json
import copy
import sys,os

from abc import ABCMeta, abstractmethod
from algorithm import Algorithm


class PluginBase(object):

	__metaclass__ = ABCMeta
	_app = None
	_field_info = {}
	_field_data = {}
	
	def __init__(self,webapp,field_data):
		self._app = webapp
		self._field_info = webapp.core.get_field_detail(field_data['field_type'])
		self._field_data = field_data
		pass

	def _complie_data(self):
		"""compile input data
		编译运行输入数据

		Args:
		Returns:dict	
		"""
		_input_algorithm = self._field_data['algorithm']['input']
		_algorithm = Algorithm()
		#执行input算法获取field模板渲染的数据源.会校验时间戳，决定是否通过缓存执行
		_input_data_source = _algorithm.execute_algorithm(_input_algorithm['data'],_input_algorithm['lang'])
		#logging.info(_input_data_source)
		#执行结果转为py的dict
		#_input_data_result = self.__format_plugin_source(_field_type,_input_data_source)
		
		#field数据注入到input_data_source和submit js
		_input_html_source = self._field_info['form_html'].replace('{$field_id}',str(self._field_data['field_id'])).replace('{$field_name}',self._field_data['field_name']).replace('{$field_value}',self._field_data['field_value'])
		_input_submit_js = self._field_info['form_submit'].replace('{$field_id}',str(self._field_data['field_id']))
		_input_html_target = _input_html_source
		return {'data_source':_input_data_source,'html_source':_input_html_source,'submit_js':_input_submit_js,'css':self._field_info['form_css'],'js':self._field_info['form_js']}
	


	def _template_iterator(self,**param):
		"""iterator command parser

		迭代器解析
		Args:
			param:
				html:模板
				name:迭代集合名称
				data:绑定的数据集 需要[{'key1':value1,'key2':value2,....}]的格式
		"""
		if not ('html' in param and 'name' in param and 'data' in param):
			return param['html']
		pattern = re.compile(r'(.*)(\{#\w+:'+param['name']+r'\})(.*)(\{#end\})(.*)')
		m = pattern.match(param['html'])
		if m is None:
			return param['html']
		_match = m.groups()
		if len(_match)==5:
			_html = copy.deepcopy(_match[0])
			for item in param['data']:
				_block = copy.deepcopy(_match[2])
				for (k,v) in item.items():
					_block = _block.replace('{#'+k+'}',str(v))
				_html = _html + _block
			_html = _html + _match[4]
			return _html
		else:
			return param['html']

	def _template_param(self,**param):
		"""param command parser

		解析参i数.用value1替换key1
		Args:
			html:模板
			params:参数列表 格式：{'key1':value1,'key2':value2}
		Returns:
			string
		"""
		print(param)
		if not ('html' in param and 'params' in param):
			return ''
		html = param['html']
		for k, v in param['params'].items():
			html = html.replace('{#param:'+k+'}', v)
		return html


	@abstractmethod
	def render_plugin(self):
		"""render plugin data for form html/js/css

		渲染插件的html css js
		Args:
			input_data:输入数据源 json

		Returns:
			string
		"""
		pass
