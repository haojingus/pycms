# coding=utf-8
import pymysql
import logging
import os
import json
import copy
import time
import subprocess
from error import Error
from common import Common

from modfield import ModField
from fulltext import Fulltext

from plugins.fieldtype.algorithm import Algorithm


class ModDocument(object):
    """Document access class

	执行文档的增删改查等数据操作
	"""

    db = None
    conf = None
    modfield = None
    cache = None
    webapp = None

    def __init__(self, webapp):
        """Init ModDocument  Class
		"""
        self.__class__.webapp = webapp
        self.__class__.db = webapp.db
        self.__class__.conf = webapp.cfg['system']
        self.__class__.modfield = ModField(webapp)
        self.__class__.cache = webapp.cache

    def update(self, pid, tid, **document):
        """Add document

		添加/修改一个文档,入库后的用户字段为序列化后的信息

		Args:
			pid:项目id
			tid:模板id
			document:
				document_id:文档id
				data.sp_x:各模板域
				publish_url:发布URL
				user:当前用户
		Returns:
			Error json
		"""
        pass
        action = 'add' if document['document_id'] == 0 else 'update'
        pid = str(pid)
        if ('document_id' not in document) and ('user' in document) is False:
            return Error.MODPARAMERR
        publish_url = '' if 'publish_url' not in document else document['publish_url']
        # 对输入做处理，入库为{"input":value,"result":value}的格式，input为输入，result为算法执行结果，此处只入input
        exp = []
        for (k, v) in document['data'].items():
            if k != 'document_id':
                # vv = pymysql.escape_string(json.dumps({"input":v}))
                vv = pymysql.escape_string(v)
                exp.append("`" + k + "`='" + vv + "'")
        expression = ",".join(exp)
        tblname = "cms_tbl_" + str(tid)
        if action == 'update':
            if 'document_id' not in document:
                return Error.MODPARAMERR
            sql = "update `" + tblname + "` set " + expression + ",`modify_user`='" + document[
                'user'] + "',`publish_url`='" + publish_url + "' where document_id=" + str(document['document_id'])
        else:
            sql = "insert into `" + tblname + "` set " + expression + ",`create_user`='" + document[
                'user'] + "',`modify_user`='" + document['user'] + "',`publish_url`='" + publish_url + "'"
        # logging.info('Document update SQL:'+sql)
        n, data = self.db.execute(pid, sql)
        # 错误判断
        if data['code'] != 0:
            return data
        if action == 'update':
            recode = copy.deepcopy(data)
            recode['did'] = int(document['document_id'])
        # 更新记录到此结束
        else:
            # 获取id并返回
            sql = "select document_id from `" + tblname + "` where `create_user`='" + document[
                'user'] + "' order by document_id desc limit 1"
            n, data = self.db.executeQuery(pid, sql)
            if n < 1:
                return data
            _document_id = data[0][0]
            recode = copy.deepcopy(Error.SUCC)
            recode['did'] = _document_id
            # 加入文档数统计
            sql = "INSERT INTO `cms_template_statistics` (template_id,document_count) VALUES(" + str(
                tid) + ", 1) ON DUPLICATE KEY UPDATE `document_count`=`document_count`+1"
            _n, _stat_data = self.db.execute(pid, sql)
            if _n < 1:
                logging.warning('insert template statistces error.tid=' + str(tid) + ' did=' + str(_document_id))
        # 开始更新lucene fulltext
        mod = ModField(self.webapp)
        data = mod.get_fulltext_fields(pid, tid)
        if data['code'] != 0:
            logging.warning('get fulltext field failed')
        else:
            lucene_doc = {'id': str(pid) + '-' + str(tid) + '-' + str(recode['did']), 'pid': int(pid), 'tid': int(tid),
                          'did': int(recode['did'])}
            for row in data['data']:
                _k = 'sp_' + str(row[0])
                if _k in document['data']:
                    lucene_doc[row[1]] = document['data'][_k]
            print(lucene_doc)
            if len(data['data']) > 0:
                fl = Fulltext(self.webapp)
                if not fl.update_doc(lucene_doc):
                    logging.warning('Lucene API call failed!')
        return recode

    def get_document_list(self, pid, tid, pagesize, pageindex, strfilter='1', order='document_id desc', is_show=True,
                          with_data=[]):
        """get document list by case,support page

		获取文档列表，支持分页

		Args:
			pid:项目id
			tid:模板id
			pagesize:页长度
			pageindex:页码
			strfilter:查找条件
			order:排序规则

		Returns:
			count,List[json] 结果集是个比较复杂的dict对象
		"""
        pass

        if pid == 0 or tid == 0:
            return -1, Error.MODPARAMERR
        if is_show:
            n, data = self.modfield.get_field_list(pid, tid, is_show=is_show, enable=1)
        else:
            n, data = self.modfield.get_field_list(pid, tid, enable=1)
        if n == -1:
            return n, data
        _fields = []
        # 配置额外数据项
        _tbl_header = [(u'文档id', 0), (u'创建人', 0), (u'创建时间', 0), (u'发布人', ''), (u'发布时间', 0), (u'发布路径', 0)]
        for row in data:
            _fields.append('sp_' + str(row['field_id']))
            _tbl_header.append((row['field_name'], row['field_id']))
        # 追加component data表头
        if len(with_data) > 0:
            _tbl_header.append((u''.join(with_data), 0))

        _tblname = "cms_tbl_" + str(tid)
        strfilter = '1' if strfilter == '' else strfilter
        order = 'document_id desc' if order == '' else order

        sql = "select count(*) from `" + _tblname + "` where " + strfilter
        n, data = self.db.executeQuery(pid, sql)
        if n == -1:
            return n, data
        count = data[0][0]
        _select_field = "" if len(_fields) == 0 else "," + ",".join(_fields)
        # 数据项追加
        if len(with_data) == 0:
            sql = "select `document_id`,`create_user`,date_format(`create_time`,'%Y-%c-%d %H:%i:%s'),`publish_user`,date_format(`publish_time`,'%Y-%c-%d %H:%i:%s'),`publish_url` " + _select_field + " from `" + _tblname + "` where " + strfilter + " order by " + order + ' limit ' + str(
                (pageindex - 1) * pagesize) + ',' + str(pagesize)
        else:
            # strfilter order需要处理
            strfilter = self.__sql_join_escape(strfilter, 'a', ('document_id', 'template_id', 'create_time'))
            order = self.__sql_join_escape(order, 'a', ('document_id', 'template_id', 'create_time'))
            sql = "select a.`document_id`,a.`create_user`,date_format(a.`create_time`,'%Y-%c-%d %H:%i:%s'),a.`publish_user`,date_format(a.`publish_time`,'%Y-%c-%d %H:%i:%s'),a.`publish_url`" + _select_field + ",CONCAT(CONVERT(ifnull(b.data_day,0),SIGNED),'/',CONVERT(ifnull(b.data_month,0),SIGNED),'/',CONVERT(ifnull(b.data_total,0),SIGNED)) from `" + _tblname + "` a left outer join (select * from cms_component_data where component_tag='" + \
                  with_data[0] + "' and template_id=" + str(
                tid) + ") as b on a.document_id=b.document_id where " + strfilter + " order by " + order + ' limit ' + str(
                (pageindex - 1) * pagesize) + ',' + str(pagesize)

        n, data = self.db.executeQuery(pid, sql)
        if n == -1:
            return n, data
        result = {"head": _tbl_header, "data": data}
        # {"head":[(string,string),(string,string),....],"data":[[col0,col1,...],[col0,col1,...],....]
        return count, result

    def get_document_one(self, pid, tid, did):
        """get document detail

		获取文档详细信息
		
		Args:
			pid:项目id
			tid:模板id
			did:文档id
		
		Returns:
			Dict 不含编译，包含cname
		"""
        pass

        n, data = self.get_document_list(pid, tid, 1, 1, " `document_id`=" + str(did), '', False)
        if n < 1:
            return None
        result = {}
        # 以字典嵌套元组方式构造返回 {'sp_x':(cname,value),.....}
        result['document_id'] = (u'文档id', data['data'][0][0])
        result['create_user'] = (u'创建人', data['data'][0][1])
        result['create_time'] = (u'创建时间', data['data'][0][2])
        result['publish_user'] = (u'发布人', data['data'][0][3])
        result['publish_time'] = (u'发布时间', data['data'][0][4])
        result['publish_url'] = (u'发布路径', data['data'][0][5])
        # print '###',data['head']
        for i in range(6, len(data['head'])):
            result['sp_' + str(data['head'][i][1])] = (data['head'][i][0], data['data'][0][i])
        return result

    def get_document_page(self, pid, tid, did):
        """get document page
		获取文档页面内容

		Args:
			pid:项目id
			tid:模板id
			did:文档id
		Returns:
			string
		"""
        doc = self.get_document_one(pid, tid, did)
        if doc is None or len(doc['publish_url'][1]) == 0:
            return None
        path = "./site/" + str(pid) + doc['publish_url'][1]
        content = ""
        try:
            fp = open(path, "r")
            content = fp.read()
            fp.close()
        except Exception as e:
            print(e)
            return None
        return content

    def remove_document(self, pid, tid, did):
        """remove document
		删除文档

		Args:
			pid:
			tid:
			did:
		Returns:Code
		"""
        doc = self.get_document_one(pid, tid, did)
        if doc is None:
            return Error.DATANOTEXISTED
        path = './safearea/' + '_'.join([str(pid), str(tid), str(did)]) + '.bak'
        fp = open(path, 'a')
        fp.write(json.dumps(doc, ensure_ascii=False))
        fp.close()
        sql = "delete from `cms_tbl_" + str(tid) + "` where `document_id`=" + str(did)
        n, data = self.db.execute(pid, sql)
        if n < 0:
            return Error.DATAREMOVEFAILED
        sql = "update `cms_template_statistics` set `document_count`=`document_count`-1 where `template_id`=" + str(
            tid) + " and `document_count`>0"
        n, data = self.db.execute(pid, sql)
        if n < 1:
            logging.warning('update template statistics error. tid:' + str(tid) + " document_id:" + str(did))
        return Error.SUCC

    def __sql_join_escape(self, sql, alias, fields):
        for item in fields:
            _f = "`" + item + "`"
            sql = sql.replace(_f, item).replace(item, alias + "." + _f)
        return sql
