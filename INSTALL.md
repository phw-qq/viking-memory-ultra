# OpenViking 安装指南

## 快速安装

### 方法1：从GitHub克隆（推荐）
```bash
cd ~/.workbuddy/skills/
git clone https://github.com/YOUR_USERNAME/viking-memory-ultra.git
```

### 方法2：手动下载
1. 下载最新release的zip文件
2. 解压到 `~/.workbuddy/skills/viking-memory-ultra/`
3. 确保目录结构：
   ```
   viking-memory-ultra/
   ├── scripts/*.py
   ├── SKILL.md
   └── _meta.json
   ```

### 方法3：使用WorkBuddy skill管理
```
/skills install viking-memory-ultra
```

## 验证安装

运行测试套件：
```bash
cd ~/.workbuddy/skills/viking-memory-ultra/
python test_suite.py
```

或手动测试：
```bash
python scripts/sv_fact.py add '{"type":"test","content":"安装测试"}'
python scripts/sv_read.py ~/.workbuddy/memory/
```

## 依赖要求

- Python 3.8+
- 标准库（无需额外安装）：
  - json, os, sys, math, re, datetime, pathlib

## 兼容性

| 平台 | 状态 | 说明 |
|------|------|------|
| WorkBuddy | ✅ 完全兼容 | 原生支持 |
| Hermes | ⚠️ 可能兼容 | 需要测试 |
| OpenClaw | ❌ 不兼容 | 架构不同 |
| Claw-Code | ✅ 完全兼容 | WorkBuddy衍生版 |

## 卸载

```bash
rm -rf ~/.workbuddy/skills/viking-memory-ultra/
```

## 故障排查

### 问题1：脚本无法执行
**解决**：检查Python版本
```bash
python --version  # 需要 3.8+
```

### 问题2：找不到memory目录
**解决**：创建目录
```bash
mkdir -p ~/.workbuddy/memory/
```

### 问题3：权限错误
**解决**：检查目录权限
```bash
chmod +x ~/.workbuddy/skills/viking-memory-ultra/scripts/*.py
```

## 支持

- GitHub Issues: https://github.com/YOUR_USERNAME/viking-memory-ultra/issues
- 文档: https://github.com/YOUR_USERNAME/viking-memory-ultra/wiki
