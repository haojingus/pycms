<?php
require dirname(__FILE__).'/vendor/autoload.php';
use PhpParser\Error;
use PhpParser\NodeDumper;
use PhpParser\ParserFactory;


function precompile($type,$pid,$tid,$fid)
{

//if ($argc!=2){
//	echo "Usage:precompile.php [tid]\n";
//}
$path = sprintf("%s/usr/%s_%s_%s_%s.php",dirname(__FILE__),$type,$pid,$tid,$fid);
//$path = dirname(__FILE__).'/usr/'.$argv[1].'.php';

if(!is_file($path))
	return array('code'=>200,'errmsg'=>"source is not existed!");

$file = fopen($path,"r");
$code = fread($file,filesize($path));
	
$parser = (new ParserFactory)->create(ParserFactory::PREFER_PHP7);
try {
	$ast = $parser->parse($code);
	} catch (Error $error) {
		return array('code'=>1500,'errmsg'=>"Parse error: {$error->getMessage()}");
	}
	
$json_ast = json_encode($ast, JSON_PRETTY_PRINT);
$new_ast = json_decode($json_ast,TRUE);

	//print_r($new_ast);

$target_code = array();
$entry_point = False;
foreach($new_ast as $stmts)
{
	if ($stmts['nodeType']!="Stmt_Class"&&$stmts['nodeType']!="Stmt_Function")
	{
		array_push($target_code,array($stmts['attributes']['startLine'],$stmts['attributes']['endLine']));
	}
	elseif ($stmts['nodeType']=="Stmt_Function"&&$stmts['name']=='cmsapp'&&count($stmts['params'])==1)
	{
		$entry_point = True;
	}

}

//无入口函数则退出
if (!$entry_point)
{
	return array('code'=>1502,'errmsg'=>"need a entry point named cmsapp");
}

	fseek($file,0);
	$i = 1;
	$outfile = fopen(str_replace('.php','.obj.php',$path),"w");
	
	while(! feof($file))
	{
		$line = fgets($file);
		if (count($target_code)>0)
		{
			if ($i>=$target_code[0][0]&&$i<=$target_code[0][1])
			{	
				$line = "//".$line;
				array_shift($target_code);
			}
		}
		fwrite($outfile,$line);
		$i++;
	}
	fclose($outfile);
	fclose($file);
	return array('code'=>200,'errmsg'=>"precompile ok!");
//	print_r($entry_point==False);
//	echo json_encode($ast, JSON_PRETTY_PRINT), "\n";
//		$dumper = new NodeDumper;
		//echo $dumper->dump($ast) . "\n";
}
