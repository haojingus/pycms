#coding=utf-8
import os
import sys
import json
import logging
from common import Common

class ThirdParty(object):

	third_party_cfg = {}
	
	def __init__(self):
		pass

	def load_all(self):
		path = "./thirdparty"
		files = os.listdir(path)
		for f in files:
			filename_arr = os.path.splitext(path+'/'+f)
			if filename_arr[1]=='.json':
				try:
					fp = open(path+'/'+f,'r')
					cfg = json.load(fp)
					fp.close()
					self.third_party_cfg[filename_arr[0].replace(path+'/','')] = cfg
				except Exception as e:
					logging.warning(str(e))
				pass
		pass
		return

	def get_api_info(self,corp,apiname):
		"""get api info

		获取API信息
		Args:
			corp:组织机构
			apiname:api名称
		Returns:
			dict
		"""
		if corp not in self.third_party_cfg:
			return None
		return Common.collection_find(self.third_party_cfg[corp],lambda s:s['name']==apiname)
		
