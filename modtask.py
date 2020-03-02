# coding=utf-8
import json
import logging
import copy
import redis
import subprocess
import time
from error import Error
from common import Common


class ModTask(object):
	cache = None
	current_user = 'Nobody'
	timeout = 60

	def __init__(self, webapp):
		self.__class__.cache = webapp.cache
		if 'username' in webapp.curent_user:
			self.__class__.current_user = webapp.curent_user['username']
		pass

	def async_batch_render(self, pid, tid, did_set):
		"""batch render document for publish

		批量发布页面
		Args:
			pid:项目id
			tid:模板id
			did_set:目标did集合
		Returns:
			void
		"""
		_cache = self.cache
		task_id = '_'.join(['batchpub', str(pid), str(tid), did_set + ',', str(int(round(time.time() * 1000)))])
		task_mail = []
		prefix = 'batchpub_' + str(pid) + '_' + str(tid) + '_'
		if len(_cache.keys(prefix + '*')) > 0:
			return copy.deepcopy(Error.COMPILE_PENDING)
		task_mail = [
			{'code': 201, 'errmsg': 'ready', 'user': self.current_user, 'pid': pid, 'tid': tid, 'didset': did_set,
			 'progress': 0}]
		_cache.setex(task_id, self.timeout, json.dumps(task_mail, ensure_ascii=False))
		# 该任务系统需要具备自行建立单独发布任务邮箱和状态机的功能，否则无法对接单体发布
		# 以上功能集成于batchpub.py中
		subprocess.Popen(['python3 batchpub.py ' + task_id + '>>batch.log'], shell=True)
		return {'code': 201, 'errmsg': 'start task', 'task_id': task_id}
		pass

	def async_render(self, algorithm_type, pid, tid, did, preview):
		"""render document by async task

		一个任务由一个主体状态机[task_status]和一个任务邮箱[task_mail]构成，分别是dict和list类型
		状态机用于描述当前主体的渲染状态，生命期为字段数量*2000ms
		任务邮箱用于投递任务日志，任务初始化的时候邮箱清空，生命期和状态机等同

		Returns:
			taskid
		"""
		_cache = self.cache
		key = '_'.join([algorithm_type, str(pid), str(tid), str(did)])

		task_status = {'status': 'ready', 'msg': '', 'taskid': ''}
		task_mail = []
		if _cache.exists(key):
			task_status = json.loads(str(_cache.get(key), encoding='utf-8'))
			if task_status['status'] in ('succ', 'failed'):
				logging.warning('task is running')
				return {'code': 0, 'errmsg': task_status['status'], 'taskid': task_status['taskid']}
		# 获取field信息和document信息
		task_id = key + '_' + str(int(round(time.time() * 1000)))

		task_mail.append(
			{'code': 201, 'errmsg': "ready", 'smid': key, 'tag': algorithm_type, 'pid': pid, 'tid': tid, 'did': did,
			 'user': self.current_user, 'preview': preview, 'progress': 0})
		# 写邮箱
		_cache.setex(task_id, 60, json.dumps(task_mail, ensure_ascii=False))
		logging.info('task id ok ' + task_id)
		# 写状态机
		_cache.setex(key, 30, json.dumps({'status': 'running', 'msg': 'rend field ', 'taskid': task_id}))
		# 返回task_id，由客户端触发任务执行，服务端不做消费，也没消息系统
		subprocess.Popen(['python3 compile.py ' + task_id + '>>' + algorithm_type + '.log'], shell=True)
		return {'code': 201, 'errmsg': 'start task', 'task_id': task_id}

	def get_task_status(self, taskid):
		"""get task status

		获取任务状态，用于高速轮询

		Returns:
			dict
		"""
		_cache = self.cache
		if not _cache.exists(taskid):
			return {'code': 404, 'errmsg': 'no task'}
		mail = json.loads(str(_cache.get(taskid), encoding='utf-8'))
		return mail[-1]

	def get_batch_task_status(self, taskid):
		if not self.cache.exists(taskid):
			total_recode = {'code': 404, 'errmsg': 'no task'}
			return total_recode
		mail = json.loads(str(self.cache.get(taskid), encoding='utf-8'))
		total_recode = mail[-1]
		if 'single_task_id' in total_recode:
			single_recode = self.get_task_status(total_recode['single_task_id'])
			if 'progress' not in single_recode:
				total_recode['single_progress'] = 0
			else:
				total_recode['single_progress'] = single_recode['progress']
		else:
			total_recode['single_process'] = 0
		return total_recode
