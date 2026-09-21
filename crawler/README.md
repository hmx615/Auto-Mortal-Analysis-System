# 牌谱爬取模块

通过牌谱屋网页前端抓取历史牌谱。程序打开有界面的 Microsoft Edge，等待站点正常完成 CAP 验证，再持续滚动虚拟列表并从 DOM 提取数据。

`player_records` 直连 API 已停用：该接口现在要求 CAP 令牌，会拒绝无授权的 API 爬取。

## 文件

- `crawl_frontend.py` - 网页滚动爬虫实现
- `crawl_all.py` - 兼容原命令的启动入口，仅调用网页爬虫
- `run_crawl.bat` / `run_crawler.sh` - 一键启动脚本

## 使用

可直接读取根目录 `config.py` 中的 `PLAYER_NAME`、`PLAYER_ID` 和 `MODE`：

```bash
python crawler/crawl_all.py
```

也可通过命令行指定：

```bash
python crawler/crawl_all.py Carax143 --player-id 20018263 --modes 16,12,9,8
```

模式编号：

- `16` - 王座南场
- `12` - 玉之间南场
- `9` - 金之间南场
- `8` - 金之间东场

## 输出

牌谱保存到 `data/<玩家名>/paipu_list.csv`。重复执行会按 UUID 合并已有数据，不会重复写入。

## 注意

- 必须安装 Microsoft Edge 和 Selenium。
- 不要使用无头模式；牌谱屋的 CAP 验证会拒绝无头自动化浏览器。
- 爬取时会显示 Edge 窗口，请保持图形桌面可用。
- `PLAYER_ID` 可从牌谱屋玩家页 URL 中获取，例如 `/player/20018263/12`。
