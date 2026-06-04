# 🆔 如何获取正确的玩家ID

爬虫需要配置两个ID，它们分别用于不同的用途。

## 📊 两个ID的区别

### 1. PLAYER_ID（牌谱屋账号ID）
- **示例**: `11351776`
- **用途**: 用于从牌谱屋API查询对局记录
- **获取方法**: 访问牌谱屋网站，从URL中获取

### 2. REAL_MAJSOUL_ID（雀魂友人ID）⭐
- **示例**: `"33734565"`
- **用途**: 用于构建雀魂官方牌谱链接，**这个ID才能用于Mortal分析**
- **获取方法**: 从雀魂牌谱链接中提取

---

## 🎯 重要：用于Mortal分析的是哪个ID？

**答案**: **REAL_MAJSOUL_ID** (雀魂友人ID)

Mortal AI分析工具需要访问雀魂官方牌谱链接，格式为：
```
https://game.maj-soul.com/1/?paipu={UUID}_a{REAL_MAJSOUL_ID}
                                              ↑
                                         这个ID才是关键！
```

---

## 📝 获取步骤

### 方法1：从雀魂牌谱链接获取（最准确）

#### 步骤：
1. **打开雀魂游戏客户端**（PC版或网页版）
2. **点击主界面的"牌谱"按钮**
3. **选择任意一场你的对局**
4. **点击"复制链接"或"分享牌谱"**

你会得到类似这样的链接：
```
https://game.maj-soul.com/1/?paipu=251213-d838b689-aae4-4cd5-87ab-0ee25405ec3c_a3373455
```

**提取ID**：
- 找到 `_a` 后面的数字
- 在这个例子中，ID是 `3373455`
- 这就是你的 **REAL_MAJSOUL_ID**

#### 验证：
访问这个链接，如果能正常打开牌谱回放，说明ID正确。

---

### 方法2：从牌谱屋网页获取

#### 步骤：

1. **打开牌谱屋网站**: https://amae-koromo.sapk.ch

2. **搜索你的游戏昵称**（例如"Traaaaa"）

3. **进入你的个人主页**，URL类似：
   ```
   https://amae-koromo.sapk.ch/player/11351776/16
                                      ↑
                                  这是PLAYER_ID
   ```

4. **点击任意一场对局**，查看详情页面

5. **右键点击"雀魂牌谱"链接** → 选择"复制链接地址"

6. **从链接中提取ID**：
   ```
   https://game.maj-soul.com/1/?paipu=xxx_a33734565
                                        ↑
                                   REAL_MAJSOUL_ID
   ```

---

### 方法3：从浏览器开发者工具获取（高级）

如果上述方法都不行，可以使用浏览器开发者工具：

1. **打开牌谱屋任意对局页面**
2. **按F12打开开发者工具**
3. **切换到"网络"(Network)标签**
4. **刷新页面**
5. **筛选"game.maj-soul.com"域名的请求**
6. **查看请求URL中的 `_a` 后缀**

---

## ⚙️ 配置到爬虫中

获取到两个ID后，编辑 `crawl_all.py` 文件：

```python
# 配置
PLAYER_ID = 11351776          # 牌谱屋账号ID（从URL获取）
PLAYER_NAME = "Traaaaa"       # 你的游戏昵称
REAL_MAJSOUL_ID = "33734565"  # 雀魂友人ID（从牌谱链接获取）⭐
```

---

## ❓ 常见问题

### Q: 两个ID可以不一样吗？
**A**: 是的！牌谱屋的PLAYER_ID和雀魂的REAL_MAJSOUL_ID是两个不同系统的ID，通常不相同。

### Q: 如果ID配置错误会怎样？
**A**:
- PLAYER_ID错误 → 爬虫无法从牌谱屋API获取数据
- REAL_MAJSOUL_ID错误 → 生成的牌谱链接无法打开，Mortal分析会失败

### Q: 如何验证ID配置正确？
**A**: 运行爬虫后，检查生成的 `paipu_list.csv` 文件：
```csv
uuid,paipu_url,start_time,score,rank,room
251213-xxx,https://game.maj-soul.com/1/?paipu=251213-xxx_a33734565,...
```
复制 `paipu_url` 在浏览器中打开，如果能正常显示牌谱，说明配置正确。

### Q: 可以用别人的ID吗？
**A**: 可以！只要你知道别人的两个ID，就可以爬取并分析他们的牌谱。
---

## 🔗 相关链接

- 牌谱屋网站: https://amae-koromo.sapk.ch
- 雀魂官网: https://game.maj-soul.com
- Mortal AI分析工具: https://mjai.ekyu.moe

---

## ✅ 快速检查清单

配置完成后，确认以下内容：

- [ ] PLAYER_ID 是纯数字（如 11351776）
- [ ] REAL_MAJSOUL_ID 是字符串，用引号包裹（如 "33734565"）
- [ ] 复制一条生成的 paipu_url 能在浏览器中正常打开
- [ ] 爬虫能成功获取到对局数据

如果全部打钩，说明配置正确！可以开始运行分析了。
