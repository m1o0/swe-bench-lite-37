# MANIFEST v1（盲写条件，已冻结）

生成时间：`2026-09-10T21:21:55+0800`

本清单把 v1 的分数与其证据文件绑定：`25/37 = 67.6%` 只有在下列文件哈希不变时才成立。任何依据失败反馈修改补丁的工作都属于 v2（见 `V2_PLAN.md`），不得覆盖本清单记录的文件。

## 运行信息

| 项 | 值 |
|---|---|
| run_id | `tonight` |
| model_name_or_path | `glm-5.3-zcode-campaign` |
| 命令 | `HF_ENDPOINT=https://hf-mirror.com python3 -m swebench.harness.run_evaluation -d SWE-bench/SWE-bench_Lite -s test -p predictions_swebench.jsonl -id tonight --max_workers 4` |
| swebench | 5.0.2 |
| Docker server | 29.8.0 |
| WSL | Ubuntu-22.04 (Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.35) |
| 数据集 | SWE-bench/SWE-bench_Lite / test，parquet sha256 `7a21f37b8bc179c7db5beeb14e88ac538ba283455c776e6b2535bbfb6e3551b4` |

## 产物完整度

| artifact | 覆盖 |
|---|---|
| `patch.diff` | 37/37 |
| `summary.md` | 37/37 |
| `verify.py` | 19/37 |
| `harness report.json` | 37/37 |

## 校验值

