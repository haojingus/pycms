#include "config.h"
#include "cmsast.h"
#include <sstream>

bool CmsAST::checkEntryPoint(std::string key)
{
	char cmd[256];
	sprintf(cmd,"clang -Xclang -ast-dump -fsyntax-only %s/plugins/script/cpp/usr/%s.cpp |grep cmsapp|sed \"s,\\x1B\\[[0-9;]*[a-zA-Z],,g\"",CMSROOT,key.c_str());

	char buffer[128];
	std::string result = "";
	FILE* pipe = popen(cmd,"r");
	if (!pipe){
		return 0;
	}

	while(!feof(pipe)){
		if(fgets(buffer,128,pipe))
		{
			//std::cout<<buffer<<std::endl;
			result.append(buffer);
		}
	}
	pclose(pipe);
	std::cout<<result<<std::endl;
	std::string pattern{"FunctionDecl.*?prev.*?cmsapp"};
	std::regex re(pattern);
	std::smatch r;
	std::stringstream match;
	while (std::regex_search(result, r, re)) {  
	    for (auto x : r)
			match << x;
			//std::cout << x << " ";
		//std::cout << std::endl;
		if (result==r.suffix().str())
			break;
		result = r.suffix().str();
		//std::cout<<result<<"$$$$$$$$$"<<std::endl;
	}
	std::cout<<match.str()<<std::endl;
	return false;

}
