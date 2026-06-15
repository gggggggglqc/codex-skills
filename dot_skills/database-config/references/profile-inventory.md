# Database Profile Inventory

This inventory intentionally omits passwords and other secrets.

| Profile | Type | Purpose | Secret Location |
| --- | --- | --- | --- |
| `erp-mysql` | MySQL | ERP/FMS read-only queries, voucher/payment/expense checks | `~/.config/db-profiles/erp-mysql.env` |
| `doris` | Doris/MySQL protocol | Doris warehouse read-only queries, finance and net-profit checks | `~/.config/db-profiles/doris.env` |
| `wms-mysql` | MySQL | WMS/JLS read-only task reminder queries | `~/.config/db-profiles/wms-mysql.env` |

## Handling Rules

- Do not paste profile file contents into chat.
- Do not commit profile files.
- Do not add profile files to chezmoi.
- Rotate credentials immediately if they were ever committed to a public repository.
