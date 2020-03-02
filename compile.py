#!/usr/local/bin/python3
# coding=utf8
import time
import sys
import redis
import json
import logging
import re
import os
import subprocess
import datetime
# import importlib

# importlib.reload(sys)


from error import Error
from common import Common
from dbmanager import DbManager
from plugins.fieldtype.algorithm import Algorithm

logging.info('[Compiler]:Task Start')


def render(algorithm_type, **kwargv):
    """rend field by algorithm
	"""
    global redis
    pid = kwargv['project_id']
    tid = kwargv['template_id']
    fid = kwargv['field_id']
    field_type = kwargv['field_type']
    field_algorithm = kwargv['field_algorithm']
    data_key = kwargv['data_key']
    if 'field_value' in kwargv:
        field_value = kwargv['field_value']
    else:
        field_value = ''

    algorithm_type = 'script' if algorithm_type == 'script' else 'input'
    logging.info('[Compiler]: start render')
    # print "Source Code:",field_algorithm
    _algorithm = Algorithm.parse_algorithm(field_algorithm)
    # print "ALGORITHM:",_algorithm
    lang_cfg = Common.collection_find(kwargv['lang_cfg'], lambda s: s['lang'] == _algorithm[algorithm_type]['lang'])
    cms_assert((lang_cfg is None and _algorithm[algorithm_type]['lang'] != 'raw'), 500,
               'not support ' + _algorithm[algorithm_type]['lang'])
    if _algorithm[algorithm_type]['lang'] == 'raw':
        # 判断算法类型，input则只读取raw配套的data，script则需要优先使用raw，如raw配套为空，则使用用户数据field_value
        if _algorithm[algorithm_type]['data'].strip() != '':
            print('===>',_algorithm[algorithm_type]['data'],'<====')
            logging.warning('=====>INPUT RAW DATA<======'+str(_algorithm[algorithm_type]['data']))
            return _algorithm[algorithm_type]['data']
        elif algorithm_type == 'script':
            return field_value
        else:
            return ''
    root = os.path.split(os.path.realpath(__file__))[0]
    cmd = lang_cfg['cfg']['run'].replace('{$root}', root)
    cmd = cmd.replace('%1', data_key)
    logging.info('[Compiler]:CMD**' + cmd)
    # 构建算法文件input类型前缀为developer_ script类型前缀为user_
    # prefix = 'user_' if algorithm_type=='script' else 'devloper_'
    prefix = algorithm_type + '_'
    path = root + '/plugins/script/' + lang_cfg['lang'] + '/usr/' + prefix + str(pid) + '_' + str(tid) + '_' + str(
        fid) + '.' + lang_cfg['cfg']['extname']
    logging.info('[Compiler]: ALGOR PATH:' + path)
    algo = Algorithm()
    _ready = False
    if os.path.exists(path):
        fp = open(path, 'r')
        _code = fp.read()
        fp.close()
        target_hash = Common.md5(_code)
        source_hash = Common.md5(_algorithm[algorithm_type]['data'])
        # print target_hash,source_hash
        if target_hash == source_hash:
            _ready = True
        # __out = algo.execute(cmd)
        # logging.info('[Compiler]:'+__out)
        # logging.info('[Compiler]:end render')
        # return __out
    if not _ready:
        fp = open(path, 'w')
        fp.write(_algorithm[algorithm_type]['data'])
        fp.close()
        _ready = True
    logging.info('[Compiler]:end render')
    _out = algo.execute(cmd)
    cms_assert(_out == 'algorithm time out', 500, 'algorith time out!!!')
    # 解析算法stdio输出结果，注意渲染结果和错误信息均在share memory中，stdio只有对应的key值
    # 解析错误信息
    _p = re.compile(r"\[CMSERRKEY=.*?\]")
    _errkey = _p.findall(_out)
    if len(_errkey) >= 1:
        _script_errinfo = json.loads(redis.get(_errkey[0].replace('[CMSERRKEY=', '').replace(']', '')))
        cms_assert(_script_errinfo['errcode'] == Error.ALGORITHMABORT['code'], 500,
                   Error.ALGORITHMABORT['errmsg'] + " Detail:" + _script_errinfo['errmsg'])

    # 解析渲染结果信息
    _p = re.compile(r"\[CMSDATAKEY=.*?\]")
    _key = _p.findall(_out)
    # print '@@@@@@@@@',_key
    if len(_key) == 1:
        return redis.get(_key[0].replace('[CMSDATAKEY=', '').replace(']', ''))
    else:
        return _out


