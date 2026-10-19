import json

for run in ("tonight-v2", "tonight-v2c", "tonight-v2d"):
    p = rf"<EXP_ROOT>\glm-5.3-zcode-campaign-v2.{run}.json"
    r = json.load(open(p, encoding="utf-8"))
    print("===", run, "===")
    print("resolved:", len(r["resolved_ids"]), "| unresolved:", len(r["unresolved_ids"]))
    for i in sorted(r["resolved_ids"]):
        if i in ("django__django-11001", "django__django-12308", "django__django-12589",
                 "django__django-12856", "pytest-dev__pytest-5221"):
            print("   PASS:", i)
    for i in sorted(r["unresolved_ids"]):
        print("   FAIL:", i)
