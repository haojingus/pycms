#define AA "asdsad"
#include <iostream>
#include <sstream>
#include <string>
using namespace std;
int main(int argc,char** argv)
{
char ss[256];
stringstream s;
//string s("hello");
//s+=AA;
//s.append(AA);
sprintf(ss,"Hello %s %s !\n"," world",AA);

cout<<ss<<endl;
return 0;
}
