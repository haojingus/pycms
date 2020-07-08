vm.user_func1 = function(fid){
    let compnent_id = "#localFiles_sp_"+fid;
    if($(compnent_id)[0].files.length>0){
           var formData = new FormData();
           formData.append("userFile",$(compnent_id)[0].files[0])
           var xhr = new XMLHttpRequest();
           xhr.onload = function(event){
               if(xhr.status == 200){
                   ret = JSON.parse(xhr.responseText)
                   if(ret.code==0){
                       console.log(ret)
                       $("#img_sp_"+fid).attr("src",ret.filename);
                       Vue.set(vm.user_data,"sp"+fid+"_user_data",ret.filename);
                   }
                   else
                       alert(ret.errmsg)
               } else {
                   alert("http error"+xhr.status)
               }
               return
           }
           xhr.upload.onprogress = function(event){
               console.log("total",event.total)
               console.log("passed",event.loaded)
               if(event.total==event.loaded){
                   console.log("上传成功",xhr)
   
               }
           }
           xhr.open('post', '/api/upload', true);
           xhr.send(formData);
           
           }
   
   }
//init img
if (vm.submit_data.hasOwnProperty('sp{$field_id}_submit_data')){
        if (vm.submit_data["sp{$field_id}_submit_data"]==''){
            Vue.set(vm.user_data,"sp{$field_id}_user_data","/static/img/imageholder.png");
        }else{
            Vue.set(vm.user_data,"sp{$field_id}_user_data", vm.submit_data["sp{$field_id}_submit_data"]);
        }
    }else{
        Vue.$set(vm.user_data,"sp{$field_id}_user_data","");
    }