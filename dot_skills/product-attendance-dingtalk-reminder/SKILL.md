---
name: product-attendance-dingtalk-reminder
description: Use when querying Product Group attendance records, configuring scheduled clock-in reminders, or sending signed DingTalk custom-robot reminders for missing clock-ins.
---

# Product Group Attendance DingTalk Reminder

Use this skill for the Product Group attendance reminder only. Do not use it for task reminders, leave approval, or general attendance reporting.

## Scope

- Department: Product Group (`dept_id=393819645`)
- Attendance source: `hris_ads.attendance_records`
- Time zone: `Asia/Shanghai`
- Roster: 刘庆晨 (11723), 雷奇颖 (13463), 蔡宗敏 (13554), 杨茹 (14984), 朱琳 (15281), 文秋红 (26695)

## Reminder Rules

| Time | Missing condition | Message |
|---|---|---|
| 08:55 | No record for the employee on the current `dt` | Only @ missing employees: `请及时完成上班打卡。` |
| 19:30 | Fewer than two records for the employee on the current `dt` | Only @ missing employees: `请及时完成下班打卡。` |

When nobody is missing, send only `【产品组打卡提醒】上班打卡：均已完成。` or `【产品组打卡提醒】下班打卡：均已完成。` Do not list names, mention employees, or expose punch times.

## Signed Robot Delivery

Read database settings from `~/.config/db-profiles/doris.env` and robot settings from `~/.config/dingtalk-bots/product-attendance.env`. These files are local-only; never add their contents to skills, prompts, logs, Git, or messages.

The custom robot has signing enabled. For every delivery, calculate:

```text
timestamp = current Unix time in milliseconds
sign = base64(HMAC-SHA256(secret, timestamp + "\n" + secret))
```

URL-encode `sign`, append `timestamp` and `sign` to the robot endpoint, then send a `text` payload. Use DingTalk `atUserIds` for only the missing employees. Names alone do not create real mentions.

## Safety Checks

1. Query first; do not infer missing clock-ins.
2. Use `deleted=0` and the local calendar date for `dt`.
3. Do not send duplicate messages for the same run.
4. Report only the missing-count and send result after delivery.
