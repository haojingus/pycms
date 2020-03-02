from sdk.cms import CmsSDK
import sys

def application(taskid):
	m = __import__('usr.aaa')
	usrmod = getattr(m,'aaa')
	usrapp = getattr(usrmod,'cmsapp')
	usrapp({'code':1,'msg':'23123'})

if __name__ == '__main__':
	if len(sys.argv)<2:
		return
    application(sys.argv[1])

	#End
