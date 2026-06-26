# 商品版运营订货报表代码定位

## Primary Repository

Use `/Users/liuqingchen/工作/代码/srm-ops`.

Use `rg` first. Start broad, then open only the relevant files.

## Report and Purchase Apply Creation

Important files:
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-web/src/main/java/com/jbs/srm/ops/web/controller/PurchaseAdjustReportController.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-service/src/main/java/com/jbs/srm/ops/service/impl/PurchaseAdjustReportServiceImpl.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-service/src/main/java/com/jbs/srm/ops/service/impl/PurchaseApplyServiceImpl.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-service/src/main/java/com/jbs/srm/ops/service/strategy/ProductPurchaseStrategyCreatePurchaseApply.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-service/src/main/java/com/jbs/srm/ops/service/support/PurchaseApplySupport.java`

Useful searches:
- `rg -n "ProductPurchaseStrategyCreatePurchaseApply|商品运营订货|PurchaseAdjustReport|createPurchaseApplyByAdjustReport" /Users/liuqingchen/工作/代码/srm-ops`
- `rg -n "reorderPoint|estimateDaySale|weightDaySale|adjustPurchaseNum|purchaseApplying|canUsedStock|canSaleStock" /Users/liuqingchen/工作/代码/srm-ops`
- `rg -n "PurchaseStrategy|SrmGetPurchaseStrategy|strategy|订货策略" /Users/liuqingchen/工作/代码/srm-ops`

Known behavior:
- 商品报表创建采购申请 sets `apply_source = REPORT_CREATE`.
- `purchase_adjust_report` row is marked created after purchase apply creation.
- `sub_purchase_apply` does not persist the original `purchaseAdjustReportId`.
- Report cleanup can remove old report rows, so old purchase applications may show report-created while the report row no longer exists.

## Transfer Before Submit

Important file:
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-service/src/main/java/com/jbs/srm/ops/service/impl/PurchaseApplyServiceImpl.java`

Relevant methods:
- `submit`
- `purchaseApplyAllocationCalc`
- `getGoodsPurchaseApplySubmitAllocationResponse`
- `allotGoodsAllocationNum`
- `sameWarehouseAllocationAllot`
- `buildAllocationRequest`

Known 商品版 rules:
- 商品版 transfer is same warehouse, different owner.
- Allocation order type is `INNER_WAREHOUSE`.
- Source warehouse equals target warehouse.
- Source owner must be different from target owner.
- Available transfer quantity comes from other owners' excess stock above reorder point.
- Remarks starting with `FX`, `TP`, or `KJ` are filtered from automatic allocation calculation.

Do not confuse with material logic:
- Material purchase transfer can use `ACROSS_WAREHOUSE`.
- Material logic groups by owner/factory warehouse differently.

## Warehouse and Goods Filters

Known 商品版 calculation filters:
- Allowed warehouse types include sale warehouse, replace warehouse, factory warehouse after goods-type filtering.
- Exclude CBS warehouse.
- Keep only warehouses recognized as sales-goods口径 by `GoodsTypeSupportUtil`.
- Available stock must be greater than 0 for transfer contribution.

Useful searches:
- `rg -n "filterWarehouseType|CBS_WAREHOUSE|GoodsTypeSupportUtil|getGoodsTypeByWarehouse|getGoodsTypeEnumByWarehouse" /Users/liuqingchen/工作/代码/srm-ops`
- `rg -n "SALE_WAREHOUSE|REPLACE_WAREHOUSE|FACTORY_WAREHOUSE" /Users/liuqingchen/工作/代码/srm-ops`

## Purchase Application Status and View

Important files:
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-web/src/main/java/com/jbs/srm/ops/web/controller/PurchaseApplyController.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-interface/src/main/java/com/jbs/srm/ops/interfaces/enums/PurchaseApplyStatusEnum.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-service/src/main/java/com/jbs/srm/ops/service/impl/PurchaseApplyServiceImpl.java`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-dao/src/main/resources/mybatis/mapper/PurchaseApplyMapper.xml`
- `/Users/liuqingchen/工作/代码/srm-ops/jbs-srm-ops-dao/src/main/resources/mybatis/mapper/SubPurchaseApplyMapper.xml`

Status enum:
- `EDITING`: 编辑中
- `WAIT_AUDIT`: 待审核
- `AUDIT_PASS`: 已审核
- `CANCEL`: 已取消

Operation constraints:
- Modify/cancel/submit: only `EDITING`.
- Revoke/audit/reject: only `WAIT_AUDIT`.
- Convert order: only audited, not canceled, not transferred details.
- Cancel detail: audited, not transferred, not canceled.
- View/search is not inherently status-blocked. Status is a query filter only.

## Supplier Rules

Known internal supplier behavior:
- Internal suppliers may require warehouse binding checks.
- For internal suppliers, purchase submit/modify checks factory binding warehouse relation.
- Internal suppliers may have maximum suggested delivery date limit, except KJ goods or virtual/special temporary warehouses.

Useful searches:
- `rg -n "isGroupInnerSupplier|GROUP_ORDER_MAX_DAY_NUM|searchInnerSupplierBindingWarehouse|GROUP_INNER_SUPPLIER_BINDING_WAREHOUSE_ERROR" /Users/liuqingchen/工作/代码/srm-ops`
- `rg -n "searchDisableSupplierCodes|SUPPLIER_DISABLED" /Users/liuqingchen/工作/代码/srm-ops`

## Related Investigations Already Known

采购申请显示报表创建但报表查不到:
- Likely because report rows are cleaned after 30 days.
- The purchase application only stores source as report-created, not a stable link back to report row id.

调价和新品报价限制禁用仓:
- In the known `erp-cost` quote-to-purchase-price path, selected warehouse enabled status was not explicitly blocked.
- In srm-ops ordering, some enabled/binding checks exist for internal supplier replace warehouse or supplier status.

采购退货来源:
- Self warehouse return and generation/replace warehouse return affect price source.
- Return price flows to outbound stock order price, refund total amount, and FMS/payable settlement.
