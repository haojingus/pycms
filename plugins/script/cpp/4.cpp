#include <iostream>
#include <fstream>

using namespace std;
int main(int,char**)
{
ifstream in("config.json");
if (!in.is_open()) {
	cout<<"open error"<<endl;
	return 0;
	}
char buff[128];
while(!in.eof())
{
	in.getline(buff,100);
	cout<<buff<<endl;
}
return 0;
}
