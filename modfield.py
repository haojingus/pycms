#coding=utf-8
import pymysql
import logging
import os
import json
import copy

from error import Error
from common import Common

class ModField(object):
	"""CMS template field access class

	执行模板域的底层管理类
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


	def update(self,action,pid,**field):
		"""Add/Update template field

		添加/修改一个模板域

		Args:
			action:add/update
			pid:项目id
			field:
				template_id:模板id
				field_name:项目名称
				rule:过滤规则(javascript正则)
				algorithm:json 算法模板


				enable:是否启用 True/False
		Returns:
			Error json
		"""
		pass
		pid = str(pid)
		if not ('template_id' in field and 'field_name' in field and 'field_type' in field):
			return Error.MODPARAMERR
		#校验field type合法性
		if not self.core.field_type_existed(field['field_type']):
			return Error.MODPARAMERR
		expression = "`template_id`='"+str(field['template_id'])+"',`field_name`='"+field['field_name']+"',`field_type`='"+field['field_type']+"'"
		_template_id = field['template_id']
		_enable = '1' if 'enable' not in field else str(field['enable'])
		_rule = '' if 'rule' not in field else field['rule']
		_min = '0' if 'min' not in field else str(field['min'])
		_max = '0' if 'max' not in field else str(field['max'])
		_fl_field = '' if 'fl_field' not in field else field['fl_field']
		_display_order = '0' if 'display_order' not in field else str(field['display_order'])
		_is_show = '0' if 'is_show' not in field else str(field['is_show'])
		_algorithm = '' if 'algorithm' not in field else field['algorithm']
		_default_value = '' if 'default_value' not in field else field['default_value']
		expression = expression + ",`enable`="+_enable+",`rule`='"+pymysql.escape_string(_rule)+"',`min_size`='"+_min + "',`max_size`='" + _max +"',`display_order`='"+_display_order+"',`is_show`='"+_is_show+"',`algorithm`='"+pymysql.escape_string(_algorithm)+"',`default_value`='"+pymysql.escape_string(_default_value)+"' "
		if action=='update':
			if 'field_id' not in field:
				return Error.MODPARAMERR
			_fl_field = _fl_field.replace('*','sp'+str(field['field_id'])) if  _fl_field[:1]=='*' else _fl_field
			expression = expression + ",`fl_field`='"+_fl_field+"'"
			sql = "update `cms_template_field` set `update_time`=now(),"+expression+" where field_id="+str(field['field_id'])
		else:
			sql = "insert into `cms_template_field` set "+expression
		n,data = self.db.execute(pid,sql)
		#错误断言
		if data['code']!=0:
			return data
		#更新记录到此就结束了
		if action=='update':
			return data

		#继续添加模板域，需要更新模板表结构
		sql = "select field_id from cms_template_field where template_id='"+str(field['template_id'])+"' and field_name='"+field['field_name']+"' order by field_id desc limit 1"
		n,data = self.db.executeQuery(pid,sql)
		if n<1:
			return data
		_field_id = data[0][0]
		#logging.info(str(data))
		#修改刚插入的记录，写入自动生成的fl_field
		_fl_field = _fl_field.replace('*','sp'+str(_field_id)) if  _fl_field[:1]=='*' else _fl_field
		if _fl_field!='':
			sql = "update `cms_template_field` set `fl_field`='"+_fl_field+"' where `field_id`="+str(_field_id)
			n,data = self.db.execute(pid,sql)
			if n<0:
				logging.warning('update fulltext for field failed! SQL:'+sql)
		#修改模板表cms_tbl_{$tid}字段
		_tblname = 'cms_tbl_'+str(_template_id)
		_tblfield= 'sp_'+str(_field_id)
		sql = Common.loadSql('field_create.sql')
		sql = sql.replace('{$tblname}',_tblname).replace('{$field}',_tblfield).replace("{$fieldcname}",field['field_name'])
		n,data = self.db.execute(pid,sql,mutiline=True)
		if data['code']!=0:
			return data
		recode = copy.deepcopy(data)
		recode['fid'] = _field_id
		return data


	def enable_field(self,pid,fid,enable):
		"""set field enable
		设置模板域是否可用
		备注：上边那个改成动态的，这个就可以退休了
		
		Args:
			pid:
			tid:
			enable:

		Returns:
			recode
		"""
		sql = "update `cms_template_field` set `enable`="+str(enable)+" where `field_id`="+str(fid)
		n,data = self.db.execute(pid,sql)
		if n<0:
			return data
		return Error.SUCC


	def get_fulltext_fields(self,pid,tid):
		"""get fulltext field supported

		获取加入搜索引擎的字段列表

		Args:
			pid:项目id
			tid:模板id
		Returns:
			recode
		"""
		sql = "SELECT `field_id`,`fl_field` FROM `cms_template_field` WHERE `template_id`="+str(tid)+" and enable=1 and IFNULL(fl_field,'')!=''"
		n,data = self.db.executeQuery(pid,sql)
		if n<0:
			recode = copy.deepcopy(Error.DBSQLERR)
		else:
			recode = copy.deepcopy(Error.SUCC)
			recode['data'] = data
		return recode
			


	def get_field_list(cls,pid,tid,fid=0,**kargv):
		"""get field list by case,support page

		获取模板域列表，不支持分页,暂无缓存

		Args:
			pid:项目id
			tid:模板id
			fid:模板域id
			kargv:
				detail:是否提供算法和默认值
				order:排序规则
				is_show:是否筛选show字段
				with_system:是否加入系统域

		Returns:
			List[dict]
		"""
		pass

		pid=str(pid)
		if 'detail' not in kargv:
			kargv['detail'] = False
		if 'order' not in kargv:
			kargv['order'] = ' display_order asc'

		if kargv['detail'] is True:
			fields = ",`algorithm`,`default_value`"
		else:
			fields = ""
			
		sql = "select `field_id`,`template_id`,`field_name`,`field_type`,`rule`,`min_size`,`max_size`,`display_order`,`is_show`,`create_time`,`update_time`,`enable`,`fl_field`"+fields+" from cms_template_field where `template_id`="+str(tid)
		if fid!=0:
			sql = sql + " and `field_id`="+str(fid)
		if 'is_show' in kargv:
			sql = sql + " and `is_show`="+str(int(kargv['is_show']))
		if 'enable' in kargv:
			sql = sql + " and `enable`="+str(kargv['enable'])
		sql =sql + " order by "+kargv['order']
		n,data = cls.db.executeQuery(pid,sql)
		#以后改ORM,真tmd写的累
		result = []
		if 'with_system' in kargv and kargv['with_system'] is True:
			result.append({'field_id':0,'field_name':u'创建人','field_ename':'create_user'})
			result.append({'field_id':0,'field_name':u'发布人','field_ename':'publish_user'})
			result.append({'field_id':0,'field_name':u'创建时间','field_ename':'create_time'})
			result.append({'field_id':0,'field_name':u'发布时间','field_ename':'publish_time'})
			result.append({'field_id':0,'field_name':u'发布地址','field_ename':'publish_url'})
		if n>0:
			for row in data:
				item = {'field_id':row[0],'template_id':row[1],'field_ename':'sp_'+str(row[0]),'field_name':row[2],'field_type':row[3],'rule':row[4],'min_size':row[5],'max_size':row[6],'display_order':row[7],'is_show':row[8],'create_time':row[9],'update_time':row[10],'enable':row[11],'fl_field':row[12]}
				if kargv['detail']==True:
					#转换成算法json格式
					#item['algorithm'] = json.loads(row[12])
					item['algorithm'] = row[13]

					item['default_value'] = row[14]

				result.append(item)
			data = result
		return n,data


	def async_rend_field(self,pid,tid):
		"""render field by async task
		
		一个任务由一个主体状态机[task_status]和一个任务邮箱[task_mail]构成，分别是dict和list类型
		状态机用于描述当前主体的渲染状态，生命期为字段数量*2000ms
		任务邮箱用于投递任务日志，任务初始化的时候邮箱清空，生命期和状态机等同

		Returns:
			taskid:fieldrender_pid_tid_timestamp			
		"""
		_cache = self.cache
		#这里暂时共享发布的key
		key = 'fieldrender_'+str(pid)+'_'+str(tid)
		task_status = {'status':'ready','msg':'','taskid':''}
		task_mail = []
		if _cache.exists(key):
			task_status = json.loads(_cache.get(key))
			if task_status['status'] in ('succ','failed'):
				logging.warning('task is running')
				return {'code':0,'errmsg':task_status[status],'taskid':task_status['taskid']}
		#获取field信息和document信息
		task_id = key+'_'+str(int(round(time.time() * 1000)))

		task_mail.append({'code':201,'errmsg':"ready",'smid':key,'tag':"input",'pid':pid,'tid':tid,'did':did,'progress':0})
		#写邮箱
		_cache.setex(task_id,json.dumps(task_mail,ensure_ascii=False),60)
		#写状态机
		_cache.setex(key,json.dumps({'status':'running','msg':'rend field ','taskid':task_id}),30)
		#返回task_id，由客户端触发任务执行，服务端不做消费，也没消息系统
		subprocess.Popen(['python makefield.py '+task_id+'>>log1.txt'],shell=True)
		return {'code':201,'errmsg':'start task','task_id':task_id}
