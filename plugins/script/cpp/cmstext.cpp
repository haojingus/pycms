#include "cmstext.h"


std::string CmsText::replaceAll(std::string source,std::string strold,std::string strnew)
{
	int npos = source.find(strold);
	int len = strnew.length();

	while((npos!=std::string::npos)) {
	
		source = source.replace(npos,len,strnew);
		npos = source.find(strold,npos+len);
		//std::cout<<npos<<std::endl;

	}
	//std::cout<<source<<std::endl;
	return source;
}
