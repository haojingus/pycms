#coding=utf-8
import copy
from common import Common

class ACL(object):
	DOC_E=0x1
	DOC_P=0x2
	TEMP_E=0x10
	TEMP_D=0x20
	SYS_M=0x1FFF

	AclCode = {'DOC_E':0x1,'DOC_P':0x2,'TEMP_E':0x10,'TEMP_D':0x20,'SYS_M':0x1FFF}

	def __init__(self):
		pass

	@staticmethod
	def get_acl_projects(user_acl):
		"""get acl for user

		获取用户基于模板的ACL序列

		Args:
			user_acl:用户acl字典
		Returns:
			int
		"""
		plist = []
		for p in user_acl:
			plist.append(p['pid'])
		return plist

	@staticmethod
	def get_acl_templates(pid,user_acl):
		"""get acl for project
		"""
		plist = []
		p = Common.collection_find(user_acl,lambda s:s['pid']==int(pid))
		if p is None:
			return plist
		return copy.deepcopy(p['acl'])

	@staticmethod
	def is_root(pid,user_acl):
		"""check root for project
		
		判断是否对项目有root权限
		Args:
			pid:
			user_acl: dict
		Returns:
			AclCode
		"""
		p = Common.collection_find(user_acl,lambda s:s['pid']==int(pid))
		if p is not None:
			t = Common.collection_find(p['acl'],lambda s:s['tid']==0)
			if t is not None:
				return t['acl']
		return 0
