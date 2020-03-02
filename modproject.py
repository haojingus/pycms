#coding=utf-8
import pymysql
import logging
import os
import json
import copy

from error import Error
from common import Common
class ModProject(object):
	"""Project Database access class

	执行项目(站点)的增删改查等数据操作
	"""

	db = None
	core_pid = ""
	conf = None
	def __init__(self,webapp):
		"""Init ModProject Class
		"""
		self.__class__.db = webapp.db
		self.__class__.core_pid = webapp.core_pid
		self.__class__.conf = webapp.cfg['system']


	def add(self,**project):
		"""Add project(site)

		添加一个站点

		Args:
			project:
			project_name:项目名称
			domain:域名
			rsync_uri:rsync地址 rsync://username:password@ip:port/resource
			mysql_uri:db连接信息，默认为空，mysql://username:password@ip:port/dbname
			cdn_api:CDN服务商的同步API 格式为：http://url
			enable:是否启用 True/False
		Returns:
			Error json
		"""
		pass
		#入cmscore库
		if not ('project_name' in project and 'domain' in project and 'rsync_uri' in project):
			return Error.MODPARAMERR
		expression = "`project_name`='"+project['project_name']+"',`domain`='"+project['domain']+"',`rsync_uri`='"+project['rsync_uri']+"'"
		_mysql = '' if 'mysql_uri' not in project else project['mysql_uri']
		_cdn = '' if 'cdn_api' not in project else project['cdn_api']
		_enable = '1' if 'enable' not in project else str(project['enable'])
		expression = expression + ",`mysql_uri`='"+_cdn+"',`enable`="+_enable
		sql = "insert into `cms_project` set "+expression
		logging.info('Project SQL:'+sql)
		n,data = self.db.execute(self.core_pid,sql)
		#获取project信息
		if data['code']!=0:
			logging.warning(str(data))
			return data
		sql = "select project_id from cms_project where project_name='"+project['project_name']+"' order by project_id desc limit 1"
		n,data = self.db.executeQuery(self.core_pid,sql)
		if n<1:
			return data
		_project_id = data[0][0]
		logging.info(str(data))
		#创建项目数据库
		_dbname = 'cms_site_'+str(_project_id)
		sql = Common.loadSql('project_create.sql')
		sql = sql.replace('{$database}',_dbname)
		n,data = self.db.execute(self.core_pid,sql,mutiline=True)
		if data['code'] != 0:
			return data
		#生成user config文件
		_dbinfo = self.__build_project_config(_project_id,project['project_name'],project['domain'])
		#初始化项目库
		self.db.reload(_dbinfo)
		sql = Common.loadSql('init_project.sql')
		n,data = self.db.execute(str(_project_id),sql,mutiline=True)
		recode = copy.deepcopy(data)
		recode['pid'] = _project_id
		return recode

	def update(self,**project):
		"""update project info

		修改项目(站点)信息
		Arges:
			project:
			project_name:项目名称
			domain:域名
			rsync_uri:rsync地址 rsync://username:password@ip:port/resource
			mysql_uri:db连接信息，默认为空，mysql://username:password@ip:port/dbname
			cdn_api:CDN服务商的同步API 格式为：http://url
			enable:是否启用 True/False
		Returns:
			Error json
		"""
		pass

		if 'project_id' not in project:
			return Error.MODPARAMERR
		expression = ''
		if 'project_name' in project:
			expression = expression + ",project_name='"+project['project_name']+"'"
		if 'domain' in project:
			expression = expression + ",`domain`='"+project['domain']+"'"
		if 'rsync_uri' in project:
			expression = expression + ",`rsync_uri`='"+project['rsync_uri']+"'"
		if 'mysql_uri' in project:
			expression = expression + ",`mysql_uri`='"+project['mysql_uri']+"'"
		if 'cdn_api' in project:
			expression = expression + ",`cdn_api`='"+project['cdn_api']+"'"
		if 'enable' in project:
			expression = expression + ",`enable`="+project['enable']
		if expression=='':
			return Error.MODPARAMERR
		if expression[0]==',':
			expression = expression[1:]
		sql = "update `cms_project` set "+expression+" where `project_id`="+str(project['project_id'])
		n,data = self.db.execute(self.core_pid,sql)
		return data




	def __build_project_config(self,pid,name,domain):
		"""build a user config file for project(site)

		创建项目的数据库配置文件，保存连接信息

		Args:
			pid:项目id
			name:项目名称
		Returns:
			Boolean
		"""
		pass

		conf = []
		_path = './conf/userdb.json'
		content = ''
		if os.path.exists(_path):
			fp = open(_path,'r+')
			content = fp.read()
		else:
			fp = open(_path,'w')
		if content!='':
			conf = json.loads(content)
		_usercfg = copy.deepcopy(self.conf)
		_usercfg['conn'] = 0
		_usercfg['project'] = name
		_usercfg['db'] = 'cms_site_'+str(pid)
		_usercfg['pid'] = pid
		_usercfg['domain'] = domain
		conf.append(_usercfg)
		print("CONF:",conf)
		fp.seek(0,0)
		fp.write(json.dumps(conf))
		fp.close()
		return _usercfg
