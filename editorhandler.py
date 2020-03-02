# coding=utf-8
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

from modproject import ModProject
from modtemplate import ModTemplate
from modvariable import ModVariable
from modcomponent import ModComponent
from moddocument import ModDocument
from modfield import ModField
from plugin import Plugin
from plugins.fieldtype.algorithm import Algorithm
from basehandler import BaseHandler

from tornado.options import define, options
from pycket.session import SessionMixin
import urllib
import base64

class EditorHandler(BaseHandler):

    def get(self, input):
        """ get route

			处理所有/editor/下的get路由
		"""
        if not self._checkSession():
            return
        _action = self.get_argument('action', '')

        # ACL检查
        if not self._checkACL(input, _action):
            return

        if input == 'document':
            if _action == 'list':
                self.__list_documents()
            if _action in ('add', 'update'):
                self.__update_document(_action)
            if _action == 'preview':
                self.__preview_document()

    def post(self, input):
        """ post route
			
			处理所有/editor/下的post路由
		"""
        if not self._checkSession():
            return
        pass
        _action = self.get_argument('action', '')

        # ACL检查
        if not self._checkACL(input, _action):
            return
        if input == 'document':
            if _action in ('add', 'update'):
                self.__update_document(_action, True)
            if _action == 'remove':
                self.__remove_document()

    def __update_document(self, action, isapi=False):
        """ add/update document controller

			创建/修改文档的路由

			Argument:
			isapi:是否为操作接口，False为view路由，True为API操作
		"""
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        did = int(self.get_argument('did', 0))

        if pid == 0 or tid == 0:
            logging.warning('CGI Param error!')
            self.write(json.dumps(Error.CGIREQUESTERR))
            return
        pass

        if isapi == False:
            # 获取文档信息
            _doc_data = {}
            if did != 0:
                _doc = ModDocument(self.application)
                _doc_data = _doc.get_document_one(pid, tid, did)
                if _doc_data is None:
                    self.write(json.dumps(Error.DBEMPTYERR))
                    return
            pass
            publish_url = "" if 'publish_url' not in _doc_data else _doc_data['publish_url'][1]
            publish_url = "" if publish_url is None else publish_url
            # render document page for view
            _field = ModField(self.application)
            n, _field_list = _field.get_field_list(pid, tid, detail=True)
            if n < 0:
                self.write(json.dumps(_field_list))
                return
            _plugin = Plugin(self.application)
            form_html = ""
            form_submit_js = ""
            form_js = ""
            form_css = ""
            form_fields = []
            vue_data = []
            remove_list = []
            for i in range(0, len(_field_list)):
                # build_result = _plugin.make_field_html(pid,tid,_field_list[i]['field_id'])
                _field_list[i]['algorithm'] = Algorithm.parse_algorithm(_field_list[i]['algorithm'])
                _field_cfg = self.application.core.get_field_detail(_field_list[i]['field_type'])
                # 只处理input类型的插件
                if _field_cfg['type'] == 'input' and _field_list[i]['enable'] == 1:
                    # 合成html css js
                    form_html = form_html + _field_cfg['html'].replace('{$field_id}',
                                                                       str(_field_list[i]['field_id'])).replace(
                        '{$field_name}', _field_list[i]['field_name']) + '\n<!--auto html code-->\n'
                    form_submit_js = form_submit_js + Common.js_encode(_field_cfg['submit']).replace('{$field_id}', str(
                        _field_list[i]['field_id'])) + '\n//cms auto js code\n'
                    form_js = form_js + _field_cfg['js'].replace('{$field_id}', str(
                        _field_list[i]['field_id'])) + '\n//cms auto js code\n'
                    form_css = form_css + _field_cfg['css'] + '\n/*cms auto css */\n'
                    # form_fields.append(str(_field_list[i]['field_id']))
                    # 生成vue_user_data
                    if 'sp_' + str(_field_list[i]['field_id']) in _doc_data:
                        _field_list[i]['field_value'] = _doc_data['sp_' + str(_field_list[i]['field_id'])][1]
                    else:
                        _field_list[i]['field_value'] = _field_list[i]['default_value']
                    _field_list[i]['field_value'] = str(base64.b64encode(urllib.parse.quote(_field_list[i]['field_value']).encode(encoding='utf-8')),
                        encoding='utf-8')
                    #_field_list[i]['field_value'] = _field_list[i]['field_value'].replace("'", "\\'").replace("\n",
                    #                                                                                          "\\n").replace(
                    #    "\r", "")
                else:
                    # out类插件和enable=0的插件不显示
                    remove_list.append(_field_list[i])
                pass
                form_fields.append(str(_field_list[i]['field_id']))
            # 清除所有out类型插件
            for t in remove_list:
                _field_list.remove(t)
            form = {'html': form_html, 'js': form_js, 'css': form_css, 'submit': form_submit_js}
            self.render_ex('editor_document.html', action=action, project_id=pid, template_id=tid, document_id=did,
                           forminfo=form, form_fields=(',').join(form_fields), fields_data=_field_list,
                           publish_url=publish_url)
        else:
            # add/update document api
            form_fields = self.get_argument('field_ids', '')
            if form_fields == '':
                self.write(json.dumps(Error.CGIREQUESTERR))
                return
            data = {}
            for sp in form_fields.split(','):
                data['sp_' + sp] = self.get_argument('_sp' + sp + "_value", '')
            # 获取登录用户昵称
            curent_user = self.userinfo['nick_name'] if self.userinfo['nick_name'].strip() != '' else self.userinfo[
                'username']
            url = self.get_argument('publish_url', '')
            _doc = ModDocument(self.application)
            result = _doc.update(pid, tid, document_id=did, publish_url=url, user=curent_user, data=data)
            self.write(json.dumps(result))

    def __remove_document(self):
        """remove document

		删除文档
		Args:
		Returns:
		"""
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        did = int(self.get_argument('did', 0))
        if pid == 0 or tid == 0 or did == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
        doc = ModDocument(self.application)
        recode = doc.remove_document(pid, tid, did)
        self.write(json.dumps(recode))
        return

    def __list_documents(self):
        """list all document for template

		列出指定模板下的所有文档
		Args:
		Returns:
			List[]
		"""
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        pageindex = int(self.get_argument('page', 1))
        pflag = int(self.get_argument('pflag', -1))
        fl = "1"
        display_status = '全部'
        if pflag == 0:
            fl = "(publish_url is NULL or publish_url='')"
            display_status = '未发布'
        if pflag == 1:
            fl = "(publish_url is not NULL or publish_url<>'')"
            display_status = '已发布'

        if pid == 0 or tid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
        # 构建Component Tag列表
        ctag = self.get_argument('ctag', '')
        with_data = []
        if ctag != '':
            with_data.append(ctag)
        _component = ModComponent(self.application)
        n, tag_data = _component.get_component_tags(pid, tid)
        if n < 0:
            return Error.DBERROR
        # 构建筛选器 dk:关键词 df:所选模板域(field)
        dk = self.get_argument('dk', '')
        df = self.get_argument('df', '')
        field = ModField(self.application)
        _n, field_list = field.get_field_list(pid, tid, detail=False, with_system=True)
        if dk != '' and df != '':
            # 对时间类型、数值类型、字符串类型特殊处理
            if df in ('create_time', 'publish_time'):
                dk = Common.filter_digit(dk)
                dk = "" if len(dk) != 8 else dk[:4] + "-" + dk[4:6] + "-" + dk[6:8]
                if dk != "":
                    fl = fl + " and " + df + ">'" + dk + " 00:00:00' and " + df + "<='" + dk + " 23:59:59'"
            elif df in ('document_id'):
                dk = Common.filter_digit(dk)
                dk = "0" if dk == "" else dk
                fl = fl + "document_id=" + dk
            else:
                fl = fl + " and " + df + " like '%" + dk + "%'"
        # 构建文档列表
        page = int(self.get_argument('page', 1))
        doc = ModDocument(self.application)
        pagesize = 30
        count, data = doc.get_document_list(pid, tid, pagesize, pageindex, fl, ' document_id desc', True, with_data)
        if count < 0:
            self.write(json.dumps(data))
            return
        p_cfg = Common.collection_find(self.application.cfg['db'], lambda s: s['pid'] == int(pid))
        domain = '' if p_cfg is None else p_cfg['domain']
        pageinfo = Common.make_page(count, pageindex, pagesize, 20)
        self.render_ex('editor_document_list.html', project_id=pid, template_id=tid, data=data, domain=domain,
                       pageinfo=pageinfo, pflag=pflag, display_status=display_status, field_list=field_list,
                       tags=tag_data, ctag=ctag, dk=dk, df=df)

    def __preview_document(self):
        """preview document

		预览文档
		"""
        url = self.get_argument('url', '')
        pid = self.get_argument('pid', '0')
        print('URL', url)
        if url == '':
            self.write('error url')
        elif os.path.exists('./site/' + pid + url):
            fp = open('./site/' + pid + url, 'r')
            c = fp.read()
            fp.close()
            self.write(c)
        else:
            self.write('file is not existed')
        return
