#coding=utf-8
import sys
from innerapi import InnerAPI

if len(sys.argv)!=5:
	print 'param error'

token = sys.argv[1]
func = sys.argv[2]
params = sys.argv[3].split(',')
env = sys.argv[4]
ia = InnerAPI(token)
ia.set_env(env)
getattr(ia,func)(*params)

