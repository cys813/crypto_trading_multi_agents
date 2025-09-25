# Zellij-Nav.nvim 配置

已成功将 smart-splits.nvim 替换为 zellij-nav.nvim 插件，这是一个专门为 Zellij 设计的轻量级导航插件。

## 插件配置

### Neovim 配置 (`~/.config/nvim/lua/plugins/smart-splits.lua`)
```lua
return {
  "swaits/zellij-nav.nvim",
  lazy = false,
  keys = {
    { "<C-h>", "<cmd>ZellijNavigateLeftTab<cr>", { silent = true, desc = "navigate left or tab", mode = { "n", "i", "v" } } },
    { "<C-j>", "<cmd>ZellijNavigateDown<cr>",     { silent = true, desc = "navigate down",     mode = { "n", "i", "v" } } },
    { "<C-k>", "<cmd>ZellijNavigateUp<cr>",       { silent = true, desc = "navigate up",       mode = { "n", "i", "v" } } },
    { "<C-l>", "<cmd>ZellijNavigateRightTab<cr>", { silent = true, desc = "navigate right or tab", mode = { "n", "i", "v" } } },
  },
  config = function()
    require("zellij-nav").setup()
    
    -- 确保退出 Neovim 时 Zellij 返回正常模式
    vim.api.nvim_create_autocmd("VimLeave", {
      pattern = "*",
      command = "silent !zellij action switch-mode normal"
    })
    
    -- 调整大小键位
    local modes = { "n", "i", "v" }
    vim.keymap.set(modes, "<A-h>", ":vertical resize -3<CR>", { silent = true, desc = "Resize left" })
    vim.keymap.set(modes, "<A-j>", ":resize +3<CR>", { silent = true, desc = "Resize down" })
    vim.keymap.set(modes, "<A-k>", ":resize -3<CR>", { silent = true, desc = "Resize up" })
    vim.keymap.set(modes, "<A-l>", ":vertical resize +3<CR>", { silent = true, desc = "Resize right" })
  end,
}
```

### Zellij 配置 (`~/.config/zellij/config.kdl`)
```kdl
shared_except "locked" {
    // Zellij 导航键位 - 与 zellij-nav.nvim 配合使用
    // 这些键位在不在 Neovim 中时会直接由 Zellij 处理
    
    bind "Ctrl h" { MoveFocus "Left"; }
    bind "Ctrl j" { MoveFocus "Down"; }
    bind "Ctrl k" { MoveFocus "Up"; }
    bind "Ctrl l" { MoveFocus "Right"; }
    
    // 面板调整大小
    bind "Alt h" { Resize "Increase Left"; }
    bind "Alt j" { Resize "Increase Down"; }
    bind "Alt k" { Resize "Increase Up"; }
    bind "Alt l" { Resize "Increase Right"; }
}
```

## 主要功能特性

### 1. 智能导航
- **统一键位**：`Ctrl+h/j/k/l` 在 Neovim 窗口和 Zellij 面板间无缝切换
- **自动检测**：插件自动识别当前环境，在 Neovim 内部移动窗口，到达边缘时切换到 Zellij
- **标签页支持**：`Ctrl+h` 和 `Ctrl+l` 支持标签页切换（LeftTab/RightTab）

### 2. 键位映射
#### 导航键位（支持 normal, insert, visual 模式）
- `<C-h>` - 向左移动或切换到左标签页
- `<C-j>` - 向下移动
- `<C-k>` - 向上移动  
- `<C-l>` - 向右移动或切换到右标签页

#### 调整大小键位（支持 normal, insert, visual 模式）
- `<A-h>` - 向左调整窗口大小
- `<A-j>` - 向下调整窗口大小
- `<A-k>` - 向上调整窗口大小
- `<A-l>` - 向右调整窗口大小

### 3. Zellij 集成
- **自动解锁**：退出 Neovim 时自动返回 Zellij 正常模式
- **简化配置**：Zellij 端使用原生命令，无需额外插件
- **无缝切换**：在 Neovim 窗口边缘自动切换到 Zellij 面板

## 技术优势

### 相比 smart-splits.nvim
- **专为 Zellij 设计**：更简洁，专注于 Zellij 集成
- **无额外依赖**：不需要复杂的终端复用器配置
- **轻量级**：代码更少，启动更快
- **原生支持**：直接使用 Zellij 原生命令

### 工作原理
1. **Neovim 内部**：使用 `ZellijNavigate*` 命令移动窗口
2. **到达边缘**：自动检测到窗口边缘，执行 Zellij 命令
3. **Zellij 接管**：使用 `MoveFocus` 命令在面板间导航
4. **自动解锁**：退出 Neovim 时恢复 Zellij 正常模式

## 配置状态
- ✅ 已删除 smart-splits.nvim 插件
- ✅ 已安装 zellij-nav.nvim 插件
- ✅ 已配置 Zellij 原生导航键位
- ✅ 已测试插件功能
- ✅ 已优化配置并文档化

## 使用建议
1. **重启 Neovim**：确保新插件正确加载
2. **重启 Zellij**：应用新的键位配置
3. **测试导航**：在 Neovim 窗口和 Zellij 面板间测试 `Ctrl+h/j/k/l`
4. **享受体验**：无缝的终端复用器导航体验