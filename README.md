# CMS开发指南和备忘录

> * 安装
------
python 2.7 (dep zlib-devel readline-devel)  
mysql-devel  
redis  

python3 模块  
pymysql  
tornado  
Image(PIL)  
pycket.session  
markdown  
requests

------

配置太多了，有点记不住，必须写下来，找不到的就从这里看，**环境和配置** 部署和二次开发中最重要的问题，CMS能走多远取决于你的二次开发能力，我仅仅是提供一种文档管理工具：

> * 备忘录
> * 部署指南
> * 插件体系
> * 应用和二次开发

![cmd-markdown-logo](https://www.zybuluo.com/static/img/logo.png)


## 备忘录

> 配置描述:  
> /$webroot/conf/config.json   
> **核心数据库cms_core连接信息、redis连接信息、document表默认字段名和别名对照表**  
> *中文sql翻译完全依赖这个对应表*  
>
> /$webroot/conf/userdb.json  
> **项目数据库的连接信息** *cms_site_n*  
>   
> 文件描述  
> \*handler.py 控制器  
> mod\*.py 数据访问层  
> templates/\*.html 模板  
> plugins/fieldtype/\* 模板域插件 **需要通过vue框架实现**
>
> 发布路径模板  
> /site\_{$pid}/{$tid}/{$did}.html  
> 根路径为发布目标域名的根，通过项目配置的rsync来同步  
>   
> Task id说明： 
> Task\_id生成规则：pid\_tid\_did\_timestamp  
> Task Data set key 规则：pid\_tid\_did\_timestamp\_fid 此key为一次渲染会话生成的  
> Task Data set 需要根据field\_type来决定是否把用户输入的模板域值加载到算法脚本用，名称为usr\_input\_data，类型为string  
> 插件:插件仅仅是用于捕获编辑的输入，所以多数三方插件的类型均为input，input插件需要定义html和css\js\submit_js，用于form表单的显示，方便编辑录入，out型插件不会显示在编辑录入界面，只会渲染文档时执行算法，同时[input:\*]算法域不生效，多数系统插件属于out类型。  
> 插件修改为vue 2.4支持，不再通过后端完成渲染，而是使用数据双向绑定的方式完成渲染和采集。  
  
## 算法描述
**关键词** 

@@ *单行注释*  
input: *插件渲染作用域*  
script: *输出渲染作用域*  
[sql] SQL段描述符  
[input:lang] 输入段描述符  
[script:lang] 脚本段描述符  
{$name} 模板域/字段  
[#name] 模板/表  
  
范例  
```php 
 
@@这是一套模板算法mydata是用户数据集,通过<<符号导入到script域，成为argv的一个成员
@@sql结果集
[sql]
script:mydata<<"select {$文档编号},{$头条} from {#测试模板1} where {$文档编号}<100 limit 50"
@@后台模板域算法
[input:raw]
[{"name":"类别一","value":1},{"name":"类别二","value":2}]
@@前台渲染算法
[script:php]
<?php
function cmsapp($argv){
  $key = '$input';
  
$argv->display('我们选择的是['.$argv->$key.']'.'<br/>数据库取出来的数组为'.json_encode($argv->mydata));
}
?>
```

------
## 开发者必读
### 1.当前支持语言和未来可支持的语言

- [x] C++
- [x] Python
- [x] PHP
- [x] Node.js
- [ ] J2EE
- [ ] Blockly Google图形化开发语言，适合老人小孩 
### 2.为什么要做二次开发
如果cms做的事情仅仅是把编辑录入的数据片段组合在一起，我们不需要二次开发。实际情况并非如此，编辑可能录入的是一个id，也可能是一个选择项，我们需要通过这个id或者选项来决定获取对应的内容来渲染到模板，这个过程，无法通过简单的文本拼接来完成，二次开发就是针对这个场景来设立的。

### 3.二次开发的辅助工具
cms本身提供了基于web的debug窗口，但从用户输入角度来开，有时候单行文本、多行文本、复选框这些通用的组件无法满足编辑录入的需求，二次开发的源头需要做增强，因此我提供了开放的录入插件设计标准，并提供在线debug，通过录入插件，可以完成数据的录入、转换、入库。配合二次开发代码实现最终的渲染展示。

### 4.构造属于自己的辅助工具
模板域是构造站点的基本单元，模板域是以插件形式加载到CMS系统中的，模板域的易用性决定了cms构建文档的速度和质量。  
模板域的使用js来开发，基于vue 2.x框架，通过系统设置->插件信息进入开发界面。每个模板域插件包含以下文件:  
form.html、form.js、form.css、form_submit.js、develop.test(可选)、user.test(可选)  
**form.html**:模板域html模板，需要兼容bootstrap，包含在样式为"form-group"的div之中  
**form.js**:模板域的js初始化文件，用于初始化模板域，此处推荐使用vue进行数据双向绑定，cms引擎会把spx_develop_data数据直接传递到该js变量中，该变量也是vue的data集合一个成员，用于绑定到模板域的初始状态  
**form.css**:模板域的css支持部分，该文件会被引入到header的style中  
**form_submit.js**:模板域提交数据的时候，数据格式化js，用于完成vue数据到入库数据spx_submit_data的转换，上述js变量为string类型。
*develop.test*:注入spx_develop_data的数据，该数据为JSON化之前的数据，cms引擎会完成JSON.parse
*user.test*:用户入库数据的模拟数据，该数据为string，渲染时注入spx_submit_data  

完整的vue对象和data结构描述

```js
var vm = new Vue({
	el:'#app',
	data:{
		dev_data:{},//插件组件的全量数据
		user_data:{},//当前插件组件绑定的有效数据，比如下拉列表的选中项
		submit_data:{},//提交到后端数据库的数据，一般是已经被序列化的数据
		system_data:{publish_url:''}//和插件无关的系统数据
	}
});

//此处的convert函数不存在，仅仅是为了说明自定义插件需要对spx_submit_data这种用户数据做转换再附加到spx_user_data上。spx_user_data不对数据做要求，仅仅是绑定关系决定数据类型。

```
#### cmsobj对象说明
cmsobj对象为cms主要js对象。插件开发中会使用到部分功能  
cmsobj.push_error(msg) 用于生成一个提交错误，并阻断发布/保存  
cmsobj.clean_error() 用于清楚错误栈，插件开发工程师一般用不到  
cmsobj.error_stack 错误栈信息，用于显示所有错误  
cmsobj.register_callback(func,new Array()) 用于注册所有插件初始化完成的回调。
以上文档中出现的spx实际编写时应改为{$field_id},该标签是cms的系统标签，用于替换为对应的field_id，类似的标签还有{$field_name}


### 5.PHP二次开发
二次开发前请务必理解前文提到的模板域插件渲染机制，这有助于你正确使用cms提供的debug工具  

所有语言版本的入口均为cmsapp(argv)方法，PHP版本范例如下  

```php
<?php

//下边这行echo代码会被cms沙盒过滤掉,cms禁止在函数、变量、类定义之外有执行动作
echo('test');

class myClass1{

	private $myPriv;
	public function __construct($param){
		$this->myPriv = $param;
	}

	public function show()
	{
		return $this->myPriv;
	}

}

function cmsapp($argv){

    $key = '$input';
	$cls1 = new myClass1('hello world');
    //统一通过display内置方法来输出，可以通过序列化来查看$argv的内容
    //因为我们的系统变量都是$前缀，和php的变量声明冲突，所以使用系统变量的时候，需要把变量名赋值过去，再间接引用
	$argv->display('这是myClass1的方法结果'.$cls1->show().'.这是插件输入值：'.$argv->$key);
	

}

?>
```

以上代码中，自定义的class、function均会被编译，能够外部执行的代码会被沙盒完全过滤，$argv传入的参数为PHP的Array类型，
> * 内部key介绍：  
$pid:项目id，引用方式：$argv['$pid'].菜鸟们注意，必须是单引号  
$tid:模板id  
$fid:模板域id  
$did:文档id  
$type:脚本类型（input、script）
$input:插件传值，也就是刚才的submit_data，如下拉列表的选定值 
/\w+/:非$前缀的字母key为算法中[sql]段中定义的结果集。在cmsapp中被引用到参数$argv中，生存期很短
> * 类型说明：
input:用于渲染后台输入域插件，结果直接引入spx_develop_data，需要能被json化  
script:用于输出渲染，输出的内容成为模板域的最终输出，当算法语言为raw时，且未定义其数据，结果会被用户录入覆盖

### 6. Node.JS的二次开发
Node.JS二次开发前请先参照PHP部分的渲染机制，脚本说明符号为es5,Node.JS版本的渲染和PHP一致，需要注意的是，Node.JS中三方库的使用大量采用了异步机制，debug的时候需要注意。  
该版本的核心库依然通过构建AST树完成代码的清理和保护，function cmsapp(argv)之外的所有表达式、定义均会被过滤掉，因此require需要加入到cmsapp的定义内部。渲染结果通过console.log输出到cms。  
示例代码：  
```js
function cmsapp(argv){

//console.log(argv); console输出已废弃，统一通过$display来输出
argv.$display(argv);
}

```

### 7. 系统内置方法说明
二次开发中，基于渲染模式时（Script模式）cmsapp传入的参数argv携带了一些系统调用可供开发者使用。  
argv.$display(string) 用于输出渲染结果  
argv.$abort(errmsg) 用于强行终止渲染和页面生成过程  
C++/php语言调用方法类似，如$argv-\>$display($content);


### 5. API的使用
##### CMS系统API均为RESTful规则  
#### 1.文档类
*添加文档*  
API:http://cmsdomain/api/document/{$pid}/{$tid}  
Method:POST  
Args:sp_x  
*eg:*curl -X POST -d "sp_1=123123&sp_2=asdasd&sp_3=dfsdf&sp_4=asdasd" "http://cms.gamebuilder.com.cn/api/document/18/1"  
- - - - -


*获取文档列表*  
API:http://cmsdomain/api/document/{$pid}/{$tid}  
Method:GET  
Args: 
	format 输出格式，目前对于文档类输出，支持page输出，其他默认为json，可以忽略此参数
	fl 条件参数  
	page 页码  
	pagesize 默认页长度为30  
*eg:*curl "http://cms.gamebuilder.com.cn/api/document/18/1?fl=create_time%3e20171201##sp_1%3d1"  
- - - - -


*批量发布文档*  
API:http://cmsdomain/api/document/{$pid}/{$tid}/didset  
Method:PATCH  
Args:  
	无  
*eg:*curl -X PATCH "http://cms.gamebuilder.com.cn/api/document/18/1/1,2,3,4,5"  
- - - - -


#### 2.模板类  
*模板列表*  
API:http://cmsdomain/api/template/{$pid}  
Method:GET  
Args:fl 条件参数  
*eg:*curl "http://cms.gamebuilder.com.cn/api/template/18  
- - - - -

### 6. 搜索引擎的使用  
CMS可以方便接入第三方全文搜索引擎，目前支持的是Lucene，也可接入Sphinx类引擎。考虑到配置便捷性，我们暂用Lucene  
I. 搜索引擎是深度整合的，在创建模板域(Field)的时候，需要选择绑定的搜索引擎字段，除了几个默认字段外，其余均可使用动态字段，即前缀为\*的字段，使用动态字段后，字段名会被强制写成fl_{$pid}_{$tid}_{$fid}_{$type},如数值型模板域pid:1 tid:1 fid:2被创建时,绑定的模板域为1_1_2_i  
检索时，需要直接调用Lucene引擎API，CMS不再介入，CMS发布文档时，Lucene会被实时刷新。Lucene配置项在/conf/config.json中

### 7. 定时发布和交叉发布的使用
CMS内建了系统消息回调，目前只开放了系统级的Timer，每10s发生一次，所有响应OnTimer的例程均被放置于CMS的子进程执行，例程只允许调用系统方法，目前开放的方法只有publish(pid,tid,did)，完成但未开放的方法有query(pid,sql)  
通过上述机制，可以完成定时发布，未来还会有交叉发布，即响应OnPlublish事件。  
注意！onTimer的设置中，setting内容为事件格式，有两种，T前缀为读秒周期，T3600代表3600秒执行一次，D前缀为闹钟触发，格式为YY-mm-dd HH:MM,通配符为\*,如D2017-10-10 \*\*:05，代表着2017年10月10日任何时间的05分触发   
以上回调设置在模板中，模板列表里点击编辑可以看到。以下为回调例程:  
```js
[
    {
		"onTimer": {
					"setting": "T5",
					"action": "publish(2,2,2)"
				}
	},
	{
		"onPublish": {
					"setting": "",
					"action": "publish(2,2,2)"
					}
	}
]
```


### 8. 文档发布和分享

在您使用 CMS 创作发布文档的同时，我不仅希望它是一个有力的工具，更希望您的思想和知识通过这个平台，连同优质的阅读体验，将他们分享给有相同志趣的人！




------

作者 [@这是名字][3]     
2017 年 11月 29日    

[^code]: 代码高亮功能支持包括 Java, Python, JavaScript 在内的，**四十一**种主流编程语言。

[1]: http://weibo.com/tuzi

