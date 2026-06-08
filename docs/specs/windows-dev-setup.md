# Windows 本地运行与调试说明

最后更新：2026-06-08

## 1. 目标

本文档用于指导在 `Windows` 电脑上运行和调试当前项目骨架，便于后续开发：

- 游戏窗口发现与连接
- Win32 截图与输入
- 日志记录
- 控制台实时进度展示

## 2. 推荐开发环境

建议使用以下环境组合：

- Windows 10 或 Windows 11
- Python 3.9 或更高版本
- Git
- VS Code

建议把游戏客户端与本项目放在同一台 Windows 机器上运行，这样最方便调试：

- 窗口句柄
- 截图结果
- 鼠标点击
- 分辨率适配

## 3. 获取项目

在 Windows 本地克隆仓库：

```bash
git clone <你的仓库地址>
cd MaaLearn
```

如果你是直接复制目录到 Windows，也可以正常使用，但后续更建议通过 Git 管理版本。

## 4. 创建虚拟环境

建议在项目根目录执行：

```bash
python -m venv .venv
```

激活虚拟环境：

```bash
.venv\Scripts\activate
```

如果 PowerShell 的脚本执行策略拦截激活命令，可先在当前用户范围内放开：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 5. 安装当前项目

当前项目还处于骨架阶段，依赖很少。

推荐两种运行方式。

### 方式一：源码方式运行

这是当前最简单的方式：

```bash
set PYTHONPATH=src
python -m czn_automation
```

如果使用 PowerShell：

```powershell
$env:PYTHONPATH = "src"
python -m czn_automation
```

### 方式二：可编辑安装

如果你更习惯直接执行模块，可以使用：

```bash
pip install -e .
python -m czn_automation
```

## 6. 当前运行结果说明

在 Windows 运行当前骨架时，程序会执行：

1. 加载配置
2. 初始化日志
3. 初始化控制台实时进度
4. 进入窗口连接阶段
5. 执行窗口扫描占位逻辑

当前尚未接入真正的 Win32 枚举实现，因此这一步暂时只是框架验证。

## 7. 日志位置

运行日志会写到：

- [debug/logs/app.log](/Users/michael/Documents/MaaLearn/debug/logs/app.log)

你可以一边运行程序，一边查看该日志文件，确认当前执行到了哪个节点。

## 8. 控制台实时进度

程序启动后，控制台会输出类似：

```text
[阶段] 初始化
[步骤] 加载配置与运行上下文
[状态] 进行中
[详情] environment=development

[阶段] 窗口连接
[步骤] 扫描系统窗口
[状态] 进行中
[详情] 当前为占位实现，后续接入 Win32 窗口枚举
```

这部分输出用于帮助你实时观察：

- 当前阶段
- 当前步骤
- 当前状态
- 当前细节说明

## 9. VS Code 调试

仓库已经包含 VS Code 配置文件：

- [launch.json](/Users/michael/Documents/MaaLearn/.vscode/launch.json)
- [settings.json](/Users/michael/Documents/MaaLearn/.vscode/settings.json)

### 使用步骤

1. 用 VS Code 打开项目根目录
2. 选择 `.venv` 作为 Python 解释器
3. 打开“运行和调试”
4. 选择 `运行 czn_automation`
5. 启动调试

### 当前调试配置作用

该配置会：

- 以模块方式启动 `czn_automation`
- 自动设置 `PYTHONPATH=src`
- 使用 VS Code 集成终端显示输出

## 10. 推荐调试习惯

建议在 Windows 上采用以下方式工作：

- VS Code 用于断点调试
- 一个终端用于手动运行程序
- 一个终端用于查看日志
- 游戏窗口保持固定分辨率

这样后面在调试窗口连接和截图时会比较清晰。

## 11. 窗口连接阶段重点关注什么

等我们开始实现 Win32 窗口控制后，建议重点观察以下信息：

- 扫描到多少个候选窗口
- 窗口标题是否符合预期
- 句柄是否稳定
- 坐标和尺寸是否正确
- 游戏是否处于固定分辨率

这些信息后续都应出现在控制台和日志中。

## 12. 后续建议

Windows 上下一阶段最适合做的是：

1. 实现真实的窗口枚举逻辑
2. 输出候选窗口列表
3. 匹配目标游戏窗口
4. 校验窗口尺寸
5. 将结果写入日志与控制台
