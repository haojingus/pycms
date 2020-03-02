# coding=utf-8
import time
import subprocess
import re
import hashlib
import logging
import fcntl
import os


class Algorithm(object):

    def __init__(self):
        pass

    def __read_std(self, output):
        fd = output.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        try:
            return output.read()
        except Exception as e:
            return ''

    def execute(self, cmd, timeout=10000):
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, close_fds=True)
        """
		try:
			outs, errs = p.communicate()
			return outs+errs
		except Exception,e:
			p.kill()
			outs, errs = p.communicate()
			logging.warning(errs+str(e))
			return outs+errs
		"""
        t_begin = int(round(time.time() * 1000))
        passed = 0
        logging.info('[Compiler]:Start Time:' + str(int(round(time.time() * 1000))))
        err = ''
        out = ''
        while True:
            time.sleep(0.1)
            _err = self.__read_std(p.stderr)
            _out = self.__read_std(p.stdout)
            err = err + "" if _err is None else str(_err, encoding="utf-8")
            out = out + "" if _out is None else str(_out, encoding="utf-8")
            if p.poll() is not None:
                break
            passed = int(round(time.time() * 1000)) - t_begin
            if timeout and passed > timeout:
                logging.warning('[Compiler-Algorithm]:' + str(p.poll()))
                try:
                    p.kill()
                except Exception as e:
                    logging.warning('[Compiler]:algorith error.' + str(e))
                return 'algorithm time out'
            # p.terminate()
            # print p.poll()
        # time.sleep(0.01)
        # print p,p.poll(),p.pid
        # print 'exited'
        logging.info('[Compiler]:End Time:' + str(int(round(time.time() * 1000))))
        # out,err = p.communicate()
        if p.stdout:
            p.stdout.close()
        if p.stdout:
            p.stdout.close()
        try:
            p.kill()
        except OSError as e:
            logging.warning(str(e))
        logging.info('[Compiler]:' + str(err))
        return out + err

        pass

    def execute_algorithm(self, algorithm, lang, sync=True):
        """complie code and run it.
	
		编译并执行算法代码
		
		Args:
			algorithm:算法代码
			language_type:语言标记
		
		Returns:
			string 执行结果
		"""
        if lang == 'raw':
            return algorithm.strip()

        # todo compile other lang
        return ''

    @staticmethod
    def parse_algorithm(code):
        """parse code to algorithm

		Returns:
			{'sql':{input:[{'variable':'$result', 'sql':'$sql'}....],
					script:[{}....]},
			 'input':{'lang':'$language', 'data':'$algorithm'},
			 'script':{'lang':'$language', 'data':'$algorithm'}
			}
		"""
        # 过滤所有注释
        algorithm = {'sql': {'input': [], 'script': []}, 'input': {'lang': 'raw', 'data': ''},
                     'script': {'lang': 'raw', 'data': ''}}
        pattern_note = re.compile(r"^@@.*$", re.M)
        code = re.sub(pattern_note, '{$cmsnote}', code)
        pattern_note = re.compile(r"\{\$cmsnote\}\n*")
        code = re.sub(pattern_note, '', code)
        if code == '':
            return algorithm
        code = code + '\n' if code[-1] != '\n' else code
        # 开始适配算法
        pattern = re.compile(r'\[(?:input|sql|script):*\w*\]\s*\n')
        segment = pattern.split(code)
        header = pattern.findall(code)
        for i in range(1, len(segment)):
            # 开始分析
            p2 = re.compile(r'(\[)(input|script|sql)(:*)(\w*)(\]\s*\n)')
            match = p2.match(header[i - 1])
            if match is None:
                logging.warning('algorith code parse error')
                return algorithm
            _tag = match.groups()[1]
            _lang = match.groups()[3]
            if _tag == 'sql':
                # 构造结果集变量系统
                # format: input:booklist>>"select * from tblname"
                sql_pattern = re.compile(r'(^\s*)(input|script)(:)(\w+)(\s*<<\s*")(.*)("$)', re.M)
                sql_arr = sql_pattern.findall(segment[i])
                input_sql_list = []
                script_sql_list = []
                for item in sql_arr:
                    if item[1] == 'input':
                        input_sql_list.append({'variable': item[3], 'sql': item[5]})
                    if item[1] == 'script':
                        script_sql_list.append({'variable': item[3], 'sql': item[5]})
                algorithm[_tag] = {'input': input_sql_list, 'script': script_sql_list}
            if _tag in ('input', 'script'):
                # 构造脚本系统
                p3 = re.compile(r"(^\n*)|(\n*$)")
                algorithm[_tag] = {'lang': _lang, 'data': re.sub(p3, '', segment[i])}
        return algorithm
