# 团队安装与调用

## 轻量安装（推荐）

克隆仓库后，仅复制数仓 Skills 到本机 Codex 技能目录，并保留仓库克隆目录作为资产库：

```bash
git clone git@github.com:gggggggglqc/codex-skills.git ~/workspace/codex-skills
for skill in data-warehouse-collaboration data-warehouse-document-versioning data-warehouse-metric-impact data-warehouse-engineering-design data-warehouse-quality-operations data-warehouse-diagnosis data-product-requirement-lifecycle; do
  mkdir -p "$HOME/.skills/$skill"
  rsync -a "$HOME/workspace/codex-skills/dot_skills/$skill/" "$HOME/.skills/$skill/"
done
```

重启或新开 Codex 任务后即可发现 Skills。Skill 会优先读取 `~/data-warehouse-agent/`；未部署时会使用本地 `codex-skills/data-warehouse-agent/` 克隆目录。

## 调用示例

- `$data-warehouse-collaboration`：分析这条需求应由哪个数仓 Agent 处理。
- `$data-warehouse-document-versioning`：将一个钉钉产品文档登记为正式来源并列出版本差异。
- `$data-warehouse-metric-impact`：分析“近 365 天收入门槛”调整的受影响表和验收条件。
- `$data-warehouse-diagnosis`：排查某店铺在老板报表没有收入的证据链。
- `$data-product-requirement-lifecycle`：把已确认的需求转换为 PRD、文档修改清单和上线验收项。

不要提交原始 XLSX/CSV/DOCX、业务明细、账号、密钥或缓存；正式原文通过 `sources/register.yaml` 的钉钉链接访问。
