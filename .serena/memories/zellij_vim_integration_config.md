# Zellij + Neovim 智能导航配置

已成功配置 Zellij 终端复用器与 Neovim (LazyVim) 的无缝集成，使用 vim-zellij-navigator 和 smart-splits.nvim 插件。

## 配置文件位置

### Zellij 配置
- 文件路径：`~/.config/zellij/config.kdl`
- 插件位置：`~/.config/zellij/plugins/vim-zellij-navigator.wasm`

### Neovim 配置
- 文件路径：`~/.config/nvim/lua/plugins/smart-splits.lua`

## 核心功能特性

### 1. 智能导航
- **统一键位**：在 Neovim 窗口和 Zellij 面板间使用相同的导航键
- **自动检测**：vim-zellij-navigator 自动检测当前是否在 Neovim 中
- **无缝切换**：当到达 Neovim 窗口边缘时，自动移动到 Zellij 面板

### 2. 导航键位（Ctrl + hjkl）
- `<C-h>` - 向左移动（Neovim 窗口 ← Zellij 面板）
- `<C-j>` - 向下移动（仅在 Neovim 窗口内）
- `<C-k>` - 向上移动（仅在 Neovim 窗口内）
- `<C-l>` - 向右移动（Neovim 窗口 → Zellij 面板）或切换标签页

### 3. 调整大小键位（Alt + hjkl）
- `<A-h>` - 向左调整大小
- `<A-j>` - 向下调整大小
- `<A-k>` - 向上调整大小
- `<A-l>` - 向右调整大小

### 4. 替代调整大小键位（Ctrl + 方向键）
- `<C-Up>` - 向上调整
- `<C-Down>` - 向下调整
- `<C-Left>` - 向左调整
- `<C-Right>` - 向右调整

### 5. 缓冲区交换（Ctrl + Alt + hjkl）
- `<C-A-h>` - 向左交换缓冲区
- `<C-A-j>` - 向下交换缓冲区
- `<C-A-k>` - 向上交换缓冲区
- `<C-A-l>` - 向右交换缓冲区

## 技术实现细节

### Zellij 端配置
- 使用 `vim-zellij-navigator.wasm` 插件（版本 0.3.0）
- 配置了 `move_focus_or_tab` 和 `move_focus` 命令
- 支持水平/垂直导航和标签页切换
- 设置了 `resize_mod = "alt"` 用于调整大小

### Neovim 端配置
- 启用了 `multiplexer_integration = "zellij"`
- 设置 `at_edge = "wrap"` 实现边缘循环
- 配置了 `disable_multiplexer_nav_when_zoomed = true` 避免冲突
- 忽略 NvimTree 等特殊缓冲区类型

## 版本信息
- Zellij 版本：0.42.2
- Neovim 版本：v0.11.3
- vim-zellij-navigator 版本：0.3.0
- smart-splits.nvim：最新版本

## 使用场景
1. **编码时**：在 Neovim 的多个窗口间快速导航
2. **调试时**：在 Neovim 和终端（Zellij 面板）间切换
3. **多任务**：在多个 Zellij 标签页间移动
4. **窗口管理**：动态调整 Neovim 窗口和 Zellij 面板大小

## 配置状态
- ✅ 插件已安装并同步
- ✅ 键位映射已配置
- ✅ 集成功能已测试
- ✅ 配置已优化并文档化