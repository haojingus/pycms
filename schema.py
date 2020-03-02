# coding=utf-8
import json
import copy
import re
import datetime
import logging
from error import Error
from common import Common


class Schema(object):
    webapp = None
    schema_config = []

    def __init__(self, webapp=None):
        self.__class__.webapp = webapp
        pass

    def load_schema(self):
        '''load auto execute schema

		加载自动执行的时间计划
		结构描述:
			main:[{'pid':pid,'schema':[{'tid':tid,'config':callback_context}]
			]
			callback_context:string类型的json，用于描述事件配置信息
		Changelog:
				上一个版本在config内包含了pid信息，本次修订忽略掉了pid节点，pid以load_schema遍历的pid为准。tid也以遍历结果为准
				新旧对比
				旧:[{"pid":"19","onTimer": [{"setting": "T5","action": "publish(19,33,1)"}]}]
				新:[{"onTimer":[{"setting":"T5","action":"publish_local(1,2,3,4...)"},{"setting":"T30","action":...}],"onPublish":[...]}]
				新增publish_local函数、publish_external函数
				函数描述：
						publish_local(int,int,int...) 发布当前模板下的多个did
						publish_external(pid,tid,did) 发布外部项目下的指定文档,等同于旧版的publish()
		Args:

		Returns:
				#加载后
				[{"pid":1,"schema":[{"tid":1,"config":{"onTimer":[],"onPublish":[]}},
									{"tid":2,"config":{"onTimer":[],"onPublish":[]}}
									...
								   ]},
				 {"pid":2,"schema":[{"tid":1,"config":{"onTimer":[],"onPublish":[]}},
									{"tid":2,"config":{"onTimer":[],"onPublish":[]}}
									...
								   ]}
				]

				pid tid会转为环境变量，did在runtime期间生成
		'''
        if self.webapp is None:
            return {}

        schema_config = []
        for item in self.webapp.cfg['db']:
            # print self.webapp.cfg['db']
            if item['pid'] != 0:
                sql = "select `template_id`,`publish_callback` from `cms_template` where `enable`=1 and `publish_callback`<>''"
                n, data = self.webapp.db.executeQuery(item['pid'], sql)
                if n < 0:
                    return data
                _schema = []
                for row in data:
                    _schema.append({'tid': row[0], 'config': json.loads(row[1])})
                schema_config.append({'pid': item['pid'], 'schema': _schema})
        pass
        self.schema_config = self.__compile_schema(schema_config)

    # print '#############',self.schema_config

    def __compile_schema(self, schema_cfg):
        """convert schema config
		
		编译callback配置,按照事件来区分，把相同事件和配置的回调合并，统一处理
		结构描述：
			旧：
			[
			{'pid':pid,'onTimer:[{'setting':'****-**-** **:**','action':'publish(1,1 ,1)'}]'
					'onPublish':[{'setting':'','action':'publish(1,1,1)'},.....]
			}
			]
			新：
			[{"onTimer":[
				{"setting":"T5","action":"publish_local(1,2,3,4...)"},
				{"setting":"T30","action":"publish_external(19,12,31)"}],
			  "onPublish":[
				{"setting":"{$did}==1","action":"publish_external(19,12,31)"},
				{"setting":"{$did}==2","action":"publish_external(19,12,32)"}]
			 }
			]
			说明：事件函数存在CMS私有环境变量，主要为pid,tid,did。引用格式为{$pid}...

		Args:
			schema_cfg:callback config<list>

		Return:
			{"onTimer":
				[{"setting":"T5","callback":[
						{"env":{"pid":1,"tid":1},"action":"publish_local(1,2,3,4,5,6,7...)"},
						{"env":{"pid":1,"tid":2},"action":"publish_local(1,2,3,4,5,6,7...)"}
						]},
				{"setting":"T10","callback":[
						{"env":{"pid":1,"tid":1},"action":"publish_local(1,2,3,4,5,6,7...)"},
						{"env":{"pid":1,"tid":2},"action":"publish_local(1,2,3,4,5,6,7...)"}
						]}
				]
			 ,
			 "onPublish":
				[{"setting":"{$pid}==1 and {$tid}==1 and {$did}==1","callback":[
						{"action":"publish_external(1,2,3)"},
						{"action":"publish_external(1,2,4)"}
						]},
				{"setting":"{$pid}==1 and {$tid}==1 and {$did}==2","callback":[
						{"action":"publish_external(1,2,3)"},
						{"action":"publish_external(1,2,4)"}
						]}
				]
			,
			"onOtherEvent":....
			
			注意：回调发生时需要传递环境变量pid tid did，否则无法获取相关参数.
		"""
        compile_result = {'onTimer': [], 'onPublish': []}
        for proj in schema_cfg:
            # _proj_event = {'onTimer':[],'onPublish':[]}
            _env_pid = proj['pid']
            for callback in proj['schema']:
                _env_tid = callback['tid']
                # callback的key为tid、config，后者为入库内容
                for event in callback['config']:
                    # print 'EVENT',event
                    for k, v in event.items():
                        # k为事件名，v为事件描述，包括setting/action
                        # 校验事件和事件配置
                        if self.__vaild(k, v):
                            # print "DEBUG====>",callback
                            # 遍历各种setting
                            for _setting in v:
                                if type(_setting) is dict and 'setting' in _setting:
                                    _target_setting = Common.collection_find(compile_result[k],
                                                                             lambda s: s['setting'] == _setting[
                                                                                 'setting'])
                                    if _target_setting is None:
                                        # print '@@',compile_result[k],'$$',_setting
                                        compile_result[k].append({"setting": _setting['setting'], "callback": [
                                            {"env": {"pid": _env_pid, "tid": _env_tid}, "action": _setting['action']}],
                                                                  "last_call": datetime.datetime.now()})
                                    else:
                                        _target_setting['callback'].append(
                                            {"env": {"pid": _env_pid, "tid": _env_tid}, "action": _setting['action']})
                                        _target_setting['last_call'] = datetime.datetime.now()
                                    pass
                                else:
                                    logging.warning("Error callback:" + str(_setting))

                        # v['tid'] = callback['tid']
                        # v['last_call'] = datetime.datetime.now()
                        # _proj_event[k].append(v)
                        else:
                            logging.warning('callback schema config error:' + str(v))
                    pass
                pass
            pass
        # compile_result.append(_proj_event)
        pass
        return compile_result

    def __vaild(self, event, callback_cfg):
        '''check callback config
		检查事件配置合法性
		
		Args:

		'''
        # print 'EVENT',event
        # print 'CALLBACK_CFG',callback_cfg
        if event == 'onTimer':
            # print 'DEBUG====>',callback_cfg,type(callback_cfg)
            if type(callback_cfg) == dict:
                callback_cfg = [callback_cfg]
            for _cfg in callback_cfg:
                if self.func_parse(_cfg['action']) is None:
                    logging.warning('func_parse error' + str(_cfg))
                    return False
                if self.cyc_format(_cfg['setting'])['code'] != 0:
                    logging.warning('cyc_format err' + str(_cfg))
                    return False

            print('EVENT', event)
            print('CALLBACK_CFG', callback_cfg)
            return True
        if event == 'onPublish':
            return True

    @staticmethod
    def func_parse(code):
        pattern = re.compile(r"(^\w+)(\()([^\)]*)(\)$)")
        m = pattern.match(code)
        match = m.groups()
        if match is None:
            return None
        else:
            return {'func_name': match[0], 'params': match[2].replace(' ', '')}

    @staticmethod
    def cyc_format(cyc_setting):
        if Common.filter_digit(cyc_setting[1:]) == cyc_setting[1:]:
            # 读秒周期
            recode = copy.deepcopy(Error.SUCC)
            recode['data'] = {'cyc_type': 'CYC', 'value': int(cyc_setting[1:])}
            return recode
        else:
            # 定时器
            pattern = re.compile(r"^D[\*|\d]{4}-[\*|\d]{2}-[\*|\d]{2}\s{1}[\*|\d]{2}:[\*|\d]{2}$")
            if len(pattern.findall(cyc_setting)) != 1:
                logging.warning('cyc err:' + cyc_setting)
                return Error.DATAFORMATERR
            else:
                timer_serial = [cyc_setting[3:5], cyc_setting[6:8], cyc_setting[9:11], cyc_setting[12:14],
                                cyc_setting[15:17]]
                _find = False
                for i in range(0, len(timer_serial)):
                    if _find == True and Common.filter_digit(timer_serial[i]) != timer_serial[i]:
                        return Error.DATAFORMATERR
                    _find = True if timer_serial[i] != '**' else False
                if not _find:
                    return Error.DATAFORMATERR
                # 构建定时字典
                data = {'cyc_type': 'TIMING',
                        'Y': timer_serial[0],
                        'm': timer_serial[1],
                        'd': timer_serial[2],
                        'H': timer_serial[3],
                        'M': timer_serial[4]
                        }
                recode = copy.deepcopy(Error.SUCC)
                recode['data'] = data
                return recode
        pass

    @staticmethod
    def check_timer(last_time, curent_time, cyc_setting):
        cyc = Schema.cyc_format(cyc_setting)
        # 校验一次
        if cyc['code'] != 0:
            return False
        if cyc['data']['cyc_type'] == 'CYC':
            # 周期类型
            return cyc['data']['value'] < (curent_time - last_time).seconds
        else:
            # 定时类型
            # 60秒用于过滤重复执行
            if (curent_time - last_time).seconds <= 60:
                return False
            recode = False
            if int(cyc['data']['M']) == curent_time.minute:
                if cyc['data']['H'] == '**':
                    return True
                elif int(cyc['data']['H']) == curent_time.hour:
                    if cyc['data']['d'] == '**':
                        return True
                    elif int(cyc['data']['d']) == curent_time.day:
                        if cyc['data']['m'] == '**':
                            return True
                        elif int(cyc['data']['m']) == curent_time.month:
                            if cyc['data']['Y'] == '**':
                                return True
                            elif int(cyc['data']['Y']) == curent_time.year:
                                return True
                            else:
                                return False
            return False

    @staticmethod
    def env_encode(env):
        _env = []
        for (k, v) in env.items():
            _env.append(k + ':' + str(v))
        return '##'.join(_env)

    @staticmethod
    def env_decode(env):
        _env = env.split("##")
        _ret = {}
        for _item in _env:
            _kv = _item.split(':')
            if len(_kv) == 2:
                _ret[_kv[0]] = _kv[1]
        return _ret
