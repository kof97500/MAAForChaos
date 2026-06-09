# MaaLearn

`MaaLearn` 用于孵化 `卡厄思梦境 PC 自动化项目`。

当前阶段目标：

- 建立项目骨架
- 明确开发流程与技术方案
- 搭建运行入口
- 接入日志与实时进度展示
- 预留游戏窗口连接能力

## 当前结构

- [docs/README.md](/Users/michael/Documents/MaaLearn/docs/README.md)：文档索引
- `src/czn_automation/`：自动化程序源码
- `tests/`：测试代码
- `config/`：示例配置
- `debug/`：运行日志与调试截图

## 本地运行

当前项目骨架采用 Python。

```bash
python3 -m czn_automation
```

如果使用源码目录方式运行：

```bash
PYTHONPATH=src python3 -m czn_automation
```

## 事件检测工具

当前仓库已经提供一个可单独运行的事件页检测入口，便于针对单个事件页面做验证。

直接检测当前游戏窗口：

```bash
PYTHONPATH=src python3 -m czn_automation.event_probe
```

对指定截图做离线检测：

```bash
PYTHONPATH=src python3 -m czn_automation.event_probe --image /path/to/event.png
```

检测结果会输出到：

- `debug/events/event_probe_result.json`
- `debug/events/options/option_*.png`

## Windows 调试

Windows 本地运行与调试说明见：

- [docs/specs/windows-dev-setup.md](/Users/michael/Documents/MaaLearn/docs/specs/windows-dev-setup.md)

如果使用 VS Code，可直接使用仓库内的调试配置。
