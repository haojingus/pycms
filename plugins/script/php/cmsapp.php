<?php
include_once(dirname(__FILE__)."/precompile.php");

class CmsUtil
{
    private $_key;
    private $_errkey;

    function __construct()
    {
        $this->_key = $this->cms_uuid('CMS_RENDER_KEY_');
	    $this->_errkey = $this->cms_uuid('CMS_RENDER_ERRKEY_');
    }

    function cms_uuid($prefix = '')
    {
        $chars = md5(uniqid(mt_rand(), true));
        $uuid  = substr($chars,0,8) . '-';
        $uuid .= substr($chars,8,4) . '-';
        $uuid .= substr($chars,12,4) . '-';
        $uuid .= substr($chars,16,4) . '-';
        $uuid .= substr($chars,20,12);
        return $prefix . $uuid;
    }

    function display($content)
    {
        if (!is_string($content))
        {
            echo('php type is not string!!!');
            return;
        }
        global $redis;
        global $timeout;

        //$key = cms_uuid('CMS_RENDER_KEY_');
        //echo $key;
        $redis->set($this->_key,$content);
        $redis->expire($this->_key,$timeout);
        echo('[CMSDATAKEY='.$this->_key.']');
        return;
    }

    function abort($msg)
    {
        global $redis;
        global $timeout;

    	if (!is_string($msg))
		{
			echo('js type is not string!!!');
			return;
		}
		$msg = array('errcode'=>704,'errmsg'=>$msg);

        $redis->set($this->_errkey,json_encode($msg));
        $redis->expire($this->_errkey,$timeout);
        echo('[CMSERRKEY='.$this->_errkey.']');
        return;
    }
}

$timeout = 30;

if ($argc!=2){
	echo "Usage:cmsapp.php [task_id]\n";
	exit(0);
}

//获取系统配置
$cfg_path = str_replace("plugins/script/php","conf/config.json",dirname(__FILE__));
$cfg_file = fopen($cfg_path,"r");
$cfg = fread($cfg_file,filesize($cfg_path));
$cfg = json_decode($cfg,True);

//获取用户sql数据集
$redis = new Redis();
$redis->connect($cfg['redis']['host'], intval($cfg['redis']['port']));
$redis->select(1);
$usr_data_set = array();
if ($redis->exists($argv[1]))
{
	$usr_data_set = json_decode($redis->get($argv[1]),True);
}
else
{
	echo('redis error');
	exit(0);
	//$usr_data_set = array();
}
$type = $usr_data_set['$type'];
$pid = $usr_data_set['$pid'];
$tid = $usr_data_set['$tid'];
$did = $usr_data_set['$did'];
$fid = $usr_data_set['$fid'];
//加入内置函数
//$usr_data_set['$display'] = 'cms_display';
$cmsobj = new CmsUtil;
foreach($usr_data_set as $k => $v)
{
    $cmsobj->$k = $v;
}


$source_path = sprintf("%s/usr/%s_%s_%s_%s.php",dirname(__FILE__),$type,$pid,$tid,$fid);
$obj_path = str_replace(".php",".obj.php",$source_path);
if (file_exists($obj_path))
{
	if(filemtime($obj_path)>filemtime($source_path))
	{
		include_once($obj_path);
		cmsapp($cmsobj);
		exit(0);
	}
}
$recode = precompile($type,$pid,$tid,$fid);
if ($recode['code']!=200)
{	echo(json_encode($recode));
	exit(0);
}
include_once($obj_path);
cmsapp($cmsobj);
$redis->close();
exit(0);


?>
  
