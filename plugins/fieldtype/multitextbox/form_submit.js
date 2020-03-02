if (vm.submit_data.hasOwnProperty('sp{$field_id}_submit_data')){
      //设置数据
        let tmp_data = vm.user_data["sp{$field_id}_user_data"];
/*
        let up_data;
        if(tmp_data){
            up_data= encodeURIComponent(tmp_data);
        }
*/
        vm.$set(vm.submit_data,"sp{$field_id}_submit_data",tmp_data );
}