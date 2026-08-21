---
asset_id: app.net_profit_t1
layer: 应用层
business_name: T+1 净利核算
status: 部分确认
version:
  baseline: V6.4.9.2（收入成本/进项成本税额，已上线）
  current_release: DWP-V6.4.9.3、DWP-V6.4.9.4、DWP-V6.4.9.5（本月底联动上线）
  pending_versions: [DWP-V6.4.9.6（未评审）]
refresh:
  net_profit_v2: 每日覆盖更新昨日；每月31日（无31日则当月最后一天）、3日、8日覆盖上月，10日覆盖本月
  finance_profit_business: 每日覆盖更新昨日；每月31日（无31日则当月最后一天）、3日、8日覆盖上月，10日覆盖本月
  voucher_subject_mid: 每日回刷最近45天
grain: 日期 + 店铺/货主/商品/供应商/科目/业务属性
source_evidence:
  - { type: product_doc, path: /Users/liuqingchen/Downloads/T+1净利核算表.xlsx, locator: 可见 Sheet：T+1利润版本规划、V6.4.9.3净利指标表、费用名称字典表V6.4.9.3、收入成本V6.4.9.3、科目费用分摊表V6.4.9.3/V6.4.9.5、分摊失败表, observed_at: 2026-08-18 }
---

# T+1 净利核算

主链路：

```text
abroad_production_revenue_profit_import（跨境收入销量原始导入）
       → tmp_data.abroad_production_revenue_profit（当月拆分）

发货 V1 / tmp_data.abroad_production_revenue_profit / 业务多维导入
       + 供应商采购占比分摊
       → doris_app_net_profit_check_report_v2（收入、成本、费用编码）

凭证、费用账单、跨境费用、费控
       → doris_dws_voucher_subject_mid
       → doris_dws_finance_cost_sbjct / doris_dws_finance_cost_sbjct_failure

V2 + 成功/失败科目分摊表 + 科目/费用关系
       → doris_app_finance_profit_business（净利指标中间表）
       → 老板报表/多维净利页面
```

净利 V2 与净利指标中间表基础任务每日覆盖更新昨日；额外在每月 31 日（没有 31 日则当月最后一天）、3 日、8 日覆盖上月，10 日覆盖本月。凭证科目中间表每日回刷最近 45 天。DWP-V6.4.9.3、DWP-V6.4.9.4、DWP-V6.4.9.5 与老板报表 v5.8.6 于本月底联动上线；DWP-V6.4.9.6 尚未评审。

详见：[血缘穿透图](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/net_profit_t1/lineage.md)、[口径规则](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/net_profit_t1/rules.md)、[待确认事项](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/net_profit_t1/open-items.md)。
