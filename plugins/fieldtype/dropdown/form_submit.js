if (vm.user_data.hasOwnProperty('sp{$field_id}_user_data')){
       if(vm.user_data.sp{$field_id}_user_data!=""){
	    vm.$set(vm.submit_data,"sp{$field_id}_submit_data",vm.user_data.sp{$field_id}_user_data);
       }
}