# coding=utf-8
from PIL import Image
import os
import sys
import glob
import time
import hashlib
import logging
import json
import re
import pymysql
import logging
import math
import copy


class Common:

    @staticmethod
    def makeThumb(path, thumb_path, size):
        """生成缩略图"""
        img = Image.open(path)
        width, height = img.size
        # 裁剪图片成正方形
        if width > height:
            delta = (width - height) / 2
            box = (delta, 0, width - delta, height)
            region = img.crop(box)
        elif height > width:
            delta = (height - width) / 2
            box = (0, delta, width, height - delta)
            region = img.crop(box)
        else:
            region = img

        # 缩放
        thumb = region.resize((size, size), Image.ANTIALIAS)
        base, ext = os.path.splitext(os.path.basename(path))
        filename = os.path.join(thumb_path, '%s_thumb_%s%s' % (base, str(size), ext))
        # print filename
        # 保存
        thumb.save(filename, quality=70)

    @staticmethod
    def makePage(count, pagesize, pageindex, url):
        print("Count:", count, pagesize)
        maxPageNum = 5
        pageInfo = {}
        if pageindex == 1:
            pageInfo['prePage'] = url + '#'
        else:
            pageInfo['prePage'] = url + '?page=' + str(pageindex - 1)
        if pageindex >= (count / pagesize) + 1 or ((count % pagesize == 0) and pageindex == count / pagesize):
            pageInfo['nextPage'] = url + '#'
        else:
            pageInfo['nextPage'] = url + '?page=' + str(pageindex + 1)
        pageInfo['data'] = []
        totalPage = (count / pagesize) + 1
        if totalPage <= maxPageNum:
            for i in range(1, totalPage + 1):
                pageInfo['data'].append(i)
        else:
            start = pageindex
            end = pageindex
            if pageindex <= maxPageNum / 2 + 1:
                start = 1
                end = totalPage if totalPage <= maxPageNum else maxPageNum
            else:
                start = pageindex
                end = pageindex + maxPageNum if totalPage >= pageindex + maxPageNum else totalPage

            if pageindex + maxPageNum / 2 + 1 > totalPage:
                start = totalPage - maxPageNum if totalPage >= maxPageNum else 1
                end = totalPage
            else:
                start = pageindex - maxPageNum / 2 - 1 if pageindex - maxPageNum >= 1 else 1
                end = pageindex + maxPageNum / 2 + 1
            print(start, end)
            for i in range(start, end + 1):
                pageInfo['data'].append(i)
        return pageInfo

    @staticmethod
    def md5(source):
        m2 = hashlib.md5()
        m2.update(source.encode("utf8"))
        return m2.hexdigest()

    @staticmethod
    def loadConfig():
        '''load system config.

		加载系统配置和用户配置
		Args:
		Return:配置词典{'redis':...'system':....'userdb':....}
		'''
        pass

        config = None
        '''加载系统配置'''
        try:
            with open('./conf/config.json', 'r') as f:
                config = json.load(f)
        except Exception as e:
            logging.warning(str(e))
            exit(1)

        '''构建数据库配置'''
        config['db'] = [config['system']]

        '''加载用户配置'''
        try:
            with open('./conf/userdb.json', 'r') as f:
                userdb = json.load(f)
                config['db'].extend(userdb)
        except Exception as e1:
            logging.warning(str(e1))

        # logging.info(str(config))
        return config

    @staticmethod
    def loadSql(resource):
        """load sql file

		加载SQL文件
		Args:
		Returns:Sql内容
		"""
        pass

        sql = ""
        try:
            with open('./sql/' + resource, 'r') as f:
                sql = f.read()
        except Exception as e:
            logging.warning(str(e))
        return sql

    @staticmethod
    def make_publish_key(pid, tid, did):
        return "_".join([str(pid), str(tid), str(did)])

    @staticmethod
    def collection_find(source, func):
        """collection find,need lambda
		"""
        for item in source:
            if func(item):
                return item
        return None

    @staticmethod
    def get_file_content(path, **kwargv):
        if not os.path.exists(path):
            if 'default' in kwargv:
                return kwargv['default']
            return None

        try:
            fp = open(path, 'r')
            if 'json' in kwargv and kwargv['json'] == True:
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

    @staticmethod
    def exp_render(source, data):
        if not isinstance(data, dict):
            logging.warning('render string failed,data is None,source:' + source)
            return source
        p = re.compile(r"(\{\$)(\w+)(\})")
        arr = p.findall(source)
        for s in arr:
            if s[1] in data:
                source = source.replace("{$" + s[1] + "}", pymysql.escape_string(str(data[s[1]])))
        pass
        return source

    @staticmethod
    def make_page(data_count, page_index, page_size, display_range=9):
        page_count = math.ceil(data_count / page_size if data_count % page_size == 0 else data_count / page_size + 1)
        page_info = {}
        page_info['curent'] = page_index
        page_info['prePage'] = '#' if page_index == 1 else str(page_index - 1)
        page_info['nextPage'] = '#' if page_index >= page_count else str(page_index + 1)
        page_info['data'] = None
        if page_count <= display_range:
            # 处理页数不足的情况
            page_info['data'] = range(1, page_count + 1)
        else:
            if page_index <= display_range / 2:
                page_info['data'] = range(1, display_range + 1)
            elif page_index + display_range / 2 <= page_count:
                page_info['data'] = range(page_index - display_range / 2, page_index + display_range / 2 + 1)
            else:
                page_info['data'] = range(page_count - display_range + 1, page_count + 1)
        return page_info

    @staticmethod
    def js_encode(code):
        return code.replace('\r', '')

    @staticmethod
    def filter_digit(s):
        p = '[^\d]*'
        return re.sub(p, '', s)
