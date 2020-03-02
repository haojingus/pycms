var compiler = require(__dirname+'/precompile');
var fs = require('fs');
var redis = require('redis');
var process = require('process');
const uuid = require('node-uuid');
const timeout = 100;
var argv = process.argv.splice(2);
//console.log(argv);
if (argv.length!=1){
	console.log("Usage:node cmsapp.js [task_id]\n");
	process.exit(0);
}
var tid = argv[0];
//获取系统配置
cfg_path = __dirname.replace("plugins/script/es5","conf/config.json")
var data=fs.readFileSync(cfg_path,"utf-8");
var cfg = JSON.parse(data.toString());
//console.log(cfg['redis']['port'].toString()+"$$$"+cfg['redis']['host']);
var client  = redis.createClient(cfg['redis']['port'].toString(), cfg['redis']['host']);
//client.on('error',function(err){console.log(err)});
client.on('ready',function(res){get_task_info(tid)});

function get_task_info(tid){
	var buffer = "";
	client.select('1',function(error){
		if (error){
			console.log(error);
		}
		else
		{
			client.get(tid, function(error, res){
				 if(error) {
					console.log("can't find tid");
					client.quit();
				 }
				 else
				 {
					call_user_app(res);
				 }
				 client.quit();
			});
		}
	});
}

function call_user_app(res){
	var usr_data_set = JSON.parse(res);
	var type = usr_data_set['$type'];
	var pid = usr_data_set['$pid'];
	var tid = usr_data_set['$tid'];
	var did = usr_data_set['$did'];
	var fid = usr_data_set['$fid'];
	//构造SDK内置方法
	const _key = 'CMS_RENDER_KEY_'+uuid.v4();
	const _errkey = 'CMS_RENDER_ERRKEY_'+uuid.v4();
	usr_data_set['$display'] = function(_content){
		if (typeof _content!='string')
		{
			process.stdout.write('js type is not string!!!');
			return;
		}
		client.set(_key,_content,function(err, reply){
			if (err) return false;
			console.log(reply);		
		});
		client.expire(_key,timeout,function(err,reply){
			if (err) return false;
			console.log(reply);
		});
		process.stdout.write('[CMSDATAKEY='+_key+']');
	}

	usr_data_set['$abort'] = function(_msg){
		if (typeof _msg!='string')
		{
			process.stdout.write('js type is not string!!!');
			return;
		}
		_msg = {'errcode':704,'errmsg':_msg};

		client.set(_errkey,JSON.stringify(_msg),function(err, reply){
			if (err) return false;
			console.log(reply);		
		});
		client.expire(_errkey,timeout,function(err,reply){
			if (err) return false;
			console.log(reply);
		});
		process.stdout.write('[CMSERRKEY='+_errkey+']');
	}


	var source_path =  __dirname+'/usr/'+type+'_'+pid.toString()+'_'+tid.toString()+'_'+fid.toString()+'.js';
	var obj_path = source_path.replace(".js",".obj.js");

	if (fsExistsSync(obj_path))
	{

		if(fs.statSync(obj_path)['ctime'].getTime()>fs.statSync(source_path)['ctime'].getTime())
		{
			
			var cmsapp = require(obj_path);
			var app = new cmsapp(usr_data_set);
			return;
		}
	
	}
	
	var c = new compiler();
	recode = c.precompile(type,pid,tid,fid);
	if (recode.code!=200)
	{
		console.log(recode);
		process.stdout.write(recode.errmsg);
		//console.log(recode);
		process.exit(0);
	}
	else
	{
		var cmsapp = require(obj_path);
		var app = new cmsapp(usr_data_set);
	}

}

function fsExistsSync(path) {
	try{
		fs.accessSync(path,fs.F_OK);
		}
	catch(e){
		return false;
		}

	return true;
}





