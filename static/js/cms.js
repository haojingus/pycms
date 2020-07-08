var vm = new Vue({
	el:'#app',
	data:{
		dev_data:{},
		user_data:{},
		submit_data:{},
		system_data:{publish_url:''}
	},
	methods:{
		user_func1:function(p){},
		user_func2:function(p){}
	}
});

var cmsTimer;
var debuginfo;
var Cms = {
    version: "1.1.0",
	data_version : "2.0",
    publish_running: false,
	fid_set : '',
	error_stack : new Array,
	vaild : true,
	_callback : new Array,

	register_callback : function(func,params){
		this._callback.push({func:func,params:params});
	},

	callback : function(){
		for (let i = 0;i<this._callback.length;i++){
			this._callback[i].func(this._callback[i].params);
		}
	},

	clean_error: function(){
		this.vaild = true;
		this.error_stack = [];
	},

	push_error: function(msg) {
		this.vaild = false;
		this.error_stack.push(msg);
	},

	
    collect: function() {
        let cms_pid = $("input#project_id").val();
        let cms_tid = $("input#template_id").val();
        let cms_did = $("input#document_id").val();
        let data = {
            pid: cms_pid,
            tid: cms_tid,
            did: cms_did
        };
		let arr_id_set = this.fid_set.split(',');
		for (let i=0;i<arr_id_set.length;i++){
			let submit_propname = 'sp'+arr_id_set[i]+'_submit_data';
			let user_propname = 'sp'+arr_id_set[i]+'_submit_data';
			if(vm.submit_data.hasOwnProperty(submit_propname)){
				data['_sp'+arr_id_set[i]+'_value'] = vm.submit_data[submit_propname];
				//JSON.stringify(vm.$get(propname));
			}
			else if(vm.user_data.hasOwnProperty(user_propname)){
				data['_sp'+arr_id_set[i]+'_value'] = vm.user_data[user_propname];
			} else{
				data['_sp'+arr_id_set[i]+'_value'] = '';
			}
		}
        data['field_ids'] = this.fid_set;
		data['publish_url'] = vm.system_data.publish_url;
        //console.log(data);*/
        return data;
    },

    save_document: function(action,callback) {
        var data = this.collect();
        action = "/editor/document?action=" + action;
        $.post(action, data,
        function(result) {
			console.log('save document====>',result);
            let obj = JSON.parse(result);
            if (obj.code === 0) {
					callback(data,obj.did,obj.errmsg);
            } else {
					callback(data,-1,obj.errmsg);
            }
        });
    },

	send_batch_task: function(pid,tid,didset,showFunc) {
		this.publish_running = true;
		$.post('/admin/task?action=batchpub', {
			pid: pid,
			tid: tid,
			did_set: didset
		},
		function(result) {
			console.log('send_batch_task=====>',result);
			var obj = JSON.parse(result);
			console.log(obj.code);
			switch (obj.code) {
				case 201:
					cmsTimer = setInterval(function() {
						//开始ajax查状态
						$.ajax({
                        type: "get",
                        url: "/admin/task?action=query&batchid="+obj.task_id+ "&rd=" + Math.random(),
                        dataType: "html"
                    }).done(function(result) {
						console.log('send_batch_task======>',result);
                        var recode = JSON.parse(result);
						console.log(recode.code);
                        if (recode.code == 200) {							
                            this.publish_running = false;
							console.log(this.publish_running);
                            clearInterval(cmsTimer);
                        } else if (recode.code == 201) {} else {
                            clearInterval(cmsTimer);
                            this.publish_running = false;
                        }
						debuginfo = recode;
						showFunc(recode);
                    }).fail(function(result) {
                        this.publish_running = false;
                        clearInterval(cmsTimer);
                    });
						//ajax end
					},100);
					break;
				default:
					showFunc(obj);
			}
		});

	},

    send_task: function(algorithmType,preview, pid, tid, did, showFunc) {
        //异步RPC队列
        this.publish_running = true;
        $.post('/admin/task?action=create', {
			type: algorithmType,
            pid: pid,
            tid: tid,
            did: did,
			preview: (preview)?'Y':'N'
        },
        function(result) {
        	console.log('send_task======>',result);
            var obj = JSON.parse(result);
            console.log('<=====');
            switch (obj.code) {
            case 201:
                cmsTimer = setInterval(function() {
                    $.ajax({
                        type: "get",
                        url: "/admin/task?action=query&taskid=" + obj.task_id + "&rd=" + Math.random(),
                        dataType: "html"
                    }).done(function(result) {
						console.log('send task====>',result);
                        var recode = JSON.parse(result);
						console.log(recode.code);
                        if (recode.code == 200) {							
                            this.publish_running = false;
							console.log(this.publish_running);
                            clearInterval(cmsTimer);
                        } else if (recode.code == 201) {
						
						} 
						else {
                            clearInterval(cmsTimer);
                            this.publish_running = false;
                        }
						debuginfo = recode;
						showFunc(recode);
                    }).fail(function(result) {
                        this.publish_running=false;
                        clearInterval(cmsTimer);
                    });
                },
                100);
                break;
            default:
				this.publish_running = false;
                alert('finished');
            }
        });
    }

};
