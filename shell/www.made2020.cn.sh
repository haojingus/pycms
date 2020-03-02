cd ./site/$1 && rsync -Ravz ./$2 rsync_cms@175.24.44.40::cms/ --password-file=/etc/rsync_client.password && cd ../../
