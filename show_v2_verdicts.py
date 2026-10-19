import json

for run in ("tonight-v2c", "tonight-v2d"):
    p = rf"<EXP_ROOT>\glm-5.3-zcode-campaign-v2.{run}.json"
    r = json.load(open(p, encoding="utf-8"))
    print("===", run, "===")
    print("resolved:", len(r["resolved_ids"]), "| unresolved:", len(r["unresolved_ids"]),
          "| error:", len(r["error_ids"]))
    for i in sorted(r["resolved_ids"]):
        print("  PASS:", i)
    for i in sorted(r["unresolved_ids"]):
        print("  FAIL:", i)
