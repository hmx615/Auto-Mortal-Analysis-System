# 爬虫部分

从API获取所有牌谱数据

## 文件
- `crawl_all.py` - API爬虫（获取所有历史数据）
- `run_crawl.bat` - 运行爬虫

## 使用
双击 `run_crawl.bat` 即可

## 输出
`../data/paipu_list.csv` - 完整牌谱列表

## 说明
- 从 amae-koromo API 获取所有可用的牌谱数据
- 无数量限制，包含所有历史对局
- 包含完整信息：得分、排名、段位分

## 配置参数
可在 `crawl_all.py` 中修改：
```python
PLAYER_ID = 11351776          # 牌谱屋账号ID（用于API查询）
PLAYER_NAME = "Traaaaa"       # 玩家昵称
REAL_MAJSOUL_ID = "33734565"  # 雀魂友人ID（⭐用于Mortal分析）
MODE = 16                     # 王座之间
MODE = 12                     # 玉之间
MODE = 9                      # 金之间
MODE = 16.12                  # 王座+玉（混合模式）
```

### ⚠️ 重要说明
- **PLAYER_ID**: 从牌谱屋URL获取（如 `amae-koromo.sapk.ch/player/11351776`）
- **REAL_MAJSOUL_ID**: 从雀魂牌谱链接获取（如 `paipu=xxx_a33734565`）
- **用于Mortal分析的是 REAL_MAJSOUL_ID**，不是PLAYER_ID！

### 🆔 如何获取ID？
详见：[如何获取ID.md](./如何获取ID.md)
