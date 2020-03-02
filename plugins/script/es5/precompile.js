function compiler(){

var esprima = require("esprima");
var fs = require("fs");


this.precompile = function(type,pid,tid,fid){
	
	path = __dirname+ "/usr/"+type+"_"+pid.toString()+"_"+tid.toString()+"_"+fid.toString()+".js";
	//console.log("PATH:"+path);
	if(!fsExistsSync(path)){
		return {code:200,errmsg:"source is not existed!"};
	}
	var data=fs.readFileSync(path,"utf-8");
	var code = data.toString();
	var option = {range:true};
	var ast = [];
	try{
		ast = esprima.parse(code,option);
	}catch(err)
	{
		return {code:1500,errmsg:"Parse error:"+err.message};
	}
	json_ast = JSON.parse(JSON.stringify(ast));

	var new_code = '';
	var find_entry_point = false;
	for (i=0;i<json_ast['body'].length;i++)
	{
		if (json_ast['body'][i]['type']=='FunctionDeclaration')
		{
			if (json_ast['body'][i]['id']['name']=='cmsapp'&&json_ast['body'][i]['params'].length==1)
				find_entry_point =true;
			new_code += code.substring(json_ast['body'][i]['range'][0],json_ast['body'][i]['range'][1])+"\n";
		}
		//console.log(json_ast['body'][i]);
	}
	if (new_code.length==0||!find_entry_point){
		return {code:1502,errmsg:'entry point miss or cmsapp params count err'};
	}
	new_code += "module.exports = cmsapp;";		
	fs.writeFileSync(path.replace(".js",".obj.js"),new_code);
	//console.log(new_code);
	return {code:200,errmsg:'precompile ok!'};

};


function fsExistsSync(path) {
    try{
	    fs.accessSync(path,fs.F_OK);
		}catch(e){
		return false;
		}
	return true;
	}
}

module.exports = compiler;
