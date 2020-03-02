#include "cmsapp.h"

int main(int argc,char* argv[])
{
	std::map<string,string> _argv;
	_argv[string("key1")] = string("hello");
	cmsapp(_argv);
	return 0;
}
