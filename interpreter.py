# coding=utf-8
import os
import sys
import time
import copy
import json
import redis
import pymysql
import re
import logging
import importlib

importlib.reload(sys)

from common import Common
from error import Error
from plugins.fieldtype.algorithm import Algorithm


class Interpreter(object):
	share_memory = None
	db = None
	lang_cfg = None
	algorithm = None
	pid = 0
	tid = 0
	is_debug = False
	start_run = 0

	def __init__(self, webapp):
		self.__class__.share_memory = webapp.cache
		self.__class__.db = webapp.db
		self.__class__.lang_cfg = webapp.core.language_config

	# self.__class__.debug = False

	def __get_curent_time(self):
		return int(round(time.time() * 1000))

	def __debug_performance(self):
		if self.is_debug:
			print('Elapsed:' + str(self.__get_curent_time() - self.start_run) + " ms")

	def load_code(self, code):
		"""load source code

		装载源代码
		Args:code
		Returns:dict
		"""
		self.start_run = self.__get_curent_time()
		self.__class__.algorithm = Algorithm.parse_algorithm(code.replace('\r\n', '\n'))
		self.__debug_performance()

	def make_data(self):
		"""make sql result set

		生成导入数据

		Args:
		Returns:
		"""
		# 不做None值检查
		_result = {'input': {}, 'script': {}}
		for _type in ('input', 'script'):
			for _sql in self.algorithm['sql'][_type]:
				# 解析script内的sql，构建用户数据源
				self.__debug_performance()
				_field_sql = self.sql_convert(_sql['sql'])
				# 执行sql
				self.__debug_performance()
				n, _data = self.db.executeQuery(self.pid, _field_sql)
				self.__debug_performance()
				self.cms_assert(n < 0, 5001, 'cms sql execute failed! C-SQL:' + _field_sql)
				# 合并sql结果集
				_result[_type][_sql['variable']] = _data
			_result[_type]['$pid'] = self.pid
			_result[_type]['$tid'] = self.tid
			_result[_type]['$did'] = 0
			_result[_type]['$type'] = _type
			_result[_type]['$debug'] = u'单插件调试不支持跨插件debug数据注入'
		return _result

	def render(self, algorithm_type, **kwargv):
		"""
		rend field by algorithm

		"""

		logging.info('[Compiler]:this is debug')
		fid = kwargv['fid']
		data_key = kwargv['data_key']
		# 用户录入值/测试输入值
		if 'field_value' in kwargv:
			field_value = kwargv['field_value']
		else:
			field_value = ''

		algorithm_type = 'script' if algorithm_type == 'script' else 'input'
		logging.info('[Compiler]:start render')
		# print "Source Code:",field_algorithm
		# print "ALGORITHM:",_algorithm
		_lang_cfg = Common.collection_find(self.lang_cfg, lambda s: s['lang'] == self.algorithm[algorithm_type]['lang'])
		self.cms_assert((_lang_cfg is None and self.algorithm[algorithm_type]['lang'] != 'raw'), 500,
						'not support ' + self.algorithm[algorithm_type]['lang'])

		print('step-1', _lang_cfg)
		if self.algorithm[algorithm_type]['lang'] == 'raw':
			# 判断算法类型，input则只读取raw配套的data，script则需要优先使用raw，如raw配套为空，则使用用户数据field_value
			if self.algorithm[algorithm_type]['data'].strip() != '':
				print('direct raw')
				return self.algorithm[algorithm_type]['data']
			elif algorithm_type == 'script':
				print('script mode null raw replaced by user data')
				return field_value
			else:
				print('input mode null raw convert to "" ')
				return ''
		print('step-2')
		root = os.path.split(os.path.realpath(__file__))[0]
		cmd = _lang_cfg['cfg']['run'].replace('{$root}', root)
		cmd = cmd.replace('%1', data_key)
		# 构建算法文件input类型前缀为developer_ script类型前缀为user_
		# prefix = 'user_' if algorithm_type=='script' else 'devloper_'
		prefix = algorithm_type + '_'
		path = root + '/plugins/script/' + _lang_cfg['lang'] + '/usr/' + prefix + str(self.pid) + '_' + str(
			self.tid) + '_' + str(fid) + '.' + _lang_cfg['cfg']['extname']
		logging.info("Script:" + path)
		algo = Algorithm()
		_ready = False
		if os.path.exists(path):
			fp = open(path, 'r')
			_code = fp.read()
			fp.close()
			target_hash = Common.md5(_code)
			source_hash = Common.md5(self.algorithm[algorithm_type]['data'])
			if target_hash == source_hash:
				_ready = True
		# return algo.execute(cmd)
		if not _ready:
			fp = open(path, 'w')
			fp.write(self.algorithm[algorithm_type]['data'])
			fp.close()
			_ready = True
		logging.info('[Compiler-Debug]:end render')
		self.__debug_performance()
		logging.info('[Compiler-Debug]:CMD:' + cmd)
		render_data = algo.execute(cmd)
		self.__debug_performance()
		logging.info('[Compiler]:' + str(render_data))
		self.cms_assert(render_data == 'algorithm time out', 500, 'algorith time out!!!')
		# 分析处理渲染结果
		# 错误处理
		_p = re.compile(r"\[CMSERRKEY=.*?\]")
		_errkey = _p.findall(render_data)
		if len(_errkey) >= 1:
			_errkey = _errkey[0].replace('[CMSERRKEY=', '').replace(']', '')
			_errdata = str(self.share_memory.get(_errkey),encoding='utf-8')
			_script_errinfo = json.loads(_errdata)
			self.cms_assert(_script_errinfo['errcode'] == Error.ALGORITHMABORT['code'], 500,
							Error.ALGORITHMABORT['errmsg'] + " Detail:" + _script_errinfo['errmsg'])

		# 结果分析
		_p = re.compile(r"\[CMSDATAKEY=.*?\]")
		_key = _p.findall(render_data)
		if len(_key) == 1:
			return str(self.share_memory.get(_key[0].replace('[CMSDATAKEY=', '').replace(']', '')),encoding='utf-8')
		else:
			return render_data

	def sql_convert(self, cms_sql):
		# 加载系统模板域
		self.cms_assert(not self.share_memory.exists('system_fields'), 5002, 'system config can not find!!!')
		system_fields = json.loads(self.share_memory.get('system_fields'))
		pattern = re.compile(r"\{#[^}]*\}")
		m = pattern.findall(cms_sql)
		self.cms_assert(len(m) == 0, 500, 'sql error,sql:' + cms_sql)
		tbl = m[0]
		tbl = tbl[2:len(tbl) - 1]
		self.cms_assert(len(tbl) == 0, 500, 'tblname is empty')
		# 开始获取模板id
		pattern = re.compile(r"cms_tbl_\d+")
		if len(pattern.findall(tbl)) == 0:
			logging.info("TBL:" + tbl)
			_sql = "select template_id,template_name from cms_template where template_name='" + tbl + "'"
			n, data = self.db.executeQuery(self.pid, _sql)
			self.cms_assert(n < 1, 500, "can't find template.tname:" + tbl)
			cms_sql = cms_sql.replace('{#' + tbl + '}', 'cms_tbl_' + str(data[0][0]))
			tbl = 'cms_tbl_' + str(data[0][0])
		else:
			cms_sql = cms_sql.replace('{#' + tbl + '}', tbl)
		pass
		cms_sql_tid = filter(str.isdigit, tbl)
		_sql = 'select field_id,field_name from cms_template_field where template_id=' + cms_sql_tid
		n, data = self.db.executeQuery(self.pid, _sql)
		self.cms_assert(n < 1, 500, 'can not find field info')
		# 开始替换用户字段
		for cms_sql_field in data:
			cms_sql = cms_sql.replace('{$' + cms_sql_field[1] + '}', 'sp_' + str(cms_sql_field[0]))
		logging.info('[C-SQL]:' + cms_sql)
		# 开始替换系统字段
		for cms_sql_field in system_fields:
			_real_field = cms_sql_field['name'].replace('{$', '').replace('}', '')
			cms_sql = cms_sql.replace(cms_sql_field['name'], _real_field).replace(cms_sql_field['cname'], _real_field)
		return cms_sql

	def cms_assert(self, boolexp, code, msg):
		if boolexp:
			print('cms assert', msg)
			raise Exception(msg, code)
		return

	def debug(self, pid, tid, code, debug_data):
		self.__class__.pid = pid
		self.__class__.tid = tid
		self.load_code(code)
		fid = str(int(round(time.time() * 1000))) + '_debug'
		# try:
		sql_result = self.make_data()
		input_key = '_'.join(['input', str(pid), str(tid), fid])
		script_key = input_key.replace('input', 'script')
		sql_result['input']['$fid'] = fid
		sql_result['input']['$input'] = ''
		# cmsapp的入口参数注入环境信息
		self.share_memory.setex(input_key, 60, json.dumps(sql_result['input'], ensure_ascii=False))
		_input = self.render('input', data_key=input_key, fid=fid)

		sql_result['script']['$fid'] = fid
		sql_result['script']['$input'] = debug_data
		self.share_memory.setex(script_key, 60, json.dumps(sql_result['script'], ensure_ascii=False))
		_script = self.render('script', field_value=debug_data, data_key=script_key, fid=fid)
		return _input, _script