# logging.info('[Compiler]:'+_out)
# return _out


def sql_convert(cms_sql):
    global db
    global pid
    global redis
    # 加载系统模板域
    cms_assert(not redis.exists('system_fields'), 500, 'system config can not find!!!')
    system_fields = json.loads(redis.get('system_fields'))
    pattern = re.compile(r"\{#.*?\}")
    m = pattern.findall(cms_sql)
    cms_assert(len(m) == 0, 500, 'sql error,sql:' + cms_sql)
    tbl = m[0]
    tbl = tbl[2:len(tbl) - 1]
    cms_assert(len(tbl) == 0, 500, 'tblname is empty')
    # 开始获取模板id
    pattern = re.compile(r"cms_tbl_\d+")
    if len(pattern.findall(tbl)) == 0:
        _sql = "select template_id,template_name from cms_template where template_name='" + tbl + "'"
        n, data = db.executeQuery(pid, _sql)
        cms_assert(n < 1, 500, "can't find template.tname:" + tbl + " SQL:" + _sql)
        cms_sql = cms_sql.replace('{#' + tbl + '}', 'cms_tbl_' + str(data[0][0]))
        tbl = 'cms_tbl_' + str(data[0][0])
    else:
        cms_sql = cms_sql.replace('{#' + tbl + '}', tbl)
    pass
    cms_sql_tid = filter(str.isdigit, tbl)
    # 只获取enable=1的模板域
    _sql = 'select field_id,field_name from cms_template_field where `enable`=1 and template_id=' + cms_sql_tid
    n, data = db.executeQuery(pid, _sql)
    cms_assert(n < 1, 500, 'can not find field info')
    # 开始替换用户字段
    for cms_sql_field in data:
        cms_sql = cms_sql.replace('{$' + cms_sql_field[1] + '}', 'sp_' + str(cms_sql_field[0]))
    logging.info('[C-SQL]:' + cms_sql)
    # 开始替换系统字段
    for cms_sql_field in system_fields:
        logging.info('[Compiler]:Start replace system field')
        logging.info('[Compiler]: ' + cms_sql_field['name'])
        _real_field = cms_sql_field['name'].replace('{$', '').replace('}', '')
        cms_sql = cms_sql.replace(cms_sql_field['name'], _real_field).replace(cms_sql_field['cname'], _real_field)
    return cms_sql


def cms_assert(boolexp, code, msg):
    global redis
    global timeout
    global task_id
    global db
    global pid
    if boolexp:
        redis.setex(task_id, timeout, json.dumps([{'code': 500, 'errmsg': msg}]))
        if (db is not None) and pid != '':
            db.closeConn([pid])
        logging.warning('CODE:' + str(code) + ' MSG:' + msg)
        # print code,msg
        exit(1)
    return


#################
# Main entry point
#################
if len(sys.argv) != 2:
    logging.warning("param count is error!")
    exit(1)

timeout = 30
db = None
pid = ''
task_id = sys.argv[1]
# algorith_type = task_id.split('_')[0]
logging.info('[Compiler]: TaskID = ' + str(task_id))
# 初始化配置
# 暂时不做超时报警
cfg = Common.loadConfig()
redis = redis.Redis(host=cfg['redis']['host'], port=cfg['redis']['port'], db=1)
# 加载语言配置

