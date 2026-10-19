import json

for run in ("tonight", "tonight-v2", "tonight-v2c", "tonight-v2d"):
    try:
        name = "glm-5.3-zcode-campaign" + ("." + run if run != "tonight" else "." + run)
        p = rf"<EXP_ROOT>\glm-5.3-zcode-campaign.{run}.json"
        r = json.load(open(p, encoding="utf-8"))
        print(run, "| resolved:", len(r["resolved_ids"]), "| unresolved:",
              len(r["unresolved_ids"]), "| submitted:",
              r.get("submitted_ids") and len(r["submitted_ids"]))
        if run == "tonight-v2":
            for i in sorted(r["resolved_ids"]):
                print("   PASS:", i)
            for i in sorted(r["unresolved_ids"]):
                print("   FAIL:", i)
    except FileNotFoundError:
        print(run, "-> file missing")
