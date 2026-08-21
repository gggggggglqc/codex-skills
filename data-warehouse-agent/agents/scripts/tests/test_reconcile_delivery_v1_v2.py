import unittest
from decimal import Decimal

from agents.scripts.reconcile_delivery_v1_v2 import build_rules, is_within_tolerance


class DeliveryV1V2RuleTest(unittest.TestCase):
    def test_relative_tolerance_accepts_precision_difference(self):
        self.assertTrue(is_within_tolerance(Decimal("129.99"), Decimal("3495074.32")))
        self.assertFalse(is_within_tolerance(Decimal("400"), Decimal("3495074.32")))

    def test_build_rules_contains_the_seven_confirmed_mappings(self):
        rules = build_rules()

        self.assertEqual(
            [rule["rule_id"] for rule in rules],
            [
                "REC-REV-001",
                "REC-REV-002",
                "REC-COST-001",
                "REC-TAX-001",
                "REC-TAX-003",
                "REC-TAX-002",
                "REC-COST-002",
            ],
        )
        self.assertEqual(rules[0]["v1_field"], "sales_amount")
        self.assertEqual(rules[0]["expense_code"], "EP001")
        self.assertEqual(rules[0]["v1_cbs_platform"], 0)
        self.assertEqual(rules[0]["v1_exclude_business_group"], 6)
        self.assertIn("estimate_brand_quotation", rules[0]["v1_sql_expression"])
        self.assertEqual(rules[1]["country_type"], 1)
        self.assertEqual(rules[-1]["v1_field"], "rebate_amount")
        self.assertEqual(rules[-1]["expense_code"], "EP038")
        self.assertEqual(rules[-2]["v2_sign"], -1)
        self.assertEqual(rules[-1]["v2_sign"], -1)


if __name__ == "__main__":
    unittest.main()
