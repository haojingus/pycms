if(vm.user_data["sp{$field_id}_user_data"]==""||vm.user_data["sp{$field_id}_user_data"]=="/static/img/imageholder.png")
Vue.set(vm.submit_data,"sp{$field_id}_submit_data","");
else
Vue.set(vm.submit_data,"sp{$field_id}_submit_data",vm.user_data["sp{$field_id}_user_data"]);