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
import markdown
import codecs
from interpreter import Interpreter
from dbmanager import DbManager
from common import Common
from error import Error
from acl import ACL
import hashlib
from modtemplate import ModTemplate
from moduser import ModUser
from modplugin import ModPlugin
from plugin import Plugin
from plugins.fieldtype.algorithm import Algorithm
from basehandler import BaseHandler

from tornado.options import define, options
from pycket.session import SessionMixin
from tornado.web import Finish
import base64
import urllib.parse


class SystemHandler(BaseHandler):

    def get(self, input):
        """ get route

            处理所有/system/下的get路由
        """
        pass
        _action = self.get_argument('action', '')
        if _action == 'welcome' and input == 'user':
            self.__login(_action)
            return
        else:
            if not self._checkSession():
                return
        # 登录已完成

        # 错误页面
        if input == 'error':
            code = self.get_argument('code', 0)
            errmsg = self.get_argument('errmsg', 'unknown error!')
            self.render_ex('system_error.html', code=code, errmsg=errmsg)
            return

        # ACL检查
        if not self._checkACL(input, _action):
            return

        if input == 'plugin':
            if _action == 'list':
                self.__list_plugin()
                return
            if _action in ('add', 'update'):
                self.__update_plugin(_action)
            if _action == 'preview':
                self.__preview_plugin()
        if input == 'guide':
            if _action == 'readme':
                self.__readme()
        if input == 'user':
            if _action == 'update':
                self.__update_user(_action)
            if _action == 'list':
                self.__list_user()
            if _action == 'updateacl':
                self.__update_user_acl(_action)
            if _action == 'logout':
                self.session.set('userinfo', "")
                self.set_status(302)
                self.set_header('Location', '/system/user?action=welcome')
        if input == 'about':
            self.render_ex('system_about.html', version=self.application.version)

    def post(self, input):
        """ post system route

            处理所有/system/下的post路由
        """
        _action = self.get_argument('action', '')
        if input == 'user' and _action == 'login':
            self.__login(_action)
            return
        self._checkSession()
        if not self._checkACL(input, _action):
            return

        if input == 'plugin':
            if _action in ('add', 'update'):
                self.__update_plugin(_action, True)
            if _action == 'debug':
                self.__debug_plugin()
        if input == 'algorithm':
            self.__debug_algorithm()
        if input == 'user':
            if _action == 'update':
                self.__update_user(_action, True)
            if _action == 'updateacl':
                self.__update_user_acl(_action, True)

    def __update_plugin(self, action, isapi=False, detail=None):
        """ add/update document controller

            创建/修改文档的路由

            Argument:
            isapi:是否为操作接口，False为view路由，True为API操作
        """
        field_type = self.get_argument('type', '')
        if field_type == '' and action == 'update':
            self.write(json.dumps(Error.CGIREQUESTERR))
            logging.warning('cgi error')
            return

        if not isapi:
            # render plugin page for view
            detail = copy.deepcopy(self.application.core.get_field_detail(field_type))
            if detail is None:
                detail = {"name": "", "cname": "", "field_type": "", "type": "input", "order": 999, "html": "",
                          "css": "", "js": "", "submit": "", "debug_input": "", "debug_value": ""}
            else:
                plugin = ModPlugin(self.application)
                detail['debug_input'], detail['debug_value'] = plugin.get_test_data(field_type)
            for item in ('html', 'css', 'js', 'submit'):
                # out类插件需要补足数据
                if detail['type'] == 'out':
                    detail[item] = ''
                else:
                    detail[item] = str(base64.b64encode(urllib.parse.quote(detail[item]).encode(encoding='utf-8')),
                                       encoding='utf-8')
                # js转义转换
                # v1.8取消转义，改为base64
            pass
            # detail[item] = detail[item].replace('\\', '\\\\').replace("'", "\\'").replace('\n', "\\n").replace(
            # '\r',
            # '') detail['debug_input'] = detail['debug_input'].replace("'", "\\'").replace('\n', "\\n").replace(
            # '\r', '') detail['debug_value'] = detail['debug_value'].replace("'", "\\'").replace('\n',
            # "\\n").replace('\r', '')
            self.render('system_plugin.html', action=action, plugin=detail, userinfo=self.userinfo)
            return
        else:
            cgi_params = self.__get_argument(('name', 'cname', 'field_type', 'type', 'order', 'html', 'css', 'js',
                                              'form_submit', 'debug_input', 'debug_value'))
            _check = ('name', 'cname', 'field_type', 'order')
            for item in _check:
                if cgi_params[item] == '':
                    self.write(json.dumps(Error.CGIREQUESTERR))
                    logging.warning(str(cgi_params))
                    return
            plugin = ModPlugin(self.application)
            recode = plugin.create_plugin(cgi_params)
            if recode['code'] == 0:
                self.application.core.reload()
                self.set_status(302)
                self.set_header('Location', '/system/plugin?action=list')
            self.write('err')
            return

    def __list_plugin(self):
        """list all plugin

        列出所有插件
        Args:
        Returns:
            List[]
        """

        plugins = self.application.core.get_all()
        self.render('system_plugin_list.html', plugins=plugins, userinfo=self.userinfo)

    def __debug_plugin(self):
        """debug user plugin

        调试模板域插件
        Args:
        Returns:
        """
        plugin_info = {}
        plugin_info['html'] = self.get_argument('html', '')
        plugin_info['css'] = self.get_argument('css', '')
        plugin_info['js'] = self.get_argument('js', '')
        plugin_info['submit'] = self.get_argument('form_submit', '')
        debug_input = self.get_argument('debug_input', '')
        # debug_input = debug_input.replace("'", "\\'")
        debug_value = self.get_argument('debug_value', '')
        field_id = 10086
        field_name = '这是一个测试域'
        field_value = debug_value

        for item in ('html', 'css', 'js', 'submit'):
            plugin_info[item] = plugin_info[item].replace('{$field_id}', str(field_id))\
                .replace('{$field_name}', field_name)\
                .replace('{$field_value}', field_value)
            # plugin_info[item] = str(base64.b64encode(urllib.parse.quote(plugin_info[item]).encode(
            # encoding='utf-8')),encoding='utf-8')

        _html = self.render_string('system_plugin_debug.html', html=plugin_info['html'], css=plugin_info['css'],
                                   js=plugin_info['js'], submit=plugin_info['submit'],
                                   debug_input=debug_input, field_value=debug_value, field_id=field_id,
                                   field_name=field_name, userinfo=self.userinfo)
        self.application.cache.setex('plugins', 60, str(_html, encoding='utf-8'))
        self.write(_html)

    # self.write({'code':0,'errmsg':'succ','debugid':'plugins'}

    def __preview_plugin(self):
        """preview document

        预览文档
        """
        debugid = self.get_argument('debugid', '')
        if debugid == '':
            self.write('error')
        self.write(self.application.cache.get(debugid))
        return

    def __debug_algorithm(self):
        exp = Interpreter(self.application)
        debug_data = self.get_argument('debug_data', '')
        # default_data = self.get_argument('value', '')
        code = self.get_argument('code', '')
        field_type = self.get_argument('field_type', 'system:singletextbox')
        field_info = self.application.core.get_field_detail(field_type)
        pid = int(self.get_argument('project_id', 0))
        tid = int(self.get_argument('template_id', 0))
        _input, _script = exp.debug(pid, tid, code, debug_data)
        self.render('system_algorithm_debug.html', tinput=_input, tscript=_script, field=field_info,
                    userinfo=self.userinfo)

    def __readme(self):
        fp = codecs.open('readme.md', 'r', 'utf-8')
        c = fp.read()
        fp.close()
        exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 'markdown.extensions.tables',
                'markdown.extensions.toc']
        ret = markdown.markdown(c, extensions=exts)
        self.render('system_guide_readme.html', readme=ret, userinfo=self.userinfo)

    def __get_argument(self, params):
        cgi_params = {}
        for item in params:
            cgi_params[item] = self.get_argument(item, '')
        return cgi_params

    def __login(self, action):
        if action == 'welcome':
            self.render('system_login.html', level='info', message=u'欢迎使用CMS')
            return
        if action == 'login':
            username = self.get_argument('username', '')
            password = self.get_argument('password', '')
            # 登录验证
            user = ModUser(self.application)
            recode = user.login(username, password)
            if recode['code'] == 0:
                userinfo = recode['data']
                # ,"acl":{"template":"*","flag":0x1fff}}
                # 写入session
                self.session.set('userinfo', json.dumps(userinfo, ensure_ascii=False))
                self.set_status(302)
                self.set_header('Location', '/')
                return
            else:
                self.render('system_login.html', level='warning', message=recode['errmsg'])
            return

    def __update_user(self, action, isapi=False):
        """create/update user base info
        创建更改用户基本信息

        Args:
            action
            isapi
        Returns:
        """
        uid = self.get_argument('uid', '0')
        print(self.application.cfg['db'])
        projects = copy.deepcopy(self.application.cfg['db'])
        projects.reverse()
        projects.pop()
        projects.reverse()
        projects.append({'pid': 0, 'project': '*'})
        mod = ModUser(self.application)
        if not isapi:
            uinfo = mod.get_user_info(uid=uid)
            uinfo = {'uid': '', 'username': '', 'nickname': '', 'avator': '', 'status': 1,
                     'acl': '[]'} if uinfo is None else uinfo
            date = []
            plist = ACL.get_acl_projects(json.loads(uinfo['acl']))
            for i in range(0, len(projects)):
                if uinfo is None:
                    projects[i]['enable'] = 0
                else:
                    p = Common.collection_find(plist, lambda s: s == int(projects[i]['pid']))
                    projects[i]['enable'] = p is not None
                # projects[i]['acl'] = ACL.get_acl_projects(json.loads(uinfo['acl']))
            self.render('system_user.html', projects=projects, target=uinfo, userinfo=self.userinfo)
        else:
            # 处理post
            username = self.get_argument('username', '')
            nickname = self.get_argument('nickname', '')
            avator = self.get_argument('avator', '')
            pid_set = self.get_arguments('projects')
            uinfo = mod.get_user_info(uid=uid)
            acl = []
            if uinfo is not None:
                acl = json.loads(uinfo['acl'])
            # 扫2次，对比差异
            new_acl = []
            for item in acl:
                if Common.collection_find(pid_set, lambda s: s == str(item['pid'])) is not None:
                    new_acl.append(item)

            for i in range(0, len(pid_set)):
                p = Common.collection_find(new_acl, lambda s: s['pid'] == int(pid_set[i]))
                if p is None:
                    new_acl.append({'pid': int(pid_set[i]), 'acl': []})
            # 完成构建
            recode = mod.update_user_info(uid=uid, username=username, nickname=nickname, avator=avator,
                                          acl=json.dumps(new_acl))
            if recode['code'] == 0:
                self.set_status(302)
                self.set_header('Location', '/system/user?action=list')
            else:
                self.write(json.dumps(recode))

    def __list_user(self):
        """user list view
        用户列表

        Args:
        Returns:
        """
        mod = ModUser(self.application)
        ulist = mod.get_user_list()
        if ulist['code'] == 0:
            self.render('system_user_list.html', users=ulist['data'], userinfo=self.userinfo)

    def __update_user_acl(self, action, isapi=False):
        """update user template acl
        更新用户模板详细设置

        Args:
            action:
            isapi

        Returns:
        """
        uid = int(self.get_argument('uid', 0))
        pid = int(self.get_argument('pid', 0))
        if uid == 0 or pid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
            return
        _usr = ModUser(self.application)
        if isapi == False:
            _template = ModTemplate(self.application)
            n, data = _template.get_template_list(pid)
            if n < 0:
                self.write(json.dumps(Error.MODPARAMERR))
                return
            uinfo = _usr.get_user_info(uid=uid)
            uinfo = {'uid': '', 'username': '', 'avator': '', 'status': 1, 'acl': '[]'} if uinfo is None else uinfo
            tlist = ACL.get_acl_templates(pid, json.loads(uinfo['acl']))
            # 检查root_acl
            user_acl = Common.collection_find(tlist, lambda s: s['tid'] == 0)
            project_root_acl = 0 if user_acl is None else user_acl['acl']
            templates = [{'template_id': 0, 'template_name': '*', 'acl': project_root_acl}]
            # 获取普通模板acl
            for row in data:
                _item = {'template_id': int(row[0]), 'template_name': row[2], 'acl': 0}
                user_acl = Common.collection_find(tlist, lambda s: s['tid'] == int(row[0]))
                if user_acl is not None:
                    _item['acl'] = user_acl['acl']
                templates.append(_item)
            self.render('system_user_detail.html', templates=templates, acl=ACL.AclCode, target=uinfo, project_id=pid,
                        userinfo=self.userinfo)
        else:
            acl = self.get_arguments('acl')
            uinfo = _usr.get_user_info(uid=uid)
            if uinfo is None:
                self.write(json.dumps(Error.ACL_NOTFOUNDUSER))
                return
            _uacl = json.loads(uinfo['acl'])
            # item：tid_DOC_E ....
            # 构建一个需要追加权限的list
            _new_template_acl = []
            _tid_set = []
            for item in acl:
                _tid = item.split('_')[0]
                if _tid not in _tid_set:
                    _tid_set.append(_tid)
                _tacl = Common.collection_find(_new_template_acl, lambda s: s['tid'] == int(_tid))
                if _tacl is not None:
                    # 这里修改的是引用值，不是深拷贝
                    _index = _new_template_acl.index(_tacl)
                    _new_template_acl[_index] = {'tid': int(_tid),
                                                 'acl': _tacl['acl'] | ACL.AclCode[item.replace(_tid + '_', '')]}
                else:
                    # 没有的就追加
                    _new_template_acl.append({'tid': int(_tid), 'acl': ACL.AclCode[item.replace(_tid + '_', '')]})

            # 修改template表的allow
            _template = ModTemplate(self.application)
            recode = _template.update_template_allow(pid, uinfo['username'], _tid_set)
            if recode['code'] != 0:
                self.write(json.dumps(recode))
                return
            # 改写pacl
            _pacl = Common.collection_find(_uacl, lambda s: s['pid'] == pid)
            if _pacl is None:
                _uacl.append({'pid': pid, 'acl': _new_template_acl})
            else:
                _pacl['acl'] = _new_template_acl
            recode = _usr.update_user_info(uid=uid, acl=json.dumps(_uacl))
            if recode['code'] == 0:
                self.set_status(302)
                self.set_header('Location', '/system/user?action=list')
                return
            else:
                self.write(json.dumps(recode))
                return
