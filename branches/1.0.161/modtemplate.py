# coding=utf-8
import pymysql
import logging
import os
import json
import copy
import subprocess

from error import Error
from common import Common


class ModTemplate(object):
    """Project Database access class

	执行项目(站点)的增删改查等数据操作
	"""

    db = None
    conf = None

    def __init__(self, webapp):
        """Init ModTemplate  Class
		"""
        self.__class__.db = webapp.db
        self.__class__.conf = webapp.cfg

    def update(self, action, pid, **template):
        """Add template

		添加/修改一个站点模板(数据表)

		Args:
			template:
			template_name:项目名称
			enable:是否启用 True/False
		Returns:
			Error json
		"""
        pass

        pid = str(pid)
        if 'template_name' not in template:
            return Error.MODPARAMERR
        expression = "`project_id`=" + pid + ",`template_name`='" + template['template_name'] + "'"
        _enable = '1' if 'enable' not in template else str(template['enable'])
        _template_view = '' if 'template_view' not in template else template['template_view']
        _template_summary = '' if 'template_summary' not in template else template['template_summary']
        _callback = '' if 'callback' not in template else template['callback']
        _publish_url = self.conf['default_publish_url'] if 'publish_url' not in template else template['publish_url']
        expression = expression + ",`enable`=" + _enable + ",`template_view`='" + pymysql.escape_string(
            _template_view) + "'," \
                              "`template_summary`='" + pymysql.escape_string(
            _template_summary) + "',`publish_callback`='" + pymysql.escape_string(
            _callback) + "',`publish_url`='" + _publish_url + "' "
        if action == 'update':
            if 'template_id' not in template:
                return Error.MODPARAMERR
            sql = "update `cms_template` set " + expression + " where template_id=" + str(template['template_id'])
        else:
            sql = "insert into `cms_template` set " + expression + ",`allow`=''"
        logging.info('Template update SQL:' + sql)
        n, data = self.db.execute(pid, sql)
        # 获取project信息
        if data['code'] != 0:
            return data
        # 更新记录
        if action == 'update':
            return data

        # 添加记录
        sql = "select template_id from cms_template where project_id='" + pid + "' and template_name='" + template[
            'template_name'] + "' order by template_id desc limit 1"
        n, data = self.db.executeQuery(pid, sql)
        if n < 1:
            return data
        _template_id = data[0][0]
        logging.info(str(data))
        # 创建模板表cms_tbl_{$tid}
        _tblname = 'cms_tbl_' + str(_template_id)
        sql = Common.loadSql('template_create.sql')
        sql = sql.replace('{$tblname}', _tblname)
        n, data = self.db.execute(pid, sql, mutiline=True)
        if data['code'] != 0:
            return data
        recode = copy.deepcopy(data)
        recode['tid'] = _template_id
        return data

    def get_template_list(cls, pid, pagesize=-1, pageindex=1, strfilter='', order=''):
        """get template list by case,support page

		获取模板列表，支持分页

		Args:
			pid:项目id
			pagesize:页长度
			pageindex:页码
			strfilter:查找条件
			order:排序规则

		Returns:
			List
		"""
        pass

        pid = str(pid)
        strfilter = '1' if strfilter == '' else strfilter
        order = 'template_id desc' if order == '' else order
        sql = 'select count(*) from cms_template where ' + strfilter
        n, data = cls.db.executeQuery(pid, sql)
        if n == -1:
            return n, data
        count = data[0][0]
        # 处理strfilter和order
        strfilter = strfilter.replace('`', '').replace('template_id', 'a.template_id')
        order = order.replace('`', '').replace('template_id', 'a.template_id')
        sql = "select a.template_id,a.project_id,a.template_name,a.`enable`,a.`template_summary`,ifnull(b.`document_count`,0)  from cms_template a left outer join `cms_template_statistics` b on a.template_id=b.template_id where " + strfilter + ' order by ' + order
        if pagesize > 0:
            sql = sql + ' limit ' + str((pageindex - 1) * pagesize) + ',' + str(pagesize)
        n, data = cls.db.executeQuery(pid, sql)
        if n >= 0:
            return count, data
        return n, data

    def get_template_one(cls, pid, tid):
        """get template detail

		获取模板详细信息
		
		Args:
			pid:项目id
			tid:模板id
		
		Returns:
			Dict
		"""
        pass
        sql = "select `template_id`,`project_id`,`template_name`,`template_view`,`publish_callback`,`publish_url`,`enable`,`template_summary` from `cms_template` where `project_id`=" + str(
            pid) + " and `template_id`=" + str(tid)
        n, data = cls.db.executeQuery(pid, sql)
        if n > 0:
            # 加入多模板支持
            _views = []
            try:
                _views = json.loads(data[0][3].strip())
            except Exception as e:
                _views.append({'name': 'default', 'view': data[0][3].strip(), 'publish_url': data[0][5]})
            # _view被解析为json数组
            # result = {'template_id':data[0][0],'project_id':data[0][1],'template_name':data[0][2].rstrip(),'template_summary':data[0][7].strip(),'template_view':data[0][3].rstrip(),'publish_callback':data[0][4],'publish_url':data[0][5],'enable':data[0][6]}
            result = {'template_id': data[0][0], 'project_id': data[0][1], 'template_name': data[0][2].rstrip(),
                      'template_summary': data[0][7].strip(), 'template_view': _views, 'publish_callback': data[0][4],
                      'publish_url': data[0][5], 'enable': data[0][6]}
            return result
        return Error.DBEMPTYERR

    def create_empty(self, pid=0):
        """ make a empty instance
		"""
        return {'template_id': 0, 'project_id': pid, 'template_name': '',
                'template_view': [{'name': 'default', 'view': '', 'publish_url': self.conf['default_publish_format']}],
                'template_summary': '', 'publish_callback': '', 'publish_url': self.conf['default_publish_format'],
                'enable': 1}

    def update_template_allow(self, pid, user, tids):
        """update template allow users
		修改模板归属

		Args:
			pid:
			user:
			tids:模板id集合 List[]
		Returns:
		"""
        sql = "select template_id,IFNULL(allow,'') from cms_template"
        n, data = self.db.executeQuery(pid, sql)
        if n < 0:
            return data
        sql = ""
        for row in data:
            tid = str(row[0])
            allow = [] if row[1] == '' else json.loads(row[1])
            is_change = False
            # 清理
            if user in allow and tid not in tids:
                allow.remove(user)
                is_change = True
            # 追加
            if user not in allow and tid in tids:
                allow.append(user)
                is_change = True
            # 生成sql
            if is_change:
                sql = sql + "update `cms_template` set allow='" + pymysql.escape_string(
                    json.dumps(allow, ensure_ascii=False)) + "' where `template_id`=" + tid + ";\n"
        pass
        n, data = self.db.execute(pid, sql, mutiline=True)
        if n < 0:
            return data
        return Error.SUCC

    def remove_template(self, pid, tid):
        """
		remove template
		删除模板，删除前会备份至安全区目录./safearea

		Args:
			pid:
			tid:

		Returns:
			
		"""
        _cfg = Common.collection_find(self.conf['db'], lambda s: s['pid'] == int(pid))
        if _cfg is None:
            return Error.DATANOTEXISTED
        _cfg['tid'] = tid
        cmd = "mysqldump -h " + _cfg['host'] + " -u " + _cfg['user'] + " -p" + _cfg['passwd'] + " cms_site_" + str(
            pid) + " cms_tbl_" + str(tid) + " >./safearea/" + str(pid) + "_" + str(tid) + ".sql"
        child = subprocess.Popen([cmd], shell=True)
        child.wait()
        cmd = 'mysql -h{$host} -P{$port} -u {$user} -p{$passwd} --execute="select * from cms_template where template_id={$tid}" cms_site_{$pid} >./safearea/template_cfg_{$pid}_{$tid}.bak'
        cmd = Common.exp_render(cmd, _cfg)
        child = subprocess.Popen([cmd], shell=True)
        child.wait()
        cmd = 'mysql -h{$host} -P{$port} -u {$user} -p{$passwd} --execute="select * from cms_template_field where template_id={$tid}" cms_site_{$pid} >./safearea/template_field_{$pid}_{$tid}.bak'
        cmd = Common.exp_render(cmd, _cfg)
        child = subprocess.Popen([cmd], shell=True)
        child.wait()
        sql = "DROP TABLE IF EXISTS `cms_tbl_" + str(tid) + "`;\n"
        sql = sql + "delete from `cms_template_field` where template_id=" + str(tid) + ";\n"
        sql = sql + "delete from `cms_template` where template_id=" + str(tid) + ";"
        n, data = self.db.execute(pid, sql, mutiline=True)

        if n < 0:
            return data
        return Error.SUCC
