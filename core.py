# coding=utf-8
import os
import json
import copy
import logging
import re
from error import Error
from common import Common


class Core(object):
    field_type_config = []
    language_config = []
    env = {}

    def __init__(self):
        self.reload()

    def reload(self):
        """init Core Class
		"""

        # 加载模板域类型插件
        path = './plugins/fieldtype'
        files = os.listdir(path)
        plugins = []
        for f in files:
            if os.path.isdir(path + '/' + f):
                plugin_cfg = {}
                plugin_files = os.listdir(path + '/' + f)
                if 'config.json' in plugin_files:
                    _path = path + '/' + f + '/config.json'
                    content = Common.get_file_content(_path, json=True)
                    plugin_cfg = copy.deepcopy(content)
                    if (content is not None) and content['type'] == 'input':
                        plugin_cfg['html'] = Common.get_file_content(path + '/' + f + '/form.html', default='')
                        plugin_cfg['css'] = Common.get_file_content(path + '/' + f + '/form.css', default='')
                        plugin_cfg['js'] = Common.get_file_content(path + '/' + f + '/form.js', default='')
                        plugin_cfg['submit'] = Common.get_file_content(path + '/' + f + '/form_submit.js', default='')
                    plugins.append(plugin_cfg)
        self.field_type_config = plugins
        self.field_type_config = sorted(self.field_type_config, key=lambda f: f['order'])
        # print self.field_type_config
        # 加载语言插件
        _language = os.listdir('./plugins/script')
        # print _language
        for lang in _language:
            _path = './plugins/script/' + lang + '/config.json'
            if os.path.exists(_path):
                try:
                    fp = open(_path, 'r')
                    self.language_config.append({'lang': lang, 'cfg': json.load(fp)})
                    print(lang + ' cfg loaded')
                except:
                    print(lang + ' cfg err')
                    pass
                pass
            else:
                print('lang' + lang + ' cfg not exists')

    # 检查各语言SDK完整性和编译环境

    def __get_file_content(self, path, **kwargv):
        if not os.path.exists(path):
            if 'default' in kwargv:
                return kwargv['default']
            return None

        try:
            fp = open(path, 'r')
            if 'json' in kwargv and kwargv['json'] is True:
                content = json.load(fp)
                fp.close()
                return content
            else:
                content = fp.read()
                return content
        except Exception as e:
            if 'default' in kwargv:
                return kwargv['default']
            return None

    def get_all(self):
        return self.field_type_config

    def get_field_types(self, ftype=''):
        """get all field types

		获取所有模板域类型
		
		Args:
		Returns:
			List
		"""
        pass
        types = []
        for field in self.field_type_config:
            _t = {'field_type': field['field_type'], 'cname': field['cname'],
                  'selected': True if field['field_type'] == ftype else False}
            types.append(_t)
        return types

    def get_field_detail(self, field_type):
        """get field config detail

		获取指定模板类型的详细配置

		Args:
			field_type:模板域类型 user:xxx
		Returns:
			dict
		"""

        for field in self.field_type_config:
            if field['field_type'] == field_type:
                return field
        return None

    def field_type_existed(self, field_type):
        """check field type existed

		检查模板域是否可用

		Args:
			field_type:模板域

		Returns:
			Boolean
		"""
        for field in self.field_type_config:
            if field['field_type'] == field_type:
                return True
        return False

    def set_env(self, key, value):
        """set enviroment variable

		设置系统环境变量

		Args:
			key
			value

		Returns:
			void
		"""
        self.env[key] = value
        print(self.env)
        return
