# coding=utf-8
import json
import copy
import logging
import requests
from error import Error
from common import Common


class Fulltext(object):
    webapp = None

    def __init__(self, webapp):
        self.__class__.webapp = webapp

    def get_field_list(self, **kwargv):
        """get fulltext fields by tid,pid
		
		获取可用全文字段列表
		
		Args:
			kwargv:
				curent:当前fl字段
				available:做可用过滤
				pid:pid
				tid:tid
				fid:fid
		Returns:
			recode
		"""
        curent = '' if 'curent' not in kwargv else kwargv['curent']
        available = False if 'available' not in kwargv else kwargv['available']
        tid = 0 if 'tid' not in kwargv else int(kwargv['tid'])
        pid = 0 if 'pid' not in kwargv else int(kwargv['pid'])
        # fid = 0 if 'fid' not in kwargv else int(kwargv['fid'])
        if available and tid != 0:
            # 加载fl数据
            sql = 'select distinct `fl_field` from `cms_template_field` where `template_id`=' + str(
                tid) + " and fl_field<>''"
            n, data = self.webapp.db.executeQuery(pid, sql)
            if n < 0:
                return copy.deepcopy(Error.MODPARAMERR)
            fl_fields = []
            for row in data:
                fl_fields.append(row[0])
        pass
        target_fl_fields = []
        fl_schema = self.webapp.cfg['fulltext']['schema']
        for item in fl_schema:
            k = list(item.items())[0][0]
            if curent == k:
                target_fl_fields.append({'fl_name': k, 'selected': True})
            elif (curent[-2:] in ('_i', '_s')) or (curent[-5:] in ('_text', '_date')):
                target_fl_fields.append({'fl_name': curent, 'selected': True})
            elif Common.collection_find(fl_fields, lambda s: s == k) is None:
                target_fl_fields.append({'fl_name': k, 'selected': False})
        recode = copy.deepcopy(Error.SUCC)
        recode['data'] = target_fl_fields
        return recode

    def update_doc(self, doc):
        solrdoc = {'add': {'doc': doc}}
        api = self.webapp.cfg['fulltext']['api'] + "/update?commit=true&wt=json"
        try:
            r = requests.post(api, data=json.dumps(solrdoc),
                              headers={'content-type': 'application/json', 'charset': 'utf-8'})
            if str(r.status_code) == '200':
                result = json.loads(r.text)
                if result['responseHeader']['status'] != 0:
                    logging.warning('Solr update error. Solr code is ' + str(
                        result['responseHeader']['status']) + ' Bookid is ' + str(doc['id']))
                    return False
            else:
                logging.warning(
                    'Solr update error.HTTP code is ' + str(r.status_code) + ' document is ' + str(doc['id']))
                return False
        except Exception as e:
            logging.warning(str(e))
            return False
        return True
