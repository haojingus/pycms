CREATE TABLE `{$tblname}` (
	`document_id` int(11) NOT NULL COMMENT '文档id',
	`create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
	`publish_time` timestamp NULL DEFAULT NULL COMMENT '发布时间',
	`is_delete` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除 ',
	`create_user` char(32) NOT NULL COMMENT '创建者',
	`modify_user` char(32) NOT NULL COMMENT '修改者',
	`publish_user` char(32) DEFAULT NULL COMMENT '发布人',
	`publish_url` varchar(1024) DEFAULT NULL COMMENT '发布url'
	) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT = DYNAMIC;
ALTER TABLE `{$tblname}`
  ADD PRIMARY KEY (`document_id`),
  ADD KEY `create_time` (`create_time`),
  ADD KEY `is_delete` (`is_delete`),
  ADD KEY `create_user` (`create_user`),
  ADD KEY `publish_user` (`publish_user`);
ALTER TABLE `{$tblname}`
  MODIFY `document_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '文档id';
