import io

path = r"<EXP_ROOT>\RESULTS.md"
addition = """

## 提交前门禁基线 + 结构化置信度协议（2026-09-12，第一/三梯队项落地）

**GATE_BASELINE.md**：三级门禁（apply / 编译 / 受影响模块公开测试）对 12 条 v1
失败的拦截能力逐条判定（归属用 classify_gate.py 的 git grep HEAD 逐条存证）：
- 门禁只拦截 **2/12**：12589（回归型）与 6506（异常类型契约不符）
- 其余 10 条补丁通过全部门禁（公开测试在补丁树上全绿），失败只发生在
  test_patch 新增/改写的断言上——其中 11019 与 5221 的**基线版测试在本树通过**，
  改写版才暴露契约差异
- 结论：提交前门禁的边际价值集中在回归防护；M1 契约缺口与 M2 构造形态缺陷
  对不含 test_patch 的门禁不可见

**CONFIDENCE_PROTOCOL.md**：结构化置信度协议（后续生产的强制前置）——
生产前先产出《契约推测书》（逐条可证伪的契约推测 + 依据等级三档 + 不确定点清单），
自报置信度改为规则化推导（high=全仓库证据且逐项验证 / medium=含推测项 /
low=有未实现项），评分后按契约项回填"推测 vs 实测"命中率——校准分析的
最小单元。GATE_BASELINE 的结论（门禁不防契约缺口）是该协议的立论依据。

两项均已同步至 GitHub 仓库（commit 2d0a79f）。
"""

with open(path, "a", encoding="utf-8") as f:
    f.write(addition)
print("APPENDED")
