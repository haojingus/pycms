#coding=utf-8
import pymysql
import logging
import os
import json
import copy

from error import Error
from common import Common

class ModVariable(object):
	"""CMS template variable access class

	执行项目的变量管理
	"""

	db = None
	core = ""

	def __init__(self,webapp):
		"""Init ModVariable Class
		"""
		self.__class__.db = webapp.db


	def update(self,action,pid,**variable):
		"""Add/Update project variable

		添加/修改一个变量

		Args:
			action:add/update
			pid:项目id
			variable:
				scope :作用域GLOBAL/TEMPLATE
				variable_name:变量名称
				variable_type:变量类型
				variable_value:变量值
				enable:是否启用 True/False
		Returns:
			Error json
		"""
		pass

		pid = str(pid)
		if not ('variable_name' in variable and 'variable_value' in variable):
			return Error.MODPARAMERR
		expression = "`project_id`="+pid+",`variable_name`='"+variable['variable_name']+"',`variable_value`='"+variable['variable_value']+"'"
		_enable = '1' if 'enable' not in variable else str(variable['enable'])
		_scope = 'GLOBAL' if 'scope' not in variable else variable['scope']
		_variable_type = 'system:string' if 'variable_type' not in variable else variable['variable_scope']
		expression = expression + ",`enable`="+_enable+",`scope`='"+_scope+"',`variable_type`='"+_variable_type+"'"
		if action == 'update':
			if 'variable_id' not in variable:
				return Error.MODPARAMERR
			sql = "update `cms_variable` set "+expression+" where variable_id="+variable['variable_id']
		else:
			sql = "insert into `cms_variable` set "+expression
		n,data = self.db.execute(pid,sql)
		#错误检查
		if data['code']!=0:
			return data
		#更新记录到此就结束了
		if action == 'update':
			return data

		#获取新插入的记录的id
		sql = "select variable_id from `cms_variable` where project_id='"+pid+"' and `variable_name`='"+variable['variable_name']+"' order by variable_id desc limit 1"
		n, data = self.db.executeQuery(pid,sql)
		if n < 1:
			return data
		_variable_id = data[0][0]
		logging.info(str(data))
		#修改模板表cms_tbl_{$tid}字段
		if data['code']!=0:
			return data
		recode = copy.deepcopy(data)
		recode['variable_id'] = _variable_id
		return data


	def get_variable_list(cls,pid,strfilter='',order='variable_id asc'):
		"""get template list by case,support page

		获取变量列表(或单个变量)，不支持分页

		Args:
			pid:项目id
			strfilter:查找条件
			order:排序规则

		Returns:
			List
		"""
		pass

		pid=str(pid)
		strfilter = '1' if strfilter =='' else strfilter
		sql = "select `variable_id`,`variable_name`,`scope`,`variable_type`,`variable_value`,`enable` from `cms_variable` where "+strfilter+' order by '+order
		n,data = cls.db.executeQuery(pid,sql)
		return n,data


