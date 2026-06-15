# 钉钉本地测试服务

这个目录用于把现有核对 skill 接到钉钉机器人前面，先在本机跑通。

## 目录

- `dingtalk_reconcile_service.py`
  本地 API 服务
- `requirements.txt`
  依赖列表

## 功能

1. 接收本地 HTTP 请求
2. 解析核对指令
3. 调用 skill 的统一入口脚本执行核对
4. 返回摘要结果
5. 可选地把摘要回发到钉钉群机器人 webhook

## 支持的核对类型

- `采购`
- `其他入库`
- `其他出库`
- `退货应收入库`
- `无单退货入库`
- `销售出库`

## 指令格式

推荐格式：

```text
销售出库 2026-03-01 2026-03-31
```

销售出库如果数据量大，可以加：

```text
销售出库 2026-03-01 2026-03-31 day_batch_size=1
```

## 安装依赖

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' -m pip install -r C:\Users\lqc\.codex\skills\reconcile-skill\bot_service\requirements.txt
```

## 启动服务

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\bot_service\dingtalk_reconcile_service.py
```

启动后访问：

- 健康检查：`http://127.0.0.1:8000/health`

## 本地测试

### 方式 1：PowerShell

```powershell
$body = @{
  command = "销售出库 2026-03-01 2026-03-31 day_batch_size=1"
  send_to_dingtalk = $false
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/local/run" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### 方式 2：模拟钉钉消息体

```powershell
$body = @{
  payload = @{
    text = @{
      content = "采购 2026-03-01 2026-03-31"
    }
  }
  send_to_dingtalk = $false
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/dingtalk/message" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## 可选：回发到钉钉群

先配置环境变量：

```powershell
$env:DINGTALK_WEBHOOK = "你的群机器人 webhook"
```

然后把请求里的 `send_to_dingtalk` 改成 `true`。

## 说明

- 当前版本先适合本地验证流程。
- 真正接钉钉事件回调时，后面可能只需要根据钉钉正式消息体格式微调 `/dingtalk/message` 的取文本逻辑。
- 核对结果文件仍然会按原规则输出到桌面。
