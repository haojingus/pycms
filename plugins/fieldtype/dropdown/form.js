var tmp_data=vm.dev_data.sp{$field_id}_developer_data;
for(var i in tmp_data){
    if(tmp_data[i].selected){
           vm.$set(vm.user_data,"sp{$field_id}_user_data",tmp_data[i].value);
    }
}

cmsobj.register_callback(function(){
  if (vm.submit_data.hasOwnProperty('sp{$field_id}_submit_data')){
       if(vm.submit_data.sp{$field_id}_submit_data!=""){
             for(let i in vm.dev_data.sp{$field_id}_developer_data){
                   var t_d =  vm.dev_data.sp{$field_id}_developer_data[i];
                    t_d.selected = false; 
                     if(t_d.value.toString() == vm.submit_data.sp{$field_id}_submit_data.toString()){
                      vm.$set(vm.user_data,"sp{$field_id}_user_data",vm.submit_data.sp{$field_id}_submit_data);
                          t_d.selected = true;
                          break;
                     }
             }
        }else{
       vm.$set(vm.user_data,"sp{$field_id}_user_data",vm.dev_data.sp{$field_id}_developer_data[0].value);
}
  }
},[])