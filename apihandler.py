#coding=utf-8
import os.path
import sys
import json
import copy
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from datetime import datetime
from dbmanager import DbManager
from common import Common
from error import Error
import hashlib

from modtemplate import ModTemplate
from modvariable import ModVariable
from modcomponent import ModComponent
from moddocument import ModDocument
from modtask import ModTask

from tornado.options import define, options

class ApiHandler(tornado.web.RequestHandler):

	api_method = ""

	def get(self,input):
		""" get route

			处理所有/editor/下的get路由
		"""
		self.__router('GET',input,self.request.headers)
		#self.write("URI:"+input+ "<br>GET:"+self.get_argument('param','')+'<br>'+self.request.headers)
		pass


	def post(self,input):
		""" post route include create、save
			
			处理所有/editor/下的post路由
		"""
		self.__router('POST',input,self.request.headers)
		#self.write("URI:"+input+ "<br>POST:"+self.get_argument('param','')+'<br>'+str(self.request.headers))
		pass

	
	def put(self,input):
		""" put route 
		"""
		self.__router('PUT',input,self.request.headers)
		#self.write("URI:"+input+ "<br>PUT:"+self.get_argument('param','')+'<br>'+str(self.request.headers))
		pass

	def patch(self,input):
		""" patch route include publish
		"""
		self.__router('PATCH',input,self.request.headers)
		#self.write("URI:"+input+ "<br>PUT:"+self.get_argument('param','')+'<br>'+str(self.request.headers))
		pass


	def __router(self,method,input,header):
		""" router request
		
		路由选择器
		Args:
			method:GET/POST/PUT/PATCH/DELETE
			input:tornado input
			header:HTTP header dict

		Returns:
			None
		"""
		res,strfilter = self.__request_parser(input)
		res_arr = res.split('/')
		#只开放document
		if res_arr[0]=='document':
			self.__api_document(method,res,strfilter)
		elif res_arr[0]=='component':
			self.__api_component(method,res,strfilter)
		else:
			self.set_status(403)
			self.write(json.dumps(Error.API_NOTSUPPORTED))
			return
		self.finish()
		pass


	def __api_document(self,method,res,strfilter):
		print('api docment:')
		res_arr = res.split('/')
		if len(res_arr)<3:
			self.set_status(406)
			self.write(json.dumps(Error.API_RESERROR))
			return
		did = 0
		pid = 0
		tid = 0
		did_set = []
		res_type = self.get_argument('format','json')
		try:
			pid = int(res_arr[1])
			tid = int(res_arr[2])
			if len(res_arr)==4:
				did_set = res_arr[3].split(',')
				if len(did_set) == 1:
					did = int(did_set[0])
				for i in range(0,len(did_set)):
					did_set[i] = Common.filter_digit(did_set[i])
		except Exception as e:
			self.set_status(400)
			self.write(json.dumps(Error.API_RESERROR))
			return
		if method == 'GET':
			if did==0:
				_doc = ModDocument(self.application)
				_fl	= self.get_argument('fl','1')
				_page = int(self.get_argument('page',1))
				_pagesize= int(self.get_argument('pagesize',30))
				_order = self.get_argument('order','document_id desc')
				#print _fl,_order,_page
				n,data = _doc.get_document_list(pid,tid,_pagesize,_page,_fl,_order,False)
				if n<0:
					self.set_status(500)
					self.write(json.dumps(data))
				else:
					recode = {'code':0,'data':data}
					self.write(json.dumps(recode))
				return
			else:
				#输出html内容
				if res_type=="page":
					_doc = ModDocument(self.application)
					_page = _doc.get_document_page(pid,tid,did)
					if _page is None:
						self.set_status(404)
						self.write(json.dumps(Error.DATANOTEXISTED))
					else:
						self.write(_page)
				else:
					self.write('not support json document!')
				return
		if method == 'POST':
			if did==0:
				#新建文档
				data = {}
				_req = self.request.arguments
				for k,v in _req.items():
					if k[:3]=='sp_':
						data[k] = v[0]
				if len(data.keys())==0:
					self.set_status(411)
					self.write(json.dumps(Error.API_RESERROR))
					return
				_doc = ModDocument(self.application)
				recode = _doc.update(int(pid),int(tid),**{'document_id':0,'user':'spider','data':data})
				if 'did' in recode:
					self.set_status(200)
					self.write(json.dumps(recode))
				else:
					self.set_status(500)
					self.write(json.dumps(Error.API_EXECERROR))
				return
			else:
				#修改文档
				self.set_status(501)
				self.write(json.dumps(Error.API_NOTIMPLEMENT))
				return
		if method == 'PATCH':
			if len(did_set)==0:
				self.set_status(406)
				self.write(json.dumps(Error.API_RESERROR))
				return
			else:
				task = ModTask(self.application)
				task.current_user = 'spider'
				recode = task.async_batch_render(pid,tid,','.join(did_set))
				self.write(json.dumps(recode))
				return
		if method == 'PUT':
			if did==0:
				self.set_status(406)
				self.write(json.dumps(Error.API_RESERROR))
			return
		self.set_status(403)
		self.write(json.dumps(Error.API_RESERROR))
		pass

	
	def __api_component(self,method,res,strfilter):
		""" api for component
	
		组件API
	
		Args:
			method:
			res:
			strfilter:
		Returns:
			None
		"""
		res_arr = res.split('/')
		if len(res_arr)<5:
			self.set_status(406)
			self.write(json.dumps(Error.API_RESERROR))
			return
		pid = 0
		try:
			pid = int(res_arr[2])
			tid = int(res_arr[3])
			did = int(res_arr[4])
		except Exception as e:
			self.set_status(400)
			self.write(json.dumps(Error.API_RESERROR))
			return
		pass
		if method == 'PATCH':
			if res_arr[1]=='data':
				_component = ModComponent(self.application)
				_req = self.request.arguments
				data = {}
				for k,v in _req.items():
					data[k] = v[0]
				recode = _component.update_component_data(pid,tid,did,**data)
				self.write(json.dumps(recode))
			#print self.request.arguments
			#print method,res,strfilter
			return
		self.set_status(403)
		self.write(json.dumps(Error.API_RESERROR))
		pass

	def __token_check(self,token):
		"""authentication check

		认证检查
		Args:
			token:认证令牌
		Returns:
			json code
		"""
		pass


	def __request_parser(self,req):
		"""query string parser

		解析url
		Args:
			req:请求的URI
		Returns:
			resource,path
		"""
		arr_req = req.split('?')
		resource = arr_req[0]
		if resource=='':
			return None
		strfilter = {}
		if len(arr_req)==2:
			arr_filter = arr_req[1].split('&')
			for item in arr_filter:
				param = item.split('=')
				if len(param)==2:
					strfilter[param[0]]=param[1]
		pass
		return resource,strfilter

	def __api_assert(self,bool_exp,code,jscode):
		if bool_exp:
			self.set_status(code)
			self.write(json.dumps(jscode))
			self.finish()


