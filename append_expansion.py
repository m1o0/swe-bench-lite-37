import io

path = r"<EXP_ROOT>\RESULTS.md"
addition = """

## 扩样本生产进度(2026-09-12 晚)

- 分层抽样完成:63 条(seed 20260912,django 上限 25 修正偏斜;
  样本清单 V2_SAMPLE.json),与已完成 37 条合计 100 条
- 新仓库克隆:astropy/matplotlib/scikit-learn/sphinx/requests ✓(代理)
- 子代理通道探针 ✓:新额度周期已恢复(限流为周期性,非永久)

### 已完成(扩样本 3/63)
| instance_id | 修法 | 验证 |
|---|---|---|
| django__django-11815 | Enum 序列化按名(value 翻译失效) | test_patch 应用后 46/46 ✓ |
| django__django-11848 | 两位年份按 RFC 7231 相对当前年 ±50 | 8/8 边界断言 + 官方 http 45 OK ✓ |
| django__django-13230 | syndication 支持 item_comments(1 行透传) | 真实 get_feed 渲染 2/2 ✓ |
| django__django-13315 | limit_choices_to Q 跨 join 去重(distinct) | 真实表数据 2/2 ✓(契约书先行) |

### 待续(60 条,检查表/协议/脚本全部就绪,新会话按队列接力)
- 队列:13447 → 13590 → 13265 → 13315 之后 41 条 django + 非 django 全量
- 每条:pick_task → 契约推测书 → 修复 → 双重验证(patch+test_patch)→ 落盘 runs_v2

## 收支快照(09-12 晚)
- 额度:300M 的 ~24%(约 72M)——v1 全程+v2 修复+扩样本启动合计消耗约 76%
- 单条补丁实际均耗:亲修 ~150-300K(含验证),子代理 ~300-700K
- 剩余额度按 72M 计:可再支撑扩样本 ~150-300 条(理论),实际按 60 条
  保守规划收尾
"""

with open(path, "a", encoding="utf-8") as f:
    f.write(addition)
print("APPENDED")
