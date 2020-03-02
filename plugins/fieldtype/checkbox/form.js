if (vm.submit_data.hasOwnProperty('sp{$field_id}_submit_data')){
        if (vm.submit_data["sp{$field_id}_submit_data"]==''){
            vm.$set(vm.user_data,"sp{$field_id}_user_data",[]);
        }else{
            vm.$set(vm.user_data,"sp{$field_id}_user_data", vm.submit_data["sp{$field_id}_submit_data"].split(','));
        }
    }else{
        vm.$set(vm.user_data,"sp{$field_id}_user_data",[]);
    }