#ifndef __CMSREDIS_H_
#define __CMSREDIS_H_
#include <iostream>
#include <hiredis.h>
#include "cmstext.h"

class CmsRedis
{
	public:
		CmsRedis();
		~CmsRedis();
		bool connect(const char* host,int port);
		void select(const char* dbname);
		void set(std::string key,std::string value,int expired);
		std::string get(std::string key);
	void close();

	private:
		redisContext *m_conn;
		redisReply *m_reply;
};
#endif
