# django__django-11564 — v2 修复(SCRIPT_NAME 前缀进 settings 取值层)

## 信息条件
使用了 v1 评测反馈 + **读取了该条的 test_patch 断言**(v2"反馈知情修复"条件)。
v1 日志给出 10 个失败参数格的期望值(如 `'path/' != '/somesubpath/path/'`);
test_patch 给出 MediaURLStaticURLPrefixTest 的完整参数矩阵与 file_storage
test_setting_changed 的连带改写。

## v1 遗留缺陷
v1 只在请求上下文处理器(template/context_processors.py)里给渲染出的
MEDIA_URL 加前缀;隐藏测试断言的是 `settings.STATIC_URL`/`settings.MEDIA_URL`
**取值本身**被加前缀,该层完全没动,settings 值保持原样 → 10 格全失败。

## v2 实现(django/conf/__init__.py,唯一改动文件)
- 新增模块级 `_add_script_name(val)`:
  * 绝对路径(`/`开头)与已知 scheme(http/https/ftp/ftps,与 URLValidator
    schemes 一致)→ 原样返回;`htp://` 这类无效 scheme 视为相对值 → 加前缀
    (与隐藏用例 `('/somesubpath/','htp://...')→'/somesubpath/htp://...'` 一致)。
  * 其余:`get_script_prefix()` 归一化(去尾斜杠后补一个 `/`,'/' 保持 '/',
    保证 `('/','path/')→'/path/'` 而非 `'//path/'`)后拼接。
  * 空 script prefix → 原样返回;空白值仅在非默认 prefix 下返回归一化 prefix
    (`('/somesubpath/','')→'/somesubpath/'`),默认 prefix '/' 下保持 ''(P2P
    安全选择,未由隐藏用例钉死)。
- `LazySettings.__getattr__` 对 MEDIA_URL/STATIC_URL 走该函数;**不写入
  self.__dict__ 缓存**——script prefix 是线程局部、按请求变化,缓存会跨线程/跨
  请求串值;其余设置行为不变。
- v1 对 context_processors.py 的改动已 `git checkout --` 清理(settings 层
  生效后,上下文处理器自然拿到带前缀的值)。

## 验证(WSL 实跑,见 verify_output.txt)
- 临时应用 test_patch:settings_tests + file_storage **182/182 OK**
  (含全部隐藏参数格与改写后的 test_setting_changed,一次通过,零回归)。

## 已知不确定性
- 上游实现对"合法 URL"的 scheme 白名单 idiom 未考据(未读上游 patch);本实现
  用 ('http','https','ftp','ftps'),被全部隐藏参数格覆盖,无用例区分更宽的
  白名单(如 uses_netloc)。
- 空白值 + 默认 prefix '/' 的行为(返回 '' 而非 '/')未被任何测试钉死;选了
  P2P 安全侧。