# 断言语言是否支持
cms_assert(not redis.exists('lang'), 500, 'lang config miss')
lang_cfg = json.loads(str(redis.get('lang'),encoding='utf-8'))
project_cfg = json.loads(str(redis.get('project_config'),encoding='utf-8'))
system_fields_cfg = json.loads(str(redis.get('system_fields'),encoding='utf-8'))
logging.info('[Compiler]:lang load ok!')
# 断言任务id是否存在
cms_assert(not redis.exists(task_id), 404, "can't find taskid")

task_mail = json.loads(str(redis.get(task_id),encoding='utf-8'))
header_mail = task_mail[0]

print('continue-1', header_mail)
logging.info('[Compiler]:continue-1')

# 头部信息必须是201才可以进行队列操作
if header_mail['code'] != 201:
    logging.warning('header code err')
    print('mail header err', header_mail)
    exit(1)

print('continue-2')

# 获取任务信息
algorithm_type = header_mail['tag']
pid = header_mail['pid']
tid = header_mail['tid']
did = header_mail['did']
smid = header_mail['smid']
curent_user = header_mail['user']
preview = header_mail['preview']

# logging.info(str(cfg['db']))
logging.info(str(pid) + " ready!")
db_cfg = Common.collection_find(cfg['db'], lambda s: s['pid'] == int(pid))

print(header_mail)
logging.info('DB:' + str(db_cfg))
cms_assert(db_cfg is None, 404, "can't find db cfg")
db = DbManager()
db.initConn([db_cfg])

pid = str(pid)
proj = Common.collection_find(project_cfg, lambda s: s['pid'] == int(pid))
cms_assert((proj is None and preview == 'N'), 404, "can't find publish domain,please check cfg")
domain = proj['domain']

# 获取模板信息
sql = "select `template_view`,`publish_callback`,`publish_url` from `cms_template` where `template_id`=" + str(tid)
n, data = db.executeQuery(pid, sql)

# 断言模板视图是否存在
cms_assert(n < 1, 404, "can't find template info")

template_view = data[0][0]
publish_url = data[0][2]

# 获取模板域信息
tbl_name = "cms_tbl_" + str(tid)
sql = "select `field_id`,`field_name`,`field_type`,`min_size`,`max_size`,`algorithm`,`default_value` from `cms_template_field` where `template_id`=" + str(
    tid) + " and `enable`=1 order by `display_order` asc"
field_count, data = db.executeQuery(pid, sql)

print('continue-3')
logging.info('[Compiler]:continue-3')
# 断言tid空值
cms_assert(field_count < 1, 404, "field can't be found")

fields = []
for row in data:
    fields.append('`sp_' + str(row[0]) + "`")

doc_detail = {}
doc_data = []
if algorithm_type == 'script':
    exp = ",".join(fields)
    sql = "select " + exp + ",`create_time`,IFNULL(`publish_url`,''),`create_user` from `" + tbl_name + "` where `document_id`=" + str(
        did)
    n, doc_data = db.executeQuery(pid, sql)
    # 断言did空值
    cms_assert(n < 1, 404, "document can't be found.pid:" + str(pid) + " did:" + str(did) + " tbl_name is " + tbl_name)
    doc_detail = {'create_user': doc_data[0][len(doc_data[0]) - 1], 'create_time': doc_data[0][len(doc_data[0]) - 3]}
    pass
    publish_url = publish_url if len(doc_data[0][len(doc_data[0]) - 2]) == 0 else doc_data[0][len(doc_data[0]) - 2]
print('continue-4', sql, algorithm_type)
logging.info('[Compiler]:continue-4=' + sql)
# db.closeConn([pid])

# 加载插件语言配置模板,未做键值检查
language_config = json.loads(str(redis.get('lang'), encoding='utf-8'))
# 开始进入渲染队列
render_result = []
algor = Algorithm()
task_mail.append({'code': 201, 'errmsg': u'开始执行渲染队列', 'progress': 0})
redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))

print('continue-5')
logging.info('[Compiler]:continue-5')

