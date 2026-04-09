# UNO 人机对战

这是一个用 Python `tkinter` 写的本地 UNO 小游戏，支持图形界面和多个 AI 对手。对局规则按经典 UNO 的核心玩法实现，支持多人方向变化，也保留了双人局下 `Reverse` 视作 `Skip` 的规则。

## 环境依赖

- Python `3.13`
- `tk`（`tkinter` 图形界面运行库）
- 其他部分仅使用 Python 标准库，不需要额外安装 `pip` 包

项目已经提供了 `environment.yml`，推荐直接用 conda 创建环境：

```bash
conda env create -f environment.yml
conda activate uno
```

如果你已经有同名环境，也可以手动确认里面至少包含 `python` 和 `tk`。

## 运行方式

如果你还没有把项目拉到本地，可以先执行：

```bash
git clone https://github.com/ziwenze/nanoUno.git
cd nanoUno
```

创建并激活环境后，在仓库目录里运行：

```bash
python app.py
```

## 发布 Release

仓库已经配置了自动打包发布流程。你只需要给版本打一个 tag 并推送，GitHub Actions 就会自动构建发布文件，并创建 GitHub Release。

推荐流程：

```bash
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0
```

自动发布内容：

- `nanoUno-macos.zip`
- `nanoUno-windows.zip`

其中：

- macOS 会打包成 `.app` 后再压缩
- Windows 会打包成单文件 `.exe` 后再压缩
- 每次发布前都会先跑 `tests/` 里的单元测试

你也可以在 GitHub 的 `Actions` 页面手动触发 `Build Release` 工作流，先检查打包是否正常。

## Release 注意事项

- 现在这套流程已经能生成“下载后可运行”的发布包
- 但 macOS 版本目前还是未签名应用，第一次打开时系统可能会提示安全限制
- 如果你想做到更顺滑的“下载后直接双击打开”，后续还需要加 Apple Developer 签名和 notarization
- Windows 如果想减少安全警告，也可以后续再接代码签名证书

## 已实现内容

- 图形界面
- 你 vs 多个 AI 的单机对战
- `增加 AI` / `减少 AI` 按钮，支持 1 到 5 名 AI
- 经典 108 张牌组
- `Skip`、`Reverse`、`+2`、`Wild`、`Wild +4`
- 多人规则下 `Reverse` 会反转方向
- 双人规则下 `Reverse` 按 `Skip` 处理
- `Wild +4` 只能在手里没有当前颜色牌时打出
- 回合日志、当前颜色、牌堆数量、重新开局

## 操作说明

- 轮到你时，可点击高亮的可出手牌。
- 如果没有可出的牌，点击“抽牌”。
- 若抽到的牌可打，你可以直接打出，或者点击“结束回合”保留它。
- 你可以通过顶部按钮增加或减少 AI 数量，人数变化后会自动重开一局。
- 任意一方先出完手牌就获胜。

## 说明

- 这个版本做的是单局对战，胜利后会显示本轮得分。
- 为了让单机体验更顺滑，`UNO` 宣告采用自动处理，没有做手动喊牌和挑战按钮。
