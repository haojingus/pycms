//vm.$set(vm.dev_data,"sp{$field_id}_developer_data",{rows:5});
if (vm.submit_data.hasOwnProperty('sp{$field_id}_submit_data')){
   vm.$set(vm.user_data,"sp{$field_id}_user_data",vm.submit_data["sp{$field_id}_submit_data"]);
}

cmsobj.register_callback(function(){
    if (vm.submit_data.hasOwnProperty('sp{$field_id}_submit_data')){
        vm.$set(vm.user_data,"sp{$field_id}_user_data", vm.submit_data["sp{$field_id}_submit_data"]);
    }else if(vm.dev_data.hasOwnProperty('sp{$field_id}_developer_data') &&vm.dev_data["sp{$field_id}_developer_data"]!=""){
        vm.$set(vm.user_data,"sp{$field_id}_user_data", vm.dev_data["sp{$field_id}_developer_data"]);
    } else {
        vm.$set(vm.user_data,"sp{$field_id}_user_data","");
    }
},[]);