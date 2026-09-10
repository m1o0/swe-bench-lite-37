import importlib.util, sys
sys.path.insert(0, r"D:\mio\worktrees\django__django-11099")

spec = importlib.util.spec_from_file_location(
    "auth_validators",
    r"D:\mio\worktrees\django__django-11099\django\contrib\auth\validators.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = True
for v in (m.ASCIIUsernameValidator(), m.UnicodeUsernameValidator()):
    try:
        v("abc.1@x")
        print("plain username: PASS (accepted as expected)")
    except Exception:
        print("plain username: FAIL"); ok = False
    try:
        v("abc\n")
        print("trailing newline: FAIL (accepted, bug not fixed)"); ok = False
    except Exception:
        print("trailing newline: PASS (rejected as expected)")
print("ALL_OK" if ok else "NOT_FIXED")
