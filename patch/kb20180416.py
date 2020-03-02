#coding=utf-8
import sys
import json
import os

sys.path.append("..")
from dbmanager import DbManager
from common import Common
os.chdir("../")

cfg = Common.loadConfig()
#print cfg['db']
db = DbManager()
db.initConn(cfg['db'])
sql = "show databases like 'cms_site_%'"
n,data = db.executeQuery(0,sql)
for row in data:
	pid = row[0].replace('cms_site_','')
	#创建statistics表
	sql = "CREATE TABLE IF NOT EXISTS `cms_template_statistics` (`template_id` int(11) NOT NULL COMMENT '模板id',`document_count` int(11) NOT NULL COMMENT '文档数',UNIQUE KEY `template_id` (`template_id`),KEY `document_count` (`document_count`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
	n,createdata = db.execute(pid,sql)
	print sql
	print '@@@@@@@@'
	sql = "show tables like 'cms_tbl_%'"
	n ,tbldata = db.executeQuery(pid,sql)
	for tbl in tbldata:
		tid = tbl[0].replace('cms_tbl_','')
		sql = 'select count(document_id) as doc_count from '+tbl[0]
		n,statdata = db.executeQuery(pid,sql)
		for stat in statdata:
			print 'TID:',tid,' Count:',stat[0]
			sql = "INSERT INTO `cms_template_statistics` (template_id,document_count) VALUES("+str(tid)+", "+str(stat[0])+") ON DUPLICATE KEY UPDATE `document_count`=`document_count`+1"
			n,insertdata = db.execute(pid,sql)
			print sql

	print '======',pid,'======'
#print data
#db_cfg = Common.collection_find(cfg['db'],lambda s:s['pid']==int(pid))
db.closeConn()
