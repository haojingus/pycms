#include "cmsredis.h"

CmsRedis::CmsRedis():m_conn(NULL),m_reply(NULL){return;}

bool CmsRedis::connect(const char* host,int port)
{
	struct timeval timeout = { 1, 500000 }; // 1.5 seconds
	this->m_conn = redisConnectWithTimeout(host, port, timeout);
	if (this->m_conn == NULL || this->m_conn->err) {
		if(this->m_conn) {
			std::cerr<<"Connection error:"<<this->m_conn->errstr<<std::endl;
		} else {
			std::cerr<<"Connection error:can't allocate redis context"<<std::endl;
		}
		return false;
	}
	return true;
}

void CmsRedis::select(const char* dbname)
{
	this->m_reply = (redisReply*)redisCommand(this->m_conn,"select %s",dbname);
	freeReplyObject(this->m_reply);
	return;
}

void CmsRedis::set(std::string key,std::string value,int expired=-1)
{
	if (expired==-1) {
		this->m_reply = (redisReply*)redisCommand(this->m_conn,"set %s %s",key.c_str(),CmsText::replaceAll(value,"\"","\\\"").c_str());
	} else {
		this->m_reply = (redisReply*)redisCommand(this->m_conn,"setex %s %d %s",key.c_str(),expired,CmsText::replaceAll(value,"\"","\\\"").c_str());
	}
	freeReplyObject(this->m_reply);
	return;

}

std::string CmsRedis::get(std::string key)
{
	this->m_reply = (redisReply*)redisCommand(this->m_conn,"get %s",key.c_str());
	std::string result(this->m_reply->str);
	freeReplyObject(this->m_reply);
	return result;
}


void CmsRedis::close()
{
	redisFree(this->m_conn);	
}


