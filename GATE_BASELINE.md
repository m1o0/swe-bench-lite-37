# Gate Baseline:提交前门禁对 12 条失败的拦截能力(v1 复盘)

## 门禁定义(三级)

| 门禁 | 内容 | 成本 |
|---|---|---|
| A. 应用检查 | `git apply --check` 补丁可干净应用 | 秒级 |
| B. 编译/导入 | 改动文件 py_compile + 模块导入 | 秒级 |
| C. 受影响模块公开测试 | 改动模块的**既有**测试(不含 test_patch 新增/改写) | 分钟级 |

## 数据来源
- 门禁 A:官方评测 log(37/37 补丁全部应用成功,0 条失败)
- 门禁 B:全部补丁均通过编译(评测与本地验证均无 ImportError/SyntaxError)
- 门禁 C:各工作树的公开测试实跑记录(21 树)与评测 log 中**基线测试**的通过状态
- 失败测试归属:`classify_gate.py` 用 `git grep 'def <test>(' HEAD -- <file>)`
  逐条判定"基线已有"还是"test_patch 新增/改写"(可复验脚本已落盘)

## 逐条判定(12 条 v1 失败)

| instance_id | 失败测试 | 归属 | 门禁 A | 门禁 B | 门禁 C | 门禁能否拦截 |
|---|---|---|---|---|---|---|
| django__django-11001 | test_order_by_multiline_sql, test_order_of_operations | 隐藏(新增) | ✓ | ✓ | ✓(expressions 126 OK) | ✗ |
| django__django-11019 | test_combine_media, test_construction, test_form_media | 基线已有但被 test_patch **改写**(改写版失败;基线版在本树实跑通过) | ✓ | ✓ | ✓(forms_tests 639 OK) | ✗ |
| django__django-11283 | test_migrate_with_existing_target_permission | 隐藏(新增) | ✓ | ✓ | ✓(其余 8 项 OK) | ✗ |
| django__django-11564 | test_add_script_name_prefix, test_not_prefixed | 隐藏(新增) | ✓ | ✓ | ✓(settings_tests 52 OK) | ✗ |
| django__django-11630 | test_collision_*_database_routers_installed ×2 | 隐藏(新增) | ✓ | ✓ | ✓(check_framework 142 OK) | ✗ |
| django__django-11797 | test_exact_query_rhs_with_selected_columns | 隐藏(新增) | ✓ | ✓ | ✓(其余 lookup 项 OK) | ✗ |
| django__django-12308 | test_json_display_for_field(隐藏)+ test_label_for_field(基线已有,改写) | 混合 | ✓ | ✓ | ✓(admin_utils 34 OK) | ✗ |
| django__django-12589 | test_group_by_exists_annotation, test_group_by_subquery_annotation | 基线已有(**回归**) | ✓ | ✓ | ✗(aggregation 2 项失败) | **✓ 拦截** |
| django__django-12856 | test_unique_constraint_pointing_to_* ×3 | 隐藏(新增) | ✓ | ✓ | ✓(test_models 79 OK) | ✗ |
| pylint-dev__pylint-6506 | test_unknown_option_name, test_unknown_short_option_name | 基线已有(**异常类型契约不符**) | ✓ | ✓ | ✗(config 2 项失败) | **✓ 拦截** |
| pytest-dev__pytest-5103 | test_unroll_expression 等 ×3 | 隐藏(新增) | ✓ | ✓ | ✓(其余项 OK) | ✗ |
| pytest-dev__pytest-5221 | test_show_fixtures_verbose | 基线已有但被 test_patch **改写**(改写版失败;基线版预期在本树通过) | ✓ | ✓ | ✓ | ✗ |

## 结论

1. **三级门禁在 12 条失败中只拦截 2 条**:12589(回归型,公开测试直接变红)与
   6506(异常类型契约不符——基线测试要求向上抛 `_UnrecognizedOptionError`,
   补丁却 `sys.exit(32)`,公开测试立刻变红)。
2. **其余 10 条通过全部门禁**:补丁应用干净、编译通过、受影响模块的既有测试全绿,
   失败只发生在 test_patch 新增/改写的断言上。其中 11019 与 5221 尤其典型——
   基线版本的同一测试在本树通过,改写版本才暴露契约差异。
3. **对 M2(3 条运行时缺陷)的修正认识**:门禁 C 无法拦截它们——三个缺陷都只在
   test_patch 的构造形态下暴露(11001 的 distinct 变体、12308 的元组键字典、
   12856 的三字段场景)。**"补丁可运行"与"满足隐藏契约"是两个不相关的合格线。**
4. **研究含义**:在这类 benchmark 上,提交前门禁的边际价值集中在**回归防护**
   (12589 型);对契约缺口(M1)与构造形态缺陷(M2)无效。提升通过率的杠杆
   在生产前的**契约推测质量**(见 CONFIDENCE_PROTOCOL.md),而非更重的提交前门禁。
5. **例外说明**:6506 的拦截本质是"异常类型契约"——基线测试编码了"必须抛
   `_UnrecognizedOptionError`",而补丁改成了 SystemExit。它属于 M1(契约不符)
   的一个恰好被公开测试覆盖的子 case;若 test_patch 未改写这两个测试,
   本条同样不会被门禁拦截。

## 复验方式
- 每行判定的证据:`classify_gate.py`(git grep HEAD 逐条)输出可重放;
- 公开测试实跑记录:见 RESULTS.md"官方测试套件验证"小节(21 树,约 3800 断言);
- 评测 log:logs/run_evaluation/tonight/<instance_id>/test_output.txt。
