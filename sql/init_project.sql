CREATE TABLE `cms_template` (
  `template_id` int(11) NOT NULL COMMENT '模板id',
  `project_id` int(11) NOT NULL COMMENT '项目(站点)id',
  `template_name` char(128) NOT NULL COMMENT '模板名称',
  `template_summary` text NOT NULL COMMENT '模板摘要',
  `template_view` text NOT NULL COMMENT '模板视图',
  `publish_callback` text NOT NULL COMMENT '文档回调配置',
  `publish_url` varchar(512) NOT NULL COMMENT '发布路径模板',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `allow` text NOT NULL COMMENT '受信名单',
  `enable` tinyint(1) NOT NULL COMMENT '是否启用'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板表';
ALTER TABLE `cms_template`
  ADD PRIMARY KEY (`template_id`),
  ADD KEY `project_id` (`project_id`),
  ADD KEY `template_name` (`template_name`),
  ADD KEY `enable` (`enable`);
ALTER TABLE `cms_template`
  MODIFY `template_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '模板id';COMMIT;
CREATE TABLE `cms_template_field` (
  `field_id` int(11) NOT NULL COMMENT '模板域id',
  `template_id` int(11) NOT NULL COMMENT '模板id',
  `field_name` char(128) NOT NULL COMMENT '模板域名称',
  `field_type` char(64) NOT NULL COMMENT '模板域类型',
  `rule` varchar(4096) NOT NULL COMMENT '模板域规则',
  `min_size` int(11) NOT NULL COMMENT '最小长度',
  `max_size` int(11) NOT NULL COMMENT '最大长度',
  `display_order` int(11) NOT NULL COMMENT '显示顺序',
  `is_show` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否显示',
  `algorithm` text NOT NULL COMMENT '算法',
  `default_value` text NOT NULL COMMENT '默认值',
  `fl_field` char(32) NOT NULL DEFAULT '' COMMENT '全文引擎绑定字段',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `enable` tinyint(1) NOT NULL COMMENT '是否启用'
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板域表';
ALTER TABLE `cms_template_field`
  ADD PRIMARY KEY (`field_id`),
  ADD KEY `template_id` (`template_id`),
  ADD KEY `field_name` (`field_name`),
  ADD KEY `field_type` (`field_type`),
  ADD KEY `display_order` (`display_order`),
  ADD KEY `enable` (`enable`);
ALTER TABLE `cms_template_field`
  MODIFY `field_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '模板域id';
CREATE TABLE `cms_template_statistics` (
  `template_id` int(11) NOT NULL COMMENT '模板id',
  `document_count` int(11) NOT NULL COMMENT '文档数'
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
ALTER TABLE `cms_template_statistics`
  ADD UNIQUE KEY `template_id` (`template_id`),
  ADD KEY `document_count` (`document_count`);
CREATE TABLE `cms_variable` (
  `variable_id` int(11) NOT NULL COMMENT '变量id',
  `project_id` int(11) NOT NULL COMMENT '所属项目id',
  `scope` enum('GLOBAL','TEMPLATE') NOT NULL COMMENT '作用域',
  `variable_name` char(64) NOT NULL COMMENT '变量名',
  `variable_type` enum('INT','STRING','DATE','ARRAY') NOT NULL COMMENT '变量类型',
  `variable_value` text NOT NULL COMMENT '变量值',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `enable` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否有效'
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='全局变量表';
ALTER TABLE `cms_variable`
  ADD PRIMARY KEY (`variable_id`),
  ADD KEY `project_id` (`project_id`),
  ADD KEY `scope` (`scope`),
  ADD KEY `enable` (`enable`);
ALTER TABLE `cms_variable` MODIFY `variable_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '变量id';
CREATE TABLE `cms_component` (
  `component_id` int(11) NOT NULL COMMENT '组件id',
  `component_name` char(32) NOT NULL COMMENT '组件名称',
  `component_cname` char(128) NOT NULL COMMENT '组件中文名',
  `component_summary` text NOT NULL COMMENT '组件描述',
  `component_symbol` varchar(1024) NOT NULL DEFAULT '<Component:unknown>' COMMENT '组件符号',
  `component_content` text NOT NULL COMMENT '组件内容',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `enable` tinyint(4) NOT NULL DEFAULT '1' COMMENT '是否可用'
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件表';
CREATE TABLE `cms_component_data` (
  `data_id` bigint(20) NOT NULL COMMENT '数据项id',
  `template_id` int(11) NOT NULL COMMENT '模板id',
  `document_id` int(11) NOT NULL COMMENT '文档id',
  `component_id` int(11) NOT NULL COMMENT '组件id',
  `component_tag` char(32) NOT NULL COMMENT '组件标签',
  `data_day` bigint(20) NOT NULL DEFAULT '0' COMMENT '日数据',
  `data_month` bigint(20) NOT NULL DEFAULT '0' COMMENT '月数据',
  `data_total` bigint(20) NOT NULL DEFAULT '0' COMMENT '总数据',
  `effect_day` date NOT NULL DEFAULT '1900-01-01' COMMENT '影响时间(日)',
  `effect_month` date NOT NULL DEFAULT '1900-01-01' COMMENT '影响时间(月)',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间'
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组件数据统计表';
ALTER TABLE `cms_component`
  ADD PRIMARY KEY (`component_id`),
  ADD UNIQUE KEY `component_name` (`component_name`),
  ADD KEY `enable` (`enable`),
  ADD KEY `create_time` (`create_time`);
ALTER TABLE `cms_component_data`
  ADD PRIMARY KEY (`data_id`),
  ADD KEY `document_id` (`document_id`),
  ADD KEY `component_id` (`component_id`),
  ADD KEY `component_tag` (`component_tag`),
  ADD KEY `data_value` (`data_day`),
  ADD KEY `effect_date` (`effect_day`),
  ADD KEY `create_time` (`create_time`),
  ADD KEY `update_time` (`update_time`),
  ADD KEY `data_month` (`data_month`),
  ADD KEY `data_total` (`data_total`),
  ADD KEY `effect_month` (`effect_month`),
  ADD KEY `template_document_id` (`template_id`,`document_id`) USING BTREE,
  ADD KEY `template_id` (`template_id`);
ALTER TABLE `cms_component` MODIFY `component_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '组件id';
ALTER TABLE `cms_component_data` MODIFY `data_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '数据项id';
