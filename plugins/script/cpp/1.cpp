#include <iostream>
#include <cstdlib>
#include <string>
#include <regex>

int main(int argc,char* argv[])
{
	std::string cmd = "clang -Xclang -ast-dump -fsyntax-only script_20_1_2.cpp |grep cmsapp|sed \"s,\\x1B\\[[0-9;]*[a-zA-Z],,g\"";
	char buffer[128];
	std::string result = "";
	FILE* pipe = popen(cmd.c_str(),"r");
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
	std::cout<<"########"<<std::endl;
	result = "hello222world333!nihao2";
	//std::string pattern{"FunctionDecl.*?prev.*?cmsapp"};
	std::string pattern("\\d+\\w+");
	std::regex re(pattern);
	std::smatch rr;
	while (std::regex_search(result, rr, re)) {  
	    for (auto x : rr)  
			std::cout << x << " ";
		std::cout << std::endl;
		if (result==rr.suffix().str())
			break;
		result = rr.suffix().str();
		std::cout<<result<<"$$$$$$$$$"<<std::endl;
	}  
	return 0;

}
