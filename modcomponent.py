# coding=utf-8
import pymysql
import logging
import os
import json
import copy

from datetime import datetime
from error import Error
from common import Common


class ModComponent(object):
    """CMS project component access class

	执行项目的组件管理
	组件类型：AD/STAT/DEBUG
	"""

    db = None
    core = ""
    conf = None

    def __init__(self, webapp):
        """Init ModComponent Class
		"""
        self.__class__.db = webapp.db

    def update(self, action, pid, **component):
        """Add/Update project component

		添加/修改一个组件

		Args:
			action:add/update
			pid:项目id
			component:
				component_name:变量名称
				component_type:变量类型
				component_content:变量值
				enable:是否启用 True/False
		Returns:
			Error json
		"""
        pass

        pid = str(pid)
        if not ('component_name' in component and 'component_symbol' in component and 'component_content' in component):
            return Error.MODPARAMERR
        cname = component['component_name'] if 'component_cname' not in component else component[
            'component_cname']
        summary = '' if 'component_summary' not in component else component['component_summary']

        expression = "`component_name`='" + component['component_name']
        expression = expression + "',`component_cname`='" + cname
        expression = expression + "',`component_summary`='" + pymysql.escape_string(summary)
        expression = expression + "',`component_symbol`='" + pymysql.escape_string(component['component_symbol'])
        expression = expression + "',`component_content`='" + pymysql.escape_string(
            component['component_content']) + "'"
        _enable = '1' if 'enable' not in component else str(component['enable'])
        expression = expression + ",`enable`=" + _enable
        if action == 'update':
            if 'component_id' not in component:
                return Error.MODPARAMERR
            sql = "update `cms_component` set " + expression + " where component_id=" + component['component_id']
        else:
            sql = "insert into `cms_component` set " + expression
        n, data = self.db.execute(pid, sql)
        # 错误检查
        if data['code'] != 0:
            return data
        recode = copy.deepcopy(data)
        # 更新记录到此就结束了
        if action == 'update':
            return data

        # 获取新插入的记录的id
        sql = "select component_id from `cms_component` where `component_name`='" + component[
            'component_name'] + "' order by component_id desc limit 1"
        n, data = self.db.executeQuery(pid, sql)
        if n < 1:
            return data
        _component_id = data[0][0]
        logging.info(str(data))
        recode['component_id'] = _component_id
        return data

    def get_component_list(self, pid, strfilter='', order='component_id desc'):
        """get component list by case,not support page
		获取组件列表(或单个组件)，不支持分页

		Args:
			pid:项目id
			strfilter:查找条件
			order:排序规则

		Returns:
			List
		"""
        pass
        strfilter = '1' if strfilter == '' else strfilter
        sql = "select `component_id`,`component_name`,`component_cname`,`component_summary`,`component_symbol`,`create_time`,`enable` from `cms_component` where " + strfilter + ' order by ' + order
        n, data = self.db.executeQuery(pid, sql)
        return n, data

    def get_component_one(self, pid, cid):
        """get component detail info
		获取组件详情

		Args:
			pid:项目id
			cid:组件id

		Returns:
			Dict
		"""
        sql = "select `component_id`,`component_name`,`component_cname`,`component_summary`,`component_symbol`,`component_content`,`create_time`,`enable` from `cms_component` where `component_id`=" + str(
            cid)
        n, data = self.db.executeQuery(pid, sql)
        if n > 0:
            return {'component_id': data[0][0], 'component_name': data[0][1], 'component_cname': data[0][2],
                    'component_summary': data[0][3], 'component_symbol': data[0][4], 'component_content': data[0][5],
                    'create_time': data[0][6], 'enable': data[0][7]}
        else:
            return None

    def get_component_tags(self, pid, tid):
        """
		获取模板所用组件产生的所有tag
		
		Args:
			pid:项目id
			tid:模板id

		Returns:
			List
		"""
        sql = "select distinct `component_tag` from `cms_component_data` where `template_id`=" + str(tid)
        n, data = self.db.executeQuery(pid, sql)
        return n, data

    def update_component_data(self, pid, tid, did, **cdata):
        """
		更新组件数据统计值

		Args:
			pid:项目id
			tid:模板id
			did:文档id
			data:
				tag:组件标签，用于区分同一组件的不同数据项
				day:日数据
				month:月数据
				total:总数据
				effect_d:日数据统计截止日
				effect_m:月数据统计截止月

		Returns:
			recode
		"""
        # 为解决灵活性，不能一次搞定所有维度
        # sql = "INSERT INTO `cms_component_data` (`template_id`,`document_id`,`component_id`,`component_tag`) VALUES (1,2,3) ON DUPLICATE KEY UPDATE c=1;"
        if 'tag' not in cdata or 'component_id' not in cdata:
            return Error.MODPARAMERR

        expression = ''
        if 'day' in cdata and 'effect_day' in cdata:
            expression = expression + "`data_day`='" + str(cdata['day']) + "',`effect_day`='" + cdata[
                'effect_day'] + "'"
        if 'month' in cdata and 'effect_month' in cdata:
            expression = expression + "," if len(expression) > 0 else ''
            expression = expression + "`data_month`='" + str(cdata['month']) + "',`effect_month`='" + cdata[
                'effect_month'] + "'"
        if 'total' in cdata:
            expression = expression + "," if len(expression) > 0 else ''
            expression = expression + "`data_total`='" + str(cdata['total']) + "'"
        pass
        if expression == '':
            return Error.MODPARAMERR

        sql = "select `data_id` from `cms_component_data` where `template_id`=" + str(
            tid) + " and `document_id`=" + str(did) + " and `component_tag`='" + cdata['tag'] + "'"
        n, data = self.db.executeQuery(pid, sql)
        if n > 0:
            # update
            sql = "update `cms_component_data` set " + expression + ",`update_time`=now() where `data_id`=" + str(
                data[0][0])
        else:
            # insert
            sql = "insert into `cms_component_data` set " + expression + ",`template_id`=" + str(
                tid) + ",`document_id`=" + str(did) + ",`component_tag`='" + cdata['tag'] + "',`component_id`=" + str(
                cdata['component_id'])
        n, data = self.db.execute(pid, sql)
        if n > 0:
            return Error.SUCC
        else:
            return data
