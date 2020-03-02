#coding=utf-8
from datetime import datetime
import json
import copy

from common import Common
from httprpc import HttpRpc
from error import Error

class ModUser(object):

	webapp = None
	db = None
	def __init__(self,webapp):
		self.__class__.webapp = webapp
		self.__class__.db = webapp.db
	
	def login(self,username,password):
		rpc = HttpRpc(self.webapp)
		recode = rpc.call('zzsjapi','get_token','post',params={'username':username,'password':password})
		if recode['code'] !=0:
			return recode
		if recode['result']['code'] == 0:
			authcode = recode['result']['data']['token']
			recode = rpc.call('zzsjapi','get_user_info','get',params={'token':authcode})
			if recode['code'] !=0:
				return recode
			print(recode)
			if recode['result']['code'] == 0:
				#用户信息RPC获取成功
				r = copy.deepcopy(Error.SUCC)
				r['data'] = recode['result']['data']
				uinfo = self.get_user_info(uid=r['data']['uid'])
				if uinfo== None:
					return Error.CMSACCOUNTMISS
				'''
				if uinfo['username']!=r['data']['username'] or uinfo['nickname']!=r['data']['nick_name']:
					recode = self.update_user_info(uid=uinfo['uid'],username=r['data']['username'],nickname=r['data']['nick_name'])
					if recode['code']!=0:
						return recode
				'''
				r['data']['username'] = uinfo['username']
				r['data']['avator'] = uinfo['avator']
				r['data']['acl'] = json.loads(uinfo['acl'])
				r['data']['nick_name'] = uinfo['nickname']
				print(r)
				return r
			else:
				return {'code':500,'errmsg':recode['result']['msg']}	
		else:
			return {'code':500,'errmsg':str(recode['result'])}
	

	
	def get_user_info(self,**userinfo):
		"""get userinfo

		获取cms用户信息

		Args:
			userinfo:
			uid:int
			username:string
		Returns:
			dict
		"""
		#modtmp = ModTemplate(self.webapp)
		#没那么大规模，暂时不支持细分权限
		exp = ""
		if 'uid' in userinfo:
			exp = '`user_id`='+str(userinfo['uid'])
		elif 'username' in userinfo:
			exp = "`username`='"+userinfo['username']+"'"
		else:
			return None
		sql = "select user_id,username,nickname,avator,acl,status from `cms_user` where "+exp
		n,data = self.db.executeQuery(0,sql)
		if n<1:
			return None
		return {'uid':data[0][0],'username':data[0][1],'nickname':data[0][2],'avator':data[0][3],'acl':data[0][4],'status':data[0][5]}


	def update_user_info(self,**info):
		"""update cms user info

		修改cms用户信息，该用户依赖于外部Open ID

		Args:
			info:
				uid:用户id
				username:用户名
				avator:头像
				acl:权限策略
		Returns:
			dict
		"""
		if 'uid' not in info:
			return Error.MODPARAMERR
		uinfo = self.get_user_info(uid=info['uid'])
		sql = ""
		fields = []
		for k,v in info.items():
			if k!='uid' and k!='username':
				fields.append("`"+k+"`='{$"+k+"}'")
		exp = ",".join(fields)
		if uinfo is not None:
			sql = "update `cms_user` set "+exp+" where user_id={$uid}"
		else:
			sql = "insert into `cms_user` set user_id={$uid},username='{$username}',nickname='{$nickname}',avator='{$avator}',acl='{$acl}',groupid=1,status=1"
		sql = Common.exp_render(sql,info)
		n,data = self.db.execute(0,sql)
		if n<0:
			return data
		return Error.SUCC

	def get_user_list(self):
		"""get all user

		获取所有cms用户

		Args:
		Returns:
			List
		"""
		sql = "select user_id,username,nickname,groupid,avator,acl,createTime,status from cms_user"
		n,data = self.db.executeQuery(0,sql)
		if n<0:
			return data
		recode = copy.deepcopy(Error.SUCC)
		recode['data'] = []
		for row in data:
			recode['data'].append({'uid':row[0],'username':row[1],'nickname':row[2],'groupid':row[3],'avator':row[4],'createtime':row[6],'status':row[7],'acl':json.loads(row[5])})
		return recode

	'''
	def login(self,username,password):
		#rpc = RPC(self.webapp)
		_sso_key = self.source
		#非第三方登陆不需要auth_code
		recode = {"code":-1,"result":{"status":1,"data":{"auth_code":"",}}}
		if self.webapp.system_config["use_third_sso"] == 0:
			recode = self.get_token(username=username,password=password)
		else:
			recode = self.webapp.thirdparty.call(_sso_key,'get_token','post',params={'username':username,'password':password,'remember_me':1})
		#返回码被统一为code
		if recode['code'] !=0:
			return recode


		#读取本地用户信息
		local_info = self.get_one('',uname=username,ext_table={'table':'user_group','fields':['access'],'join':['group_id','group_id']})
		if local_info['code'] !=0:
			return local_info
		local_info = local_info['data']
		
		if self.webapp.system_config["use_third_sso"] == 0:
			r = copy.deepcopy(Error.SUCC)
			r['data'] = {}
			r['data']['uid'] = local_info['uid']
			r['data']['username'] = local_info['uname']
			r['data']['groupid'] = local_info['group_id']
			#这个key的信息是从配置抽离出来的
			r['data']['access'] = local_info['access']
			r['data']['token'] = recode['data']['token']
			return r
		else:
			token = "" if recode['result']['status']!=1 else recode['result']['data']['auth_code']
			if recode['result']['status'] == 1:
				recode = self.webapp.thirdparty.call(_sso_key,'get_user_info','get',params={'auth_code':token})
				if recode['code'] !=0:
					return recode
				if recode['result']['status'] == 1:
					#用户信息RPC获取成功
					r = copy.deepcopy(Error.SUCC)
					r['data'] = recode['result']['data']
					r['data']['uid'] = local_info['uid']
					r['data']['uname'] = local_info['uname']
					r['data']['nickname'] = local_info['nickname']
					r['data']['groupid'] = local_info['group_id']
					r['data']['access'] = local_info['access']
					return r
				else:
					return {'code':500,'errmsg':recode['result']['msg']}	
			else:
				return {'code':500,'errmsg':recode['result']['msg']}
	'''
