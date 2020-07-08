# coding=utf-8
import pymysql
import logging
import copy
from error import Error
import time
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class DbManager:
	"""Database access controller.

	数据库访问控制类，内含连接池

	Attributes:
		connectPool:连接池.
		registerDB:连接信息.
	"""
	connectPool = {}
	registerDB = []

	def __init__(self):
		logging.debug('DbManager class inited!')
		self.isLock = False

	@classmethod
	def initConn(cls, config):
		"""initialize database connect.

		初始化配置表中的数据库连接.

		Args:
			config: 配置字典.

		Returns:
			统一的错误状态码Error.*.
		"""
		cls.isLock = False
		if len(config) == 0:
			return Error.APPCONFIGERR

		errorInstance = []
		errorProject = ''
		for dbinfo in config:
			conn = None
			try:
				conn = pymysql.connect(host=dbinfo['host'], user=dbinfo['user'], passwd=dbinfo['passwd'],
									   db=dbinfo['db'], port=dbinfo['port'], charset=dbinfo['charset'])
				logging.debug(dbinfo['host'] + ':' + str(dbinfo['port']) + ' connected!')
			except Exception as e:
				logging.warning("db connect failed!")
				logging.warning(str(e))
				errorInstance.append(dbinfo)
			if conn is not None:
				_dbinfo = copy.deepcopy(dbinfo)
				_dbinfo['conn'] = conn
				cls.registerDB.append(_dbinfo)
				cls.connectPool[str(dbinfo['pid'])] = conn
		print(cls.connectPool)
		if len(errorInstance) == 0:
			return Error.SUCC
		else:
			logging.warning('connect failed.' + errorProject)
			return Error.DBCONNECTERR

	@classmethod
	def closeConn(cls, project=[]):
		"""close database connect.

		关闭指定的数据库连接.参数为空时全部关闭

		Args:
			project: 待处理项目(数据库)的名称list.

		Returns:
			None.
		"""
		pass

		for key in cls.connectPool:
			if len(project) == 0 or (key in project):
				cls.connectPool[key].close()
				logging.info('Project ' + key + ' is closed')

	@classmethod
	def commit(cls, project):
		"""commit database transaction.

		提交数据库事务.

		Args:
			project: 待处理项目(数据库)的pid.

		Returns:
			统一的错误状态码Error.*.
		"""
		if project in cls.connectPool:
			cls.connectPool[project].commit()
			return Error.SUCC
		else:
			logging.warning(project + ' is not in connect pool')
			return Error.DBNOTEXIST

	@classmethod
	def rollback(cls, project):
		"""rollback database transaction.

		回滚数据库事务.

		Args:
			project: 待处理项目(数据库)的pid.

		Returns:
			统一的错误状态码Error.*.
		"""
		pass

		if project in cls.connectPool:
			cls.connectPool[project].rollback()
			return Error.SUCC
		else:
			logging.warning(project + ' is not in connect pool')
			return Error.DBNOTEXIST

	@classmethod
	def reload(cls, userdb):
		"""reload new config

		加载新的配置到连接池

		Args:
		dbinfo:项目连接信息
		Returns:null
		"""
		pass
		_i = 0
		_target_index = -1
		for dbinfo in cls.registerDB:
			if str(dbinfo['pid']) == str(userdb['pid']):
				cls.connectPool[str(userdb['pid'])].close()
				_target_index = _i
			_i = _i + 1
		if _target_index >= 0:
			cls.registerDB.remove(cls.registerDB[_target_index])

		dbinfo = userdb
		try:
			conn = pymysql.connect(host=dbinfo['host'], user=dbinfo['user'], passwd=dbinfo['passwd'], db=dbinfo['db'],
								   port=dbinfo['port'], charset=dbinfo['charset'])
			logging.info('reload db ok! P:' + userdb['project'])
		except Exception as e:
			logging.warning(str(e))
			return False
		cls.registerDB.append(userdb)
		cls.connectPool[str(userdb['pid'])] = conn
		return True

	@classmethod
	def reconnect(cls, project):
		'''reconnect database.

		重新建立数据库连接，并回写入连接池.

		Args:
			project: 待处理项目(数据库)的pid.

		Returns:
			True or False.
		'''
		pass

		project = str(project)
		for dbinfo in cls.registerDB:
			if str(dbinfo['pid']) == project:
				conn = None
				try:
					conn = pymysql.connect(host=dbinfo['host'], user=dbinfo['user'], passwd=dbinfo['passwd'],
										   db=dbinfo['db'], port=dbinfo['port'], charset=dbinfo['charset'])
					logging.warning(dbinfo['host'] + ':' + str(dbinfo['port']) + ' reconnected!')
				except Exception as e:
					logging.warning("db connect failed!" + str(e))
					return False
				cls.connectPool[project] = conn
				return True
		pass
		return False

	@classmethod
	def __execute(cls, project, sql, isquery=True, commit=True):
		"""execute sql for project

		为指定数据库执行sql语句.

		Args:
			project: 待处理项目(数据库)的pid.
			sql: SQL语句.
			isquery: 是否为查询.
			commit: 是否进行事务提交，主要在批处理时要控制此粒度.

		Returns:
			行数,统一的错误状态码Error.*.
		"""
		pass

		project = str(project)
		if project not in cls.connectPool:
			return -1, Error.DBNOTEXIST
		conn = cls.connectPool[project]
		try:
			#logging.info('CONN:'+project+' SQL:'+sql)
			cursor = conn.cursor()
			conn.ping(reconnect=True)
			n = cursor.execute(sql)
		except Exception as e:
			if str(e).find('2006') != -1:
				logging.warning(str(e))
				if cls.reconnect(project) == False:
					cursor.close()
					logging.warning('reconn failed')
					return -1, Error.DBCONNECTERR
				conn = cls.connectPool[project]
				cursor = conn.cursor()
				try:
					n = cursor.execute(sql)
				except Exception as ex:
					cursor.close()
					try:
						cls.rollback(project)
					except Exception as e:
						logging.warning('rollback failed! SQL:' + sql)
						return -1, Error.DBERROR
					logging.warning(str(ex))
					return -1, Error.DBERROR
			else:
				cursor.close()
				logging.warning('Rollback by ' + str(e))
				cls.rollback(project)
				logging.warning("SQL:" + sql)
				recode = copy.deepcopy(Error.DBSQLERR)
				recode['errmsg'] = recode['errmsg'] + str(e)
				return -1, recode
		if isquery:
			data = cursor.fetchall()
		else:
			data = Error.SUCC
		cursor.close()
		if commit:
			cls.commit(project)
		return n, data

	@classmethod
	def executeQuery(cls, project, sql):
		"""execute query sql for project

		为指定数据库执行查询性的sql语句.

		Args:
			project: 待处理项目(数据库)的名称.
			sql: SQL语句.

		Returns:
			行数,统一的错误状态码Error.*.
		"""
		pass
		ret = -1,None
		while True:
			if not cls.isLock:
				cls.isLock = True
				ret = cls.__execute(project, sql, True, True)
				cls.isLock = False
				return ret
			time.sleep(0.1)
		return ret

	@classmethod
	def execute(cls, project, sql, **kwargv):
		"""execute noquery sql for project

		为指定数据库执行改写性的sql语句.

		Args:
			project: 待处理项目(数据库)的名称.
			sql: SQL语句.
			kwargv:
				single: 是否为单sql，默认为否
				commit: 是否进行事务提交，多用于批处理的粒度控制
		Returns:
			行数,统一的错误状态码Error.*.
		"""
		pass
		is_mutiline = False
		if 'mutiline' in kwargv:
			is_mutiline = kwargv['mutiline']
		is_commit = True
		if 'commit' in kwargv:
			is_commit = kwargv['commit']

		if not is_mutiline:
			return cls.__execute(project, sql, False, is_commit)

		sql = sql.replace('\n', '')
		_cmd = sql.split(';')
		n = 0
		data = {}
		for cmd in _cmd:
			cmd = cmd.lstrip().rstrip()
			if cmd != '':
				n, data = cls.__execute(project, cmd, False, is_commit)
				if data['code'] != 0:
					return -1, data
		return n, data
