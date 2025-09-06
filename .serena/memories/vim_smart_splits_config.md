# Smart Splits.nvim 配置

已为 LazyVim 配置了 smart-splits.nvim 插件，用于智能窗口导航和调整大小。

## 插件配置位置
- 文件路径：`~/.config/nvim/lua/plugins/smart-splits.lua`
- 设置了 `lazy = false` 以确保与终端复用器（zellij）的兼容性

## 主要功能
1. **窗口导航**：使用 `Ctrl+h/j/k/l` 在窗口间移动
2. **窗口调整**：使用 `Ctrl+方向键` 调整窗口大小
3. **缓冲区交换**：使用 `Ctrl+Alt+h/j/k/l` 交换缓冲区位置

## 键位映射
### 导航键位
- `<C-h>` - 向左移动
- `<C-j>` - 向下移动
- `<C-k>` - 向上移动
- `<C-l>` - 向右移动

### 调整大小键位
- `<C-Up>` - 向上调整
- `<C-Down>` - 向下调整
- `<C-Left>` - 向左调整
- `<C-Right>` - 向右调整

### 交换缓冲区键位
- `<C-A-h>` - 向左交换缓冲区
- `<C-A-j>` - 向下交换缓冲区
- `<C-A-k>` - 向上交换缓冲区
- `<C-A-l>` - 向右交换缓冲区

## 特殊配置
- 忽略的缓冲区类型：`nofile`, `quickfix`, `prompt`
- 忽略的文件类型：`NvimTree`
- 适用于所有模式：normal, insert, visual（导航和调整大小）
- 交换缓冲区仅适用于 normal 模式

## 终端复用器集成
配置适用于 zellij 终端复用器，可以在 Neovim 窗口和 zellij 面板之间无缝导航。

## 安装状态
- 插件已安装并同步
- Neovim 版本：v0.11.3
- 配置已完成并测试通过