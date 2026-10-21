import csv
import ast
import importlib
import sys
import re
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from fms_source_reconcile import FmsDataset, run_reconciliation, source_queries


def record(code="RK1", goods="001", quantity="1", warehouse="WH0388", unit="U1", ownership="unknown", direction="in", date="2026-09-01", group="127"):
    return dict(order_code=code, goods_code=goods, total_num=quantity, warehouse_code=warehouse,
                unit_code=unit, ownership=ownership, direction=direction,
                business_date=date, psi_group_type=group)


class SourceRulesTest(unittest.TestCase):
    def setUp(self):
        self.dataset = FmsDataset("no_order_return")
        self.addCleanup(self.dataset.close)

    def test_exact_duplicate_without_ownership_counts_once_and_audits_unknown(self):
        self.dataset.add("common", [record()])
        self.dataset.add("factory", [record(group="435")])
        self.assertEqual({("WH0388", "001"): Decimal("1")}, self.dataset.summary())
        self.assertEqual({("RK1", "001"): Decimal("1")}, self.dataset.detail([("WH0388", "001")]))
        r = self.dataset.db.execute("SELECT * FROM audits").fetchone()
        self.assertIn("归属待确认", r["failure_reason"])
        self.assertEqual("common", r["retained_source"])

    def test_factory_ownership_selects_factory(self):
        self.dataset.add("common", [record()])
        self.dataset.add("factory", [record(ownership="factory", group="435")])
        self.assertEqual(Decimal("1"), self.dataset.summary()[("WH0388", "001")])
        self.assertEqual("factory", self.dataset.db.execute("SELECT retained_source FROM audits").fetchone()[0])

    def test_ordinary_ownership_selects_common_without_marking_unknown(self):
        self.dataset.add("common", [record(ownership="ordinary")])
        self.dataset.add("factory", [record()])
        self.assertEqual(Decimal("1"), self.dataset.summary()[("WH0388", "001")])
        row = self.dataset.db.execute("SELECT * FROM audits").fetchone()
        self.assertEqual("common", row["retained_source"])
        self.assertIn("已确认属于普通业务", row["failure_reason"])

    def test_quantity_conflict_is_not_replaced_or_added(self):
        self.dataset.add("common", [record(quantity="2")])
        self.dataset.add("factory", [record(quantity="1")])
        self.assertEqual({}, self.dataset.detail([("WH0388", "001")]))
        self.assertEqual("来源冲突", self.dataset.blocking_issues()[0]["decision"])
        self.assertIn("数量不同", self.dataset.blocking_issues()[0]["failure_reason"])

    def test_warehouse_conflict_with_equal_total_is_returned(self):
        self.dataset.add("common", [record()])
        self.dataset.add("factory", [record(warehouse="WH0979")])
        self.assertEqual(2, len(self.dataset.summary()))
        self.assertIn("仓库不同", self.dataset.blocking_issues()[0]["failure_reason"])

    def test_equal_total_with_different_warehouse_distribution_is_conflict(self):
        self.dataset.add("common", [record(quantity="1"), record(quantity="2", warehouse="WH0979")])
        self.dataset.add("factory", [record(quantity="2"), record(quantity="1", warehouse="WH0979")])
        self.assertEqual("来源冲突", self.dataset.blocking_issues()[0]["decision"])

    def test_unit_conflict(self):
        self.dataset.add("common", [record()])
        self.dataset.add("factory", [record(unit="U2")])
        self.assertIn("单位不同", self.dataset.blocking_issues()[0]["failure_reason"])

    def test_missing_warehouse_is_not_treated_as_a_valid_duplicate(self):
        self.dataset.add("common", [record(warehouse="")])
        self.dataset.add("factory", [record(warehouse="")])
        self.assertEqual("仓库缺失", self.dataset.blocking_issues()[0]["decision"])

    def test_legitimate_split_rows_are_summed_before_comparing(self):
        self.dataset.add("common", [record(quantity="0.1"), record(quantity="0.2")])
        self.dataset.add("factory", [record(quantity="0.3")])
        self.assertEqual(Decimal("0.3"), self.dataset.summary()[("WH0388", "001")])
        self.assertFalse(self.dataset.blocking_issues())

    def test_single_source_remains_valid(self):
        self.dataset.add("common", [record(code="RK1")])
        self.dataset.add("factory", [record(code="RK2", quantity="2")])
        self.assertEqual(Decimal("3"), self.dataset.summary()[("WH0388", "001")])

    def test_confirmed_factory_without_factory_record_is_visible(self):
        self.dataset.add("common", [record(ownership="factory")])
        self.assertEqual("产销来源缺失", self.dataset.blocking_issues()[0]["decision"])
        self.assertEqual({}, self.dataset.detail([("WH0388", "001")]))

    def test_ownership_conflict_is_visible(self):
        self.dataset.add("common", [record(ownership="ordinary")])
        self.dataset.add("factory", [record(ownership="factory")])
        self.assertEqual("归属冲突", self.dataset.blocking_issues()[0]["decision"])

    def test_zero_negative_and_null_are_distinguished(self):
        self.dataset.add("common", [record(code="zero", quantity="0"), record(code="negative", quantity="-1"), record(code="null", quantity=None)])
        detail = self.dataset.detail([("WH0388", "001")])
        self.assertEqual(Decimal("0"), detail[("zero", "001")])
        self.assertEqual(Decimal("-1"), detail[("negative", "001")])
        self.assertEqual("数量缺失", self.dataset.blocking_issues()[0]["decision"])

    def test_different_dates_in_range_are_audited_not_double_counted(self):
        self.dataset.add("common", [record()])
        self.dataset.add("factory", [record(date="2026-09-02")])
        self.assertEqual(Decimal("1"), self.dataset.summary()[("WH0388", "001")])
        self.assertIn("业务日期不同", self.dataset.db.execute("SELECT failure_reason FROM audits").fetchone()[0])

    def test_directions_and_goods_are_not_collapsed(self):
        self.dataset.add("common", [record(direction="in"), record(direction="out"), record(goods="002")])
        self.dataset.add("factory", [record(direction="in")])
        self.assertEqual(Decimal("2"), self.dataset.summary()[("WH0388", "001")])
        self.assertEqual(Decimal("1"), self.dataset.summary()[("WH0388", "002")])

    def test_summary_cancellation_does_not_hide_conflicts(self):
        self.dataset.add("common", [record(quantity="2"), record(code="RK2", quantity="1")])
        self.dataset.add("factory", [record(quantity="1"), record(code="RK2", quantity="2")])
        self.assertEqual(2, len(self.dataset.blocking_issues()))

    def test_audit_contains_both_original_values_and_table_names(self):
        self.dataset.add("common", [record(quantity="2")])
        self.dataset.add("factory", [record(quantity="1")])
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "audit.csv"
            self.dataset.write_audit(target)
            with target.open(encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual("fms_cost.psi_sales", rows[0]["common_table"])
            self.assertEqual("fms_cost.psi_factory_sales", rows[0]["factory_table"])
            self.assertIn('"quantity": "2"', rows[0]["common_records"])


MODULES = {
    "no_order_return": "no_order_return_reconcile",
    "return_income": "return_income_reconcile",
    "sales_outbound": "sales_outbound_reconcile",
    "purchase": "purchase_in_stock_reconcile",
    "other_in": "other_in_stock_reconcile",
    "other_out": "other_out_stock_reconcile",
}


class AdaptersTest(unittest.TestCase):
    def test_all_six_types_use_the_same_snapshot_for_summary_and_detail(self):
        for kind, name in MODULES.items():
            with self.subTest(kind=kind), FmsSnapshotFixture(kind) as fixture:
                module = importlib.import_module(name)
                conn = SimpleNamespace(_fms_source_dataset=((kind, "2026-09-01 00:00:00", "2026-09-30 23:59:59", 1 if kind == "sales_outbound" else None), fixture.dataset))
                summary = module.fetch_fms_summary if kind == "purchase" else module.fetch_left_summary
                detail = module.fetch_fms_detail if kind == "purchase" else module.fetch_left_detail
                args = [conn, "2026-09-01 00:00:00", "2026-09-30 23:59:59"]
                self.assertEqual(Decimal("1"), summary(*args, *([1] if kind == "sales_outbound" else []))[("WH0388", "001")])
                self.assertEqual(Decimal("1"), detail(*args, [("WH0388", "001")], 100, *([1] if kind == "sales_outbound" else []))[("RK1", "001")])

    def test_sql_maps_purchase_other_and_sales_fields_and_filters(self):
        with patch("fms_source_reconcile._columns", return_value={"unit_code", "shop_code"}):
            for kind, name in MODULES.items():
                module = importlib.import_module(name)
                queries = source_queries(None, module, kind)
                for source, sql, params, date_only in queries:
                    self.assertEqual(sql.count("%s"), 2 + len(params))
                if kind == "purchase":
                    self.assertIn("r.business_no AS order_code", queries[0][1])
                    self.assertIn("r.stock_order_code AS order_code", queries[1][1])
                    self.assertIn("d.refund_num", queries[0][1])
                    self.assertNotIn("w.warehouse_use_type = 4", queries[0][1])
                if kind.startswith("other_"):
                    self.assertIn("d.sku_code AS goods_code", queries[0][1])
                    self.assertIn("d.code AS goods_code", queries[1][1])
                    self.assertNotIn("w.warehouse_use_type = 4", queries[0][1])
                if kind == "no_order_return":
                    self.assertEqual(module.FACTORY_PSI_GROUP_TYPES, ["426", "427", "428", "435", "438", "439"])

    def test_runner_returns_source_conflict_even_when_summary_totals_match(self):
        module = importlib.import_module("no_order_return_reconcile")
        dataset = FmsDataset("no_order_return")
        self.addCleanup(dataset.close)
        dataset.add("common", [record(quantity="2")])
        dataset.add("factory", [record(quantity="1")])
        with tempfile.TemporaryDirectory() as folder:
            args = SimpleNamespace(start_time="2026-09-01 00:00:00", end_time="2026-09-30 23:59:59", batch_size=100,
                                   summary_output=str(Path(folder)/"summary.csv"), detail_output=str(Path(folder)/"detail.csv"))
            with patch("fms_source_reconcile.get_fms_dataset", return_value=dataset), patch.object(module, "fetch_right_summary", return_value={("WH0388", "001"): Decimal("0")}), patch.object(module, "fetch_right_detail", return_value={("RK1", "001"): Decimal("0")}), patch.object(module, "fetch_iom_order_meta", return_value={}):
                run_reconciliation(module, None, args, "no_order_return")
            with open(args.detail_output, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual("来源冲突", rows[0]["message"])
            self.assertEqual("", rows[0]["fms_num"])

    def test_runner_distinguishes_missing_order_from_zero_quantity(self):
        module = importlib.import_module("no_order_return_reconcile")
        dataset = FmsDataset("no_order_return")
        self.addCleanup(dataset.close)
        dataset.add("common", [record(quantity="0")])
        with tempfile.TemporaryDirectory() as folder:
            args = SimpleNamespace(start_time="2026-09-01 00:00:00", end_time="2026-09-30 23:59:59", batch_size=100,
                                   summary_output=str(Path(folder)/"summary.csv"), detail_output=str(Path(folder)/"detail.csv"))
            with patch("fms_source_reconcile.get_fms_dataset", return_value=dataset), patch.object(module, "fetch_right_summary", return_value={}), patch.object(module, "fetch_right_detail", return_value={}), patch.object(module, "fetch_iom_order_meta", return_value={}):
                run_reconciliation(module, None, args, "no_order_return")
            with open(args.detail_output, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual("单据存在性不一致", rows[0]["message"])
            self.assertEqual("0", rows[0]["fms_num"])


class BotOutputTest(unittest.TestCase):
    def test_source_conflicts_and_audit_file_are_in_bot_reply(self):
        # 仅载入输出解析函数，不启动服务、不导入 HTTP 依赖也不发送消息。
        path = SCRIPTS.parent / "bot_service" / "dingtalk_reconcile_service.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"parse_run_output", "build_reply_text"}
                 or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SUMMARY_PATTERNS" for t in node.targets)]
        namespace = {"re": re, "Dict": dict, "Any": object}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
        parsed = namespace["parse_run_output"]("汇总对比 10 行，汇总差异组合 1 个，单据差异 1 条\n跨来源重复 43 组，来源异常 1 组\n来源处理文件: audit.csv", "summary.csv", "detail.csv")
        parsed.update(type_label="无单退货", start_time="2026-09-01", end_time="2026-09-30")
        reply = namespace["build_reply_text"](parsed)
        self.assertIn("来源异常：1 组", reply)
        self.assertIn("跨来源重复：43 组", reply)
        self.assertIn("audit.csv", reply)


class FmsSnapshotFixture:
    def __init__(self, kind):
        self.dataset = FmsDataset(kind)
        self.dataset.add("common", [record()])
        self.dataset.add("factory", [record()])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.dataset.close()


if __name__ == "__main__":
    unittest.main()
