# coding=utf-8
import os.path
import sys
import json
import re
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
from modfield import ModField
from modtask import ModTask
from fulltext import Fulltext
from basehandler import BaseHandler
from acl import ACL
from tornado.options import define, options
from pycket.session import SessionMixin


class AdminHandler(BaseHandler):

    def get(self, input):
        """ get route

            处理所有/admin/下的get路由
        """
        _action = self.get_argument('action', '')
        # 这个不做鉴权
        if not self._checkSession():
            return
        pass
        _action = self.get_argument('action', '')

        if not self._checkACL(input, _action):
            return
        if input == 'project':
            # 读取cookie
            self.__update_project(_action)
        if input == 'template':
            self._checkACL(input, _action)
            if _action == 'list':
                self.__list_templates()
            if _action in ('add', 'update'):
                self.__update_template(_action)
        if input == 'field':
            if _action == 'list':
                self.__list_fields()
            if _action in ('add', 'update'):
                self.__update_field(_action)
        if input == 'variable':
            pass
        if input == 'component':
            if _action == 'list':
                self.__list_components()
            if _action in ('add', 'update'):
                self.__update_component(_action)
            pass
        if input == 'task' and _action == 'query':
            self.__get_task_status()

    def post(self, input):
        """ post route

            处理所有/admin/下的post路由
        """
        _action = self.get_argument('action', '')

        if not self._checkSession():
            return
        pass
        # 异步任务单独鉴权
        if input == 'task':
            if _action == 'create':
                self.__create_task()
            if _action == 'batchpub':
                self.__create_batch_task()
            return

        # 统一鉴权
        if not self._checkACL(input, _action):
            return

        if input == 'project':
            self.__update_project(_action, True)
        if input == 'template':
            if _action in ('add', 'update'):
                self.__update_template(_action, True)
            if _action == 'remove':
                self.__remove_template()
        if input == 'component':
            if _action in ('add', 'update'):
                self.__update_component(_action, True)
            if _action == 'remove':
                self.__remove_component()

        if input == 'field':
            self.__update_field(_action, True)

    def __update_project(self, action, isapi=False):
        """ add/update project controller

            创建/修改项目的路由

            Argument:
            isapi:是否为操作接口，False为view路由，True为API操作
        """
        pass
        if isapi == False:
            if action == 'add':
                self.render('admin_project.html', action='add', project_id=0, userinfo=self.userinfo)
            if action == 'update':
                self.write('not supported')
        else:
            # 项目入库并初始化
            proj = ModProject(self.application)
            name = self.get_argument('name', '')
            domain = self.get_argument('domain', '')
            rsync = self.get_argument('rsync', '')
            mysql = self.get_argument('mysql', '')
            enable = int(self.get_argument('enable', '1'))
            pid = int(self.get_argument('pid', '0'))
            if action == 'add':
                _proj = Common.collection_find(self.application.cfg['db'], lambda s: s['project'] == name)
                if _proj is not None:
                    self.write(json.dumps(Error.MODDATAEXISTED))
                    return
                result = proj.add(project_id=pid, project_name=name, domain=domain, rsync_uri=rsync, mysql_uri=mysql,
                                  enable=enable)
                self.write(json.dumps(result))
                return
            if action == 'update':
                self.write('not supported')

    def __list_templates(self):
        """list all template for project

        列出指定项目下的所有模板
        Args:
        Returns:
            List[]
        """
        pid = int(self.get_argument('pid', 0))
        if pid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
            return
        page = int(self.get_argument('page', 1))
        temp = ModTemplate(self.application)
        # 权限过滤
        template_acl_filter = "" if ACL.is_root(pid, self.userinfo['acl']) != 0 else " allow like '%\"" + self.userinfo[
            'username'] + "\"%' "
        count, data = temp.get_template_list(pid, 200, page, template_acl_filter, 'template_id desc')
        if type(data) in (dict,):
            self.write(json.dumps(data))
            return
        self.render('admin_template_list.html', project_id=pid, templates=data, userinfo=self.userinfo)
        return

    def __update_template(self, action, isapi=False):
        """ add/update template

            创建/修改模板

            Argument:
            isapi:是否为操作接口，False为view，True为API操作
        """
        pass

        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        if pid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
            return

        if isapi == False:
            # 加载变量列表、模板域列表、组件列表
            _component = ModComponent(self.application)
            _field = ModField(self.application)
            _variable = ModVariable(self.application)
            n, components = _component.get_component_list(pid)
            if n < 0:
                # 组件库加载失败
                self.write(json.dumps(components))
                return
            fields = self.application.cfg['default_template_field']
            if tid > 0 and action == 'update':
                n, localfield = _field.get_field_list(pid, tid, enable=1)
                if n < 0:
                    # 模板域加载错误
                    self.write(json.dumps(localfield))
                    return
                for item in localfield:
                    fields.append({'name': 'sp_' + str(item['field_id']), 'cname': '{$' + item['field_name'] + '}'})
            pass
            n, variables = _variable.get_variable_list(pid)
            if n < 0:
                self.write(json.dumps(variables))
                return

            temp = ModTemplate(self.application)
            data = {}
            if action == 'add':
                data = temp.create_empty(pid)
                # self.render('admin_template.html',action='add',project_id=str(pid),variables=variables,fields=fields,components=components,template_id=0)
            if action == 'update':
                temp = ModTemplate(self.application)
                data = temp.get_template_one(pid, tid)
                if 'code' in data:
                    self.write(json.dumps(data))
                    return
            # action拦截，过滤不支持的action
            if action not in ('add', 'update'):
                self.write('no support')
                return
            self.render('admin_template.html', action=action, template=data, project_id=str(pid), template_id=tid,
                        variables=variables, fields=fields, components=components, userinfo=self.userinfo)
            return
        else:
            # 项目入库并初始化,用于API和Ajax调用
            _template = ModTemplate(self.application)
            name = self.get_argument('name', '')
            summary = self.get_argument('summary', '')
            view = self.get_argument('view', '')
            callback = self.get_argument('callback', '')
            url = self.get_argument('url', self.application.cfg['default_publish_format'])
            enable = int(self.get_argument('enable', '1'))
            result = 'failed'
            # 重名检查
            strfilter = " `template_name`='" + name + "'"
            strfilter = strfilter + " and `template_id`<>" + str(tid) if tid != 0 else strfilter
            n, data = _template.get_template_list(pid, 10, 1, strfilter)
            if n > 0:
                self.write(json.dumps(Error.MODDATAEXISTED))
                return
            # 重名监测End
            if action == 'add':
                result = _template.update(action, pid, template_name=name, template_summary=summary, template_view=view,
                                          callback=callback, publish_url=url, enable=enable)
            if action == 'update':
                if tid == 0:
                    logging.warning(str(Error.CGIREQUESTERR))
                    self.write(json.dumps(Error.CGIREQUESTERR))
                    return
                result = _template.update(action, pid, template_id=tid, template_name=name, template_summary=summary,
                                          template_view=view, callback=callback, publish_url=url, enable=enable)
            pass
            self.write(json.dumps(result))

    def __remove_template(self):
        """remove template
        删除模板

        """
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        if pid == 0 or tid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
            return
        _mod = ModTemplate(self.application)
        recode = _mod.remove_template(pid, tid)
        self.write(json.dumps(recode))
        return

    def __list_fields(self):
        """list all template for project

        列出指定模板下的所有模板域
        Args:
        Returns:
            List[]
        """
        pass
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        if pid == 0 or tid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
        _f = ModField(self.application)
        count, data = _f.get_field_list(pid, tid)
        if count >= 0:
            self.render('admin_field_list.html', project_id=pid, template_id=tid, fields=data, userinfo=self.userinfo)
        else:
            self.write(json.dumps(data))

    def __update_field(self, action, isapi=False):
        """ add/update field

            创建/修改模板域

            Argument:
            isapi:是否为操作接口，False为view，True为API操作
        """
        pass
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        fid = int(self.get_argument('fid', 0))
        if pid == 0 or tid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
            return

        _field_types = self.application.core.get_field_types()
        fl = Fulltext(self.application)
        if isapi == False:
            if action == 'add':
                # 构造一个空data
                data = {'field_name': '', 'rule': '', 'min_size': '0', 'max_size': '0', 'display_order': '0',
                        'enable': 1, 'is_show': 1,
                        'algorithm': u'@@sql结果集\n[sql]\n\n@@后台模板域算法\n[input:raw]\n\n@@前台渲染算法\n[script:raw]\n',
                        'default_value': ''}
                fl_fields = fl.get_field_list(available=True, pid=pid, tid=tid)
                if fl_fields['code'] != 0:
                    self.write(json.dumps(fl_fields))
                    return
                print(fl_fields)
                self.render('admin_field.html',
                            types=_field_types,
                            project_id=pid,
                            template_id=tid,
                            field_id=fid,
                            action=action,
                            data=data,
                            fl_fields=fl_fields['data'],
                            userinfo=self.userinfo)
                return
            if action == 'update':
                _field = ModField(self.application)
                n, data = _field.get_field_list(pid, tid, fid, detail=True)
                if n < 1:
                    self.write(json.dumps(data))
                    return
                _field_data = data[0]
                _field_types = self.application.core.get_field_types(_field_data['field_type'])
                fl_fields = fl.get_field_list(available=True, pid=pid, tid=tid, curent=_field_data['fl_field'])
                if fl_fields['code'] != 0:
                    self.write(json.dumps(fl_fields))
                    return
                self.render('admin_field.html',
                            types=_field_types,
                            project_id=pid,
                            template_id=tid,
                            field_id=fid,
                            action=action,
                            data=_field_data,
                            fl_fields=fl_fields['data'],
                            userinfo=self.userinfo)
                # todo something
                # 构造一个字典输出给模板
                return
        else:
            _field = ModField(self.application)
            field_name = self.get_argument('name', '')
            field_type = self.get_argument('field_type', '')
            min_size = self.get_argument('minsize', '0')
            max_size = self.get_argument('maxsize', '0')
            fl_field = self.get_argument('fl_field', '')
            algorithm = self.get_argument('algorithm', '')
            default_value = self.get_argument('default_value', '')
            enable = self.get_argument('enable', 1)
            is_show = self.get_argument('isshow', 1)
            display_order = self.get_argument('order', 0)
            if action == 'add':
                data = _field.update(action, pid, template_id=tid, field_name=field_name, field_type=field_type,
                                     min=min_size, max=max_size, rule='', display_order=display_order,
                                     default_value=default_value, algorithm=algorithm, is_show=is_show, enable=enable,
                                     fl_field=fl_field)
                self.write(json.dumps(data))
            if action == 'update':
                data = _field.update(action, pid, field_id=fid, template_id=tid, field_name=field_name,
                                     field_type=field_type, min=min_size, max=max_size, rule='',
                                     display_order=display_order, default_value=default_value, algorithm=algorithm,
                                     is_show=is_show, enable=enable, fl_field=fl_field)
                self.write(json.dumps(data))
            pass
        pass

    def __list_components(self):
        """list all template for project

        列出当前项目下的所有组件
        Args:
        Returns:
            List[]
        """
        pid = int(self.get_argument('pid', 0))
        if pid == 0:
            self.write(json.dumps(Error.CGIREQUESTERR))
        _c = ModComponent(self.application)
        count, data = _c.get_component_list(pid)
        if count >= 0:
            self.render('admin_component_list.html', components=data, project_id=pid, userinfo=self.userinfo)
        else:
            self.write(json.dumps(data))
        pass

    def __update_component(self, action, isapi=False):
        """ add/update field

            创建/修改组件

            Argument:
            isapi:是否为操作接口，False为view，True为API操作
        """
        pid = int(self.get_argument('pid', 0))
        if isapi == False:
            cid = self.get_argument('cid', '0')
            _component = ModComponent(self.application)
            data = {'component_id': '', 'component_name': '', 'component_cname': '', 'component_summary': '',
                    'component_symbol': '', 'component_content': '', 'enable': 1}
            if cid != '0':
                data = _component.get_component_one(pid, int(cid))
                if data is None:
                    self.write(json.dumps(Error.DATANOTEXISTED))
                    return
            self.render('admin_component.html', data=data, action=action, project_id=pid, component_id=cid,
                        userinfo=self.userinfo)
            return
            pass
        else:
            pid = self.get_argument('pid', 0)
            cid = self.get_argument('cid', '0')
            name = self.get_argument('name', '')
            cname = self.get_argument('cname', '')
            summary = self.get_argument('summary', '')
            symbol = self.get_argument('symbol', '')
            content = self.get_argument('content', '')
            enable = self.get_argument('enable', '1')
            if name == '' or cname == '' or symbol == '' or content == '':
                self.write(json.dumps(Error.CGIREQUESTERR))
                return
            _component = ModComponent(self.application)
            _data = {'component_id': cid, 'component_name': name, 'component_cname': cname,
                     'component_summary': summary, 'component_symbol': symbol, 'component_content': content,
                     'enable': enable}
            recode = _component.update(action, pid, **_data)
            self.write(json.dumps(recode))
            pass
        pass

    def __list_variables(self):
        pass

    def __update_variable(self, action, isapi=False):
        pass

    def __create_batch_task(self):
        """start a batch publish task

        发起一个批量发布任务
        Args:
        Returns:
            taskid
        """
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        did_set = self.get_argument('did_set', '')
        task = ModTask(self.application)
        print('DIDSET', did_set)
        recode = task.async_batch_render(pid, tid, did_set)
        self.write(json.dumps(recode))
        return

    def __create_task(self):
        """start an async task

        发起一个异步任务

        Args:
        Returns:
            taskid
        """
        algorithm_type = self.get_argument('type', '')
        pid = int(self.get_argument('pid', 0))
        tid = int(self.get_argument('tid', 0))
        did = int(self.get_argument('did', 0))
        preview = self.get_argument('preview', 'N')

        logging.info("Type:" + algorithm_type)
        taskid = self.get_argument('taskid', '')
        task = ModTask(self.application)
        if taskid != '':
            # 报告任务状态
            recode = task.get_task_status(taskid)
            self.write(json.dumps(recode))
            return
        # 发起异步任务

        # 开放代码太多，不能用Tornado的异步协程，走系统子进程
        recode = task.async_render(algorithm_type, pid, tid, did, preview)
        # 通过返回值告知客户端执行中和执行完
        # code=200为执行成功 201为执行中 progress为进度 errmsg为输出信息
        # taskid为任务id
        self.write(json.dumps(recode))
        pass

    def __get_task_status(self):
        """get task status

        获取异步任务状态
        Returns:
            recode
        """
        single_taskid = self.get_argument('taskid', '')
        task_id = self.get_argument('batchid', '')
        task = ModTask(self.application)
        if task_id == '':
            recode = task.get_task_status(single_taskid)
        else:
            recode = task.get_batch_task_status(task_id)
        self.write(json.dumps(recode))
        return
