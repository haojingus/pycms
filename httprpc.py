#coding=utf-8
import requests
import logging
import copy
from error import Error

class HttpRpc(object):

	tp = None
	def __init__(self,webapp):
		self.__class__.tp = webapp.thirdparty
		pass

	def call(self,corp,apiname,method,**req):
		"""call webservice
		
		http API调用

		Args:
			corp:所属组织
			apiname:api名称
			method:http方式
			req:数据和header
		Returns:
			json
		"""
		apiinfo = self.tp.get_api_info(corp,apiname)
		if apiinfo is None:
			return Error.TP_API_NOTFINDCFG
		method = method.lower()
		headers = {} if 'headers' not in req else req['headers']
		r = None
		if method=='get':
			r = requests.get(apiinfo['url'],params=req['params'], headers=headers)
		elif method=='post':
			r = requests.post(apiinfo['url'],data=req['params'], headers=headers)
		else:
			return Error.TP_API_INVAILDMETHOD

		recode = copy.deepcopy(Error.SUCC)
		recode['result'] = r.json()
		return recode