for i in range(0, field_count):
    field_id = data[i][0]
    field_name = data[i][1]
    field_type = data[i][2]
    field_algorithm = data[i][5]

    # 用于输出渲染的script类型需要field_value，input不需要
    if algorithm_type == 'script':
        field_value = data[i][6] if doc_data[0][i] == '' else doc_data[0][i]
    else:
        field_value = ''
    pass

    # 进度写入邮箱
    task_mail.append({'code': 201, 'errmsg': field_name + '[sp_' + str(field_id) + u'] 开始渲染!',
                      'progress': int(float(i) / float(field_count) * 100.0)})
    redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))

    # 循环渲染各模板域
    _algorithm = Algorithm.parse_algorithm(field_algorithm.replace('\r\n', '\n'))
    print('C-SQL:')
    print(_algorithm['sql'][algorithm_type])
    logging.info('[Compiler]:C-SQL' + str(_algorithm['sql'][algorithm_type]))
    # 开始构建模板域输入数据源
    sql_result = {}
    for _sql in _algorithm['sql'][algorithm_type]:
        # 解析script内的sql，构建用户数据源
        _field_sql = sql_convert(_sql['sql'])
        # 执行sql
        n, _data = db.executeQuery(pid, _field_sql)
        cms_assert(n < 0, 500, 'cms sql execute failed!' + _field_sql)
        # 合并sql结果集
        sql_result[_sql['variable']] = _data
    pass

    # script类型需要注入用户数据，key为$input
    if algorithm_type == 'script':
        sql_result['$input'] = field_value
    # 写入tid pid fid
    sql_result['$pid'] = pid
    sql_result['$tid'] = tid
    sql_result['$did'] = did
    sql_result['$fid'] = field_id
    sql_result['$type'] = algorithm_type
    sql_result['$debug'] = render_result
    # print sql_result
    logging.info('[Compiler]: merge result into cmsapp')

    # sql结果导入cmsapp.x，子进程运行cmsapp，cmsapp调用field算法脚本，结果集的key为 taskid_fieldid,生存期5秒
    _data_key = task_id + "_" + str(field_id)
    redis.setex(_data_key, timeout, json.dumps(sql_result, ensure_ascii=False))
    # 执行脚本，进行渲染

    # 获取cmsapp结果，完成本次渲染
    _render_result = render(algorithm_type, project_id=pid,
                            template_id=tid,
                            field_id=field_id,
                            field_type=field_type,
                            field_algorithm=field_algorithm,
                            field_value=field_value,
                            lang_cfg=lang_cfg,
                            data_key=_data_key
                            )
    if type(_render_result) is bytes:
        _render_result = str(_render_result, encoding='utf-8')
    if _render_result is None:
        _render_result = ''
    # 模板域渲染结束
    logging.info('[Compiler]: TRACE Render END')
    render_result.append(
        {'field_id': str(field_id), 'field_name': field_name, 'result': _render_result})
    task_mail.append({'code': 201, 'errmsg': field_name + '[sp_' + str(field_id) + u'] 渲染完成!',
                      'progress': int(float(i + 1) / float(field_count) * 100.0)})
    redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))
pass

if algorithm_type == 'input':
    # task_mail.append(
    #    {'code': 200, 'errmsg': u'渲染完成!', 'progress': 100, 'result': json.dumps(render_result, ensure_ascii=False)})
    task_mail.append({'code': 200, 'errmsg': u'渲染完成!', 'progress': 100, 'result': render_result})
    redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))
    # 写状态机，让任务完成，解锁该任务
    redis.setex(smid, timeout, json.dumps({'status': 'finished', 'msg': 'rend ok ', 'taskid': task_id}))
    logging.info('[Compiler]: render finished')
    logging.info('[Compiler]:' + str(render_result))
    exit(0)
pass

# 输出模板任务需要有后续过程
task_mail.append({'code': 201, 'errmsg': u'渲染完成!', 'progress': 100})
redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))

# 合并各模板域渲染结果到html，构建模板页面
for _content in render_result:
    template_view = template_view.replace("{$sp_" + _content['field_id'] + "}", _content['result'])
    template_view = template_view.replace("{$" + _content['field_name'] + "}", _content['result'])

