# Windows 本地运行、调试与验证说明

最后更新：2026-06-08

## 1. 目标

本文档用于指导在 `Windows` 电脑上运行、调试并验证当前项目骨架，便于后续开发：

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
cd MAAForChaos
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
5. 扫描可见顶层窗口
6. 按标题关键字匹配目标窗口
7. 校验目标窗口分辨率是否为 `1920x1080`
8. 如果连接成功，保存首张窗口截图

当前版本已经接入第一版 Win32 窗口枚举与截图验证能力，适合做以下验证：

- 是否能找到 `卡厄思梦境` 窗口
- 是否能匹配到标题关键字
- 是否能识别固定分辨率 `1920x1080`
- 是否能成功保存窗口客户区截图

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
[详情] 正在枚举可见顶层窗口
```

这部分输出用于帮助你实时观察：

- 当前阶段
- 当前步骤
- 当前状态
- 当前细节说明

如果窗口连接成功，后面还应出现：

```text
[阶段] 截图验证
[步骤] 保存首张窗口截图
[状态] 成功
[详情] ...debug/screenshots/last_window_capture.bmp
```

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

## 13. 本轮验证步骤

建议严格按以下顺序执行。

### 13.1 启动前准备

1. 启动 `卡厄思梦境 PC 客户端`
2. 将游戏切换为窗口模式或固定窗口模式
3. 确认客户区分辨率为 `1920x1080`
4. 保证窗口未最小化
5. 保证窗口标题中能看到 `卡厄思梦境` 或 `Chaos Zero Nightmare`

### 13.2 进入项目目录并激活环境

```powershell
cd <你的项目目录>\MAAForChaos
.venv\Scripts\activate
```

如果还没创建虚拟环境，可先执行：

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 13.3 安装或更新项目

如果是首次运行，建议执行：

```powershell
pip install -e .
```

如果只是同步了最新代码，也可以重新执行一次，确保本地入口与代码一致。

### 13.4 启动验证程序

推荐方式一：

```powershell
python -m czn_automation
```

如果你没有执行 `pip install -e .`，就用方式二：

```powershell
$env:PYTHONPATH = "src"
python -m czn_automation
```

## 14. 验证时要看什么

### 14.1 控制台输出

你需要重点确认是否出现以下阶段：

1. `初始化`
2. `窗口连接`
3. `截图验证`

理想情况会看到：

```text
[阶段] 窗口连接
[步骤] 连接目标窗口
[状态] 成功

[阶段] 截图验证
[步骤] 保存首张窗口截图
[状态] 成功
```

如果失败，注意看失败停在哪一步：

- 扫描系统窗口
- 匹配目标窗口
- 连接目标窗口
- 保存首张窗口截图

### 14.2 日志文件

打开以下文件查看详细日志：

- [debug/logs/app.log](/Users/michael/Documents/MaaLearn/debug/logs/app.log)

重点关注：

- 扫描到了多少候选窗口
- 每个候选窗口的标题和尺寸
- 标题关键字匹配了几个窗口
- 最终选中了哪个窗口
- 是否因为分辨率不符而失败
- 截图是否保存成功

### 14.3 截图文件

如果连接成功，程序会尝试保存截图到：

- [debug/screenshots/last_window_capture.bmp](/Users/michael/Documents/MaaLearn/debug/screenshots/last_window_capture.bmp)

你需要确认：

- 文件是否生成
- 打开后内容是否真的是游戏窗口客户区
- 是否存在黑屏、纯白、错位或截到别的窗口的情况

## 15. 本轮验收标准

本轮 Windows 验证可按下面标准判断结果：

### 通过

- 程序找到目标游戏窗口
- 程序确认窗口分辨率为 `1920x1080`
- 成功生成 `last_window_capture.bmp`
- 截图内容正确

### 部分通过

- 找到了标题匹配窗口
- 但分辨率不符合要求

或者：

- 找到了窗口
- 但截图失败

### 未通过

- 没有找到标题匹配窗口
- 或候选窗口信息明显不对

## 16. 反馈时请带上这些信息

如果你跑完要把结果发给我，建议至少带上：

1. 控制台完整输出
2. `debug/logs/app.log` 内容
3. 游戏窗口实际标题
4. 游戏是否确认是 `1920x1080`
5. 是否生成了 `last_window_capture.bmp`
6. 如果生成了，截图内容是否正确
