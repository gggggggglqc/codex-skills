-- 用户于 2026-08-13 提供的销售模块首批 ODS 建表语句。
-- 原始文本同时保留在会话记录；此文件作为本资产库的可追溯来源副本。

CREATE TABLE dp_ods.doris_ods_dms_refund_delivery_order (...)
COMMENT '分销退货发货主单';

CREATE TABLE dp_ods.doris_ods_dms_sub_delivery_order (...)
COMMENT '分销发货单子单';

CREATE TABLE dp_ods.doris_ods_dms_trade_order (...)
COMMENT '分销订单主单';

CREATE TABLE dp_ods.doris_ods_dms_sub_trade_order (...)
COMMENT '分销订单子单';

CREATE TABLE dp_ods.doris_ods_oms_order (...)
COMMENT '原始子单订单';

CREATE TABLE dp_ods.doris_ods_oms_refund (...)
COMMENT '原始退单主单';

-- 注意：本文件记录本次已接收的表清单和语义。完整字段 DDL 已被结构化登记到各表 fields.md。
