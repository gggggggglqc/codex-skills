from pathlib import Path
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]


class WhitelistWarehouseTest(unittest.TestCase):
    def test_wh0979_is_present_at_every_existing_whitelist_filter(self):
        targets = [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "scripts").glob("*.py"))]
        missing = []

        for path in targets:
            for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if "WH0882" in line and "WH0979" not in line:
                    missing.append(f"{path.relative_to(SKILL_DIR)}:{line_number}")

        self.assertEqual([], missing, f"WH0979 missing from whitelist entries: {missing}")


if __name__ == "__main__":
    unittest.main()