logging.info('[Compiler]: start component')
# 项目组件渲染Component
sql = "select `component_symbol`,`component_content` from `cms_component` where `enable`=1"
n, component_data = db.executeQuery(pid, sql)
cms_assert(n < 0, 500, 'get component error!' + sql)
for _component in component_data:
    template_view = template_view.replace(_component[0], _component[1])

# 模板主页面变量渲染
for sysvar in system_fields_cfg:
    # print sysvar['cname'],sysvar['name']
    template_view = template_view.replace(sysvar['cname'], sysvar['name'])

# template_view = template_view.replace(u"{$文档编号}",str(did))
template_view = template_view.replace("{$document_id}", str(did))
template_view = template_view.replace("{$template_id}", str(tid))
template_view = template_view.replace("{$project_id}", str(pid))
template_view = template_view.replace("{$create_user}", str(doc_detail['create_user']))
template_view = template_view.replace("{$create_time}", str(doc_detail['create_time']))
template_view = template_view.replace("{$publish_user}", curent_user)
template_view = template_view.replace("{$publish_time}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# 处理url
_now = time.localtime(time.time())
publish_url = publish_url.replace('{$did}', str(did)).replace('{$pid}', str(pid)).replace('{$tid}', str(tid))
publish_url = publish_url.replace('{$Y}', str(_now.tm_year)).replace('{$m}', str(_now.tm_mon)).replace('{$d}', str(
    _now.tm_mday))
publish_url = publish_url.replace('{$H}', str(_now.tm_hour)).replace('{$M}', str(_now.tm_min)).replace('{$S}',
                                                                                                       str(_now.tm_sec))

if preview == 'Y':
    publish_url = publish_url.replace(publish_url[publish_url.rfind('.')::],
                                      '_preview' + publish_url[publish_url.rfind('.')::])
target_path = './site/' + str(pid) + publish_url
_dir = target_path[0:target_path.rfind('/')]
if not os.path.exists(_dir):
    os.makedirs(_dir)
fp = open(target_path, 'w')
# 添加cms注释
ext_name = '' if target_path.rfind('.') < 0 else target_path[target_path.rfind('.'):]
note = "\n<!--build by cms at " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "-->" if ext_name in (
    '.html', '.shtml', 'htm', 'shtm') else ''
fp.write(template_view + note)
fp.close()
logging.info('[Compiler]: create html succ,url:' + publish_url)

if preview == 'N':
    # 回写document记录
    sql = "update `cms_tbl_{$tid}` set `publish_time`=now(),`publish_user`='{$user}',`publish_url`='{$publish_url}' where document_id=" + str(
        did)
    sql = sql.replace('{$tid}', str(tid)).replace('{$user}', curent_user).replace('{$publish_url}', publish_url)
    n, data = db.execute(pid, sql)
    pass
    # 断言更新文档是否成功
    cms_assert(n < 1, 500, 'build template view error!' + sql)
pass
make_page_code = 201 if preview == 'N' else 200
# 更新邮箱
task_mail.append({'code': make_page_code, 'errmsg': u'生成模板页面成功!', 'progress': 100, 'pid': str(pid), 'url': publish_url})
redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))

logging.info('[Compiler]: document update ok')
# 数据库关闭
db.closeConn([pid])

if preview == 'N':
    # rsync到目标站点
    logging.info('sh ./shell/test.domain.sh ' + domain + ' ' + str(pid) + ' ' + publish_url[1:])
    child = subprocess.Popen(['sh ./shell/test.domain.sh ' + domain + ' ' + str(pid) + ' ' + publish_url[1:]],
                             shell=True)
    child.wait()
    task_mail.append({'code': 200, 'errmsg': u'发布到目标站点完成!', 'progress': 100, 'pid': str(pid), 'url': publish_url})
    redis.setex(task_id, timeout, json.dumps(task_mail, ensure_ascii=False))

# 写状态机，让任务完成，解锁该任务
redis.setex(smid, timeout, json.dumps({'status': 'finished', 'msg': 'rend ok ', 'taskid': task_id}))
