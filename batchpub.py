#!/usr/local/bin/python3
#coding=utf-8
import subprocess
import time
import sys
import os
import copy
import json
import redis
import pymysql

from common import Common

class Publish(object):

	timeout = 20
	share_memory = None
	task_id = ''

	def __init__(self):
		cfg = Common.loadConfig()
		self.__class__.share_memory = redis.Redis(host=cfg['redis']['host'], port=cfg['redis']['port'],db=1)
		pass

	def batch_publish(self,task_id):
		self.__class__.task_id = task_id
		self.__assert(not self.share_memory.exists(task_id),404,"can't find taskid")
		task_mail = json.loads(str(self.share_memory.get(task_id),encoding='utf-8'))
		header_mail = task_mail[0]
		print('TASK MAIL', task_mail)
		self.__assert(header_mail['code']!=201,500,'header code err')

		pid = header_mail['pid']
		tid = header_mail['tid']
		did_set = header_mail['didset']
		user = header_mail['user']

		#开始循环发布
		arr_did = did_set.split(',')
		doc_count = len(arr_did)
		i = 0
		for did in arr_did:
			#创建单体发布任务
			key = '_'.join(['script',str(pid),str(tid),did])
			single_task_id = key+'_'+str(int(round(time.time() * 1000)))
			#单体任务id写入主任务邮箱
			task_mail.append({'code':201,'errmsg':u'开始渲染[did:'+did+']','progress':int(float(i)/float(doc_count)*100),'single_task_id':single_task_id})
			self.share_memory.setex(task_id, self.timeout, json.dumps(task_mail,ensure_ascii=False))


			single_task_mail = [{'code':201,'errmsg':"ready",'smid':key,'tag':'script','pid':str(pid),'tid':str(tid),'did':did,'user':user,'preview':'N','progress':0}]
			self.share_memory.setex(single_task_id, self.timeout, json.dumps(single_task_mail,ensure_ascii=False))
			self.share_memory.setex(key, self.timeout, json.dumps({'status': 'running', 'msg': 'rend field ', 'taskid': single_task_id}))
			child = subprocess.Popen(['python3 compile.py '+single_task_id+'>>script.log'],shell=True)
			child.wait()
			i = i+1
			task_mail.append({'code':201,'errmsg':u'渲染[did:'+did+u']完成','progress':int(float(i)/float(doc_count)*100),'single_task_id':single_task_id})
			self.share_memory.setex(task_id, self.timeout, json.dumps(task_mail, ensure_ascii=False))
		task_mail.append({'code': 200, 'errmsg': u'渲染完成]', 'progress':100, 'single_progress': 100})
		self.share_memory.setex(task_id, self.timeout, json.dumps(task_mail,ensure_ascii=False))
		return

	def __build_single_task(self,pid,tid,did,ptype='script'):
		task_id = ''
		return task_id

	def __assert(self,boolexp,code,msg):
		if boolexp:
			self.share_memory.setex(self.task_id, self.timeout, json.dumps([{'code':500,'errmsg':msg}]))
			print(code,msg)
			exit(1)
		return

if __name__=='__main__':
	if len(sys.argv)!=2:
		print('argv error')
		exit(1)

	pub = Publish()
	pub.batch_publish(sys.argv[1])