| instance_id | patch.diff | summary.md | verify.py | report.json | 镜像 digest |
|---|---|---|---|---|---|
| django__django-10914 | `c6c663d0a033aafc` | `a5d60e12c978d6ba` | **缺失** | `4d36aa9e74a88a5b` | `sha256:f26f0db931c6c1e78` |
| django__django-10924 | `66515cf99c1508c1` | `6871a8ed99acd40c` | `afea75ff7dccd4a8` | `9f8de0075de1768a` | `sha256:d41b289ea27a92ef6` |
| django__django-11001 | `25d5ebcd1c78e8eb` | `67a634fe372ef490` | **缺失** | `49b83db5416c8736` | `sha256:68c61032db48a5eef` |
| django__django-11019 | `d0e61122620494b7` | `90f322bac6f241bc` | `b9744788b17b79f2` | `cacd9c4c00b6010b` | `sha256:507a4ada244710df9` |
| django__django-11039 | `be63da2d5063a560` | `04d2c69839afab6d` | **缺失** | `cd1de15e1d945ec5` | `sha256:895cb9b96a9ba3a72` |
| django__django-11049 | `d4c92e54ed156af7` | `e34bae66b323d62e` | **缺失** | `4534ad31aa34e4d4` | `sha256:c5700017c1dfcca5e` |
| django__django-11099 | `dcd7202d62b786de` | `1acb21c506ea6cc2` | `19ebb7589a841e4c` | `783e252651c6cc7c` | `sha256:cca302934edd881cc` |
| django__django-11133 | `8007c04b626293e1` | `528603e10836384e` | **缺失** | `5a154c5b691830db` | `sha256:914093363dbe12def` |
| django__django-11179 | `b9011c1b8ba40b3e` | `bcbe7d51632e008b` | **缺失** | `260090955e844ae6` | `sha256:23e061f0071647d4c` |
| django__django-11283 | `c05c1fdb69697cd5` | `3aae22735025ced5` | **缺失** | `9f7c490eacf9ca6f` | `sha256:2ca0c1500292dd3c1` |
| django__django-11422 | `6ef55aebd5cb8159` | `ecfb141ecdc9e806` | `cb2c782b0327d90c` | `c6aa33188667745a` | `sha256:d8703d50c49fae627` |
| django__django-11564 | `3f5a740e36fb8a21` | `2a0e48b290648a5f` | `b522690cf1260868` | `35dd155f03f201b5` | `sha256:a565e9f99ade187a4` |
| django__django-11583 | `a9b7efd0075c46f9` | `5f76347a762117ed` | `ff31316deb071540` | `1742b822f1aa8e46` | `sha256:f2ac03fe870177231` |
| django__django-11620 | `8d95c297b27057a9` | `338ff318b840bf83` | **缺失** | `6ea493dd89c8b6d6` | `sha256:6c99f08e757436b33` |
| django__django-11630 | `ca4012ab2122f85f` | `ca36a0ae269b810c` | `001f1011d8fd4614` | `e6abdd91b3384038` | `sha256:86c81bee2d2a1c35e` |
| django__django-11742 | `59c23ab31d5448c3` | `8a08c02da020092a` | `925b9d360ce47daf` | `06754e0d8af0c161` | `sha256:64c26c94843c28857` |
| django__django-11797 | `9cdcd76068e2908f` | `e95c5514843e1116` | **缺失** | `fc1dedc5bca643ce` | `sha256:2d3c56fb0a332d8f3` |
| django__django-11999 | `a2194877702509ab` | `6a4302f9c53ce94b` | **缺失** | `a184f919d25dd01d` | `sha256:3c7e7f035f611b17f` |
| django__django-12125 | `14f76a9b1191174f` | `69a40ed2ec2358c2` | `458de9c3e246cb7f` | `6b81f7254ada2fc4` | `sha256:4345ad65eec0da8a3` |
| django__django-12184 | `674ed411740d281a` | `ef5c92d77868ea13` | `d1b6a98493f2a58f` | `0ba39434768bfa1e` | `sha256:c28686e155d0dd367` |
| django__django-12284 | `1a654d8f20f64829` | `1aa56caf866b772c` | **缺失** | `ecc10c0794577c24` | `sha256:f6566d6750acadc43` |
| django__django-12286 | `1f004134e7ef980c` | `efb419920c651a2a` | `e03a0db1bce04b45` | `3f7580ec828a828d` | `sha256:90c377f8c5ea3844a` |
| django__django-12308 | `f577cbc106247b49` | `15f484af76e5a21d` | `9d16d25919602661` | `53a7f39dfef0a6cc` | `sha256:6250d2a608d52b82c` |
| django__django-12453 | `c92d181d3766cd37` | `979b747dcac47041` | `ecb2a22736ef51de` | `ba38eb1c3953a09b` | `sha256:a4ddc630adffc7e64` |
| django__django-12470 | `8c53871d71226267` | `80ef9416e8f061e9` | **缺失** | `2fde2ed7c3a9c18d` | `sha256:6bcd06ce3f41aba55` |
| django__django-12497 | `f97a720e00a4c1f1` | `0b799d16c9b5ede6` | **缺失** | `2a2db0337d3b4820` | `sha256:8fb1142fc9cece8de` |
| django__django-12589 | `29259a0d1f7293db` | `6501a96b5d96c7c5` | **缺失** | `4538385fb47d686b` | `sha256:91c4b9e6b044f038a` |
| django__django-12700 | `82993b2c58e0e4cc` | `6b89ce868ab85a5b` | `99579e37c18660cd` | `59f5f978cba96f7d` | `sha256:be0fbf89e9add2c0c` |
| django__django-12708 | `d01ceabf416b52c6` | `55f8240ea9eabd2f` | `b925c9196ec11d44` | `a70abcffb9812b5d` | `sha256:3722a130f618602e5` |
| django__django-12856 | `07a6849b9940229b` | `07989712b817dcbd` | `ee0bceecdcf8fd0b` | `2e1ccec5963691c4` | `sha256:d53de59169fc601ca` |
| django__django-12915 | `d1f83bf8d46db760` | `eeba684df52ecdda` | `876397aadf8c51b3` | `84a60e00f6c06582` | `sha256:cb8a11360b096bcd0` |
| django__django-12983 | `6ae14f97c6b3457d` | `955dc06a4152cf90` | `50d576ca5624bfe3` | `49cae97ffc4e5023` | `sha256:f89a493dc687475e9` |
| django__django-13028 | `b371334c6daf8271` | `54f54eadd416cf9b` | `93755e3c183a9f5e` | `3c3fbde0bbf87498` | `sha256:4250631872579b9eb` |
| pylint-dev__pylint-5859 | `41fef95969b7f81b` | `c7758c9f963b72c7` | **缺失** | `8aaf66dd516c586d` | `sha256:12412d9d1d7a06b8f` |
| pylint-dev__pylint-6506 | `b9a490de709b29dc` | `8f261d7d28b313fd` | **缺失** | `ced779e43f5bb18e` | `sha256:f2304d2a6461bc098` |
| pytest-dev__pytest-5103 | `0eb3c976dc44caa9` | `d3fb16ad99bda13b` | **缺失** | `788d10047c1cb4a3` | `sha256:1648c614485c81d9e` |
| pytest-dev__pytest-5221 | `1bddfd690f056759` | `b87c8c678132c165` | **缺失** | `444ad4e5853c9a50` | `sha256:547472f1933751a67` |

> 表格中哈希为前 16 位便于阅读；完整 64 位值见 `MANIFEST_v1.json`。
> **本次生成自检**：`patch_delta_vs_predictions` 不一致 0 条；镜像 digest 解析 37/37；`verify.py` 19/37。
