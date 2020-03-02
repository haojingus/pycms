#include "../cmsapp.h"

using namespace std;

class Cms
{
	public:
		string version;

		void echo();
};

void Cms::echo()
{
	cout<<this->version<<endl;
}

void cmsapp(std::map<string,string> argc)
{
	Cms _cms;
	_cms.version = string("this is object");
	_cms.echo();
	cout<<"hello cmsapp"<<endl;
}
/*
int main(int argc,char* argv[])
{
	std::map<string,string> _argv;
	_argv[string("key1")] = string("hello");
	cmsapp(_argv);
	return  0;
}
*/
