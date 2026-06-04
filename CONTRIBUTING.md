# 贡献指南 Contributing Guide

感谢您对本项目的关注！欢迎提交问题报告、功能建议或代码贡献。

## 🐛 报告问题

如果您遇到 bug 或有功能建议，请：

1. 先搜索 [Issues](https://github.com/YOUR_USERNAME/mortal-analysis/issues) 确认没有重复
2. 创建新 Issue 并提供以下信息：
   - **问题描述**：清晰描述遇到的问题
   - **复现步骤**：详细的操作步骤
   - **环境信息**：操作系统、Python版本
   - **错误日志**：相关的错误信息或截图
   - **预期行为**：您期望的正确行为

## 💡 功能建议

如果您有新功能建议：

1. 创建 Feature Request Issue
2. 说明：
   - 功能用途和使用场景
   - 期望的实现方式
   - 是否愿意自己实现

## 🔧 代码贡献

### 开发流程

1. **Fork 项目**
   ```bash
   # 点击右上角 Fork 按钮
   ```

2. **Clone 到本地**
   ```bash
   git clone https://github.com/YOUR_USERNAME/mortal-analysis.git
   cd mortal-analysis
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行修改**
   - 遵循现有代码风格
   - 添加必要的注释（中文或英文）
   - 测试您的改动

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加XXX功能"
   # 或
   git commit -m "fix: 修复XXX问题"
   ```

6. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 详细描述改动内容
   - 引用相关的 Issue
   - 等待 review

### Commit 规范

请使用语义化提交信息：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加玉之间数据爬取支持
fix: 修复网页爬取时间解析错误
docs: 更新安装说明
```

## 📝 代码规范

- **Python 代码**：
  - 使用 UTF-8 编码
  - 遵循 PEP 8 风格（宽松）
  - 函数和类添加文档字符串

- **Batch 脚本**：
  - 使用纯英文避免编码问题
  - 添加清晰的 echo 提示信息

- **文档**：
  - README 使用中文
  - 代码注释中英文均可
  - 保持格式清晰

## 🙏 行为准则

- 尊重所有贡献者
- 友善地讨论和提问
- 接受建设性批评
- 专注于对项目最有利的方案

## ❓ 需要帮助？

- 查看 [README.md](./README.md) 了解项目详情
- 浏览已有的 Issues 和 Pull Requests
- 在 Issue 中提问

再次感谢您的贡献！🎉
