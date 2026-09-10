"""Verify the Media merge fix (django issue: spurious MediaOrderConflictWarning
when merging 3 or more media objects).

Standalone script: imports django.forms from the worktree at
D:\\mio\\worktrees\\django__django-11019 (first on sys.path) without
installing anything; pytz (unused by the media code) is stubbed.

Checks:
1. The issue scenario (3+ media objects) in both accumulation orders.
2. Every 2-list Media.merge case pinned by tests/forms_tests/tests/test_media.py
   and the warning message pinned by test_merge_warning.
3. The existing three-way tests and other pinned behaviors (combine/inherit/
   dedup/docs example/rendering).
4. Differential fuzz of the new merge against a verbatim copy of the OLD
   (pre-fix) algorithm: for acyclic 2-list merges the output must be
   identical; for cyclic merges both must warn.
5. Multi-list property fuzz: result is a duplicate-free permutation that
   respects each input list's relative order unless a warning was raised.
"""
import datetime
import itertools
import random
import sys
import types
import warnings

sys.path.insert(0, r"D:\mio\worktrees\django__django-11019")

# This old django version imports pytz at module load time; stub it so the
# media module can be imported standalone (pytz is irrelevant to Media).
pytz_stub = types.ModuleType("pytz")
pytz_stub.utc = datetime.timezone.utc
pytz_stub.timezone = lambda name: datetime.timezone.utc
pytz_stub.FixedOffset = lambda minutes: datetime.timezone(datetime.timedelta(minutes=minutes))
pytz_stub.UnknownTimeZoneError = type("UnknownTimeZoneError", (KeyError,), {})
pytz_stub.__version__ = "stub"
sys.modules["pytz"] = pytz_stub

from django.conf import settings  # noqa: E402

settings.configure(STATIC_URL="http://media.example.com/static/", USE_TZ=True)

import django  # noqa: E402

django.setup()

from django.forms import Media, TextInput  # noqa: E402

failures = []
checks = 0


def check(label, actual, expected):
    global checks
    checks += 1
    if actual != expected:
        failures.append(label)
        print("FAIL %s\n  expected: %r\n  actual:   %r" % (label, expected, actual))
    else:
        print("ok   %s" % label)


def run_with_warnings(func):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = func()
    return result, [w for w in caught if issubclass(w.category, Warning)]


def check_no_warning(label, func):
    global checks
    checks += 1
    result, caught = run_with_warnings(func)
    if caught:
        failures.append(label)
        print("FAIL %s (unexpected warning(s): %r)" % (label, [str(w.message) for w in caught]))
    else:
        print("ok   %s" % label)
    return result


def check_warning(label, func, expected_msg, expected_result):
    global checks
    checks += 1
    result, caught = run_with_warnings(func)
    msgs = [str(w.message) for w in caught]
    if result != expected_result:
        failures.append(label)
        print("FAIL %s (result)\n  expected: %r\n  actual:   %r" % (label, expected_result, result))
    elif msgs != [expected_msg]:
        failures.append(label)
        print("FAIL %s (warnings)\n  expected: %r\n  actual:   %r" % (label, [expected_msg], msgs))
    else:
        print("ok   %s" % label)


print("== 1. Issue scenario: ColorPicker + SimpleTextWidget + FancyTextWidget ==")

color_picker = Media(js=["color-picker.js"])
simple_text = Media(js=["text-editor.js"])
fancy_text = Media(js=["text-editor.js", "text-editor-extras.js", "color-picker.js"])


def issue_media():
    return (color_picker + simple_text + fancy_text)._js


# text-editor.js < text-editor-extras.js < color-picker.js is the only order
# compatible with FancyTextWidget's declared dependencies.
merged_js = check_no_warning("issue: no MediaOrderConflictWarning", issue_media)
check("issue: resolved order", merged_js, ["text-editor.js", "text-editor-extras.js", "color-picker.js"])

# The reversed accumulation order must resolve without a warning as well.
merged_rev = check_no_warning("issue (reversed accumulation): no warning", lambda: (fancy_text + simple_text + color_picker)._js)
check("issue (reversed accumulation): order", merged_rev, ["text-editor.js", "text-editor-extras.js", "color-picker.js"])

print()
print("== 2. Two-list Media.merge cases pinned by test_merge ==")

merge_cases = (
    (([1, 2], [3, 4]), [1, 2, 3, 4]),
    (([1, 2], [2, 3]), [1, 2, 3]),
    (([2, 3], [1, 2]), [1, 2, 3]),
    (([1, 3], [2, 3]), [1, 2, 3]),
    (([1, 2], [1, 3]), [1, 2, 3]),
    (([1, 2], [3, 2]), [1, 3, 2]),
)
for (list1, list2), expected in merge_cases:
    check("merge(%r, %r)" % (list1, list2), Media.merge(list1, list2), expected)

print()
print("== 3. test_merge_warning semantics ==")

check_warning(
    "merge([1, 2], [2, 1]) warns and returns [1, 2]",
    lambda: Media.merge([1, 2], [2, 1]),
    "Detected duplicate Media files in an opposite order:\n1\n2",
    [1, 2],
)

print()
print("== 4. Existing three-way tests ==")

# test_merge_js_three_way
widget1 = Media(js=["custom_widget.js"])
widget2 = Media(js=["jquery.js", "uses_jquery.js"])
form_media = widget1 + widget2
check("three-way: form_media._js", list(form_media._js), ["custom_widget.js", "jquery.js", "uses_jquery.js"])
inline_media = Media(js=["jquery.js", "also_jquery.js"]) + Media(js=["custom_widget.js"])
merged, w = run_with_warnings(lambda: (form_media + inline_media)._js)
check("three-way: merged._js", merged, ["custom_widget.js", "jquery.js", "uses_jquery.js", "also_jquery.js"])
check("three-way: no warning", w, [])

# test_merge_css_three_way
widget1 = Media(css={"screen": ["a.css"]})
widget2 = Media(css={"screen": ["b.css"]})
widget3 = Media(css={"all": ["c.css"]})
form1 = widget1 + widget2
form2 = widget2 + widget1
check("css three-way: form1._css", form1._css, {"screen": ["a.css", "b.css"]})
check("css three-way: form2._css", form2._css, {"screen": ["b.css", "a.css"]})
merged, w = run_with_warnings(lambda: (widget3 + form1 + form2)._css)
check("css three-way: merged._css", merged, {"screen": ["a.css", "b.css"], "all": ["c.css"]})
check("css three-way: no warning", w, [])

print()
print("== 5. Other pinned behaviors (construction/combine/inheritance) ==")

# test_construction: a directly constructed Media keeps its original objects
# (repr shows tuples, not lists).
m = Media(
    css={"all": ("path/to/css1", "/path/to/css2")},
    js=("/path/to/js1", "http://media.other.com/path/to/js2", "https://secure.other.com/path/to/js3"),
)
check(
    "repr of direct Media keeps tuples",
    repr(m),
    "Media(css={'all': ('path/to/css1', '/path/to/css2')}, "
    "js=('/path/to/js1', 'http://media.other.com/path/to/js2', 'https://secure.other.com/path/to/js3'))",
)
check(
    "str of direct Media",
    str(m),
    '<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet">\n'
    '<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet">\n'
    '<script type="text/javascript" src="/path/to/js1"></script>\n'
    '<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>\n'
    '<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>',
)

# test_combine_media
m2 = Media(css={"all": ("/path/to/css2", "/path/to/css3")}, js=("/path/to/js1", "/path/to/js4"))
m3 = Media(css={"all": ("path/to/css1", "/path/to/css3")}, js=("/path/to/js1", "/path/to/js4"))
combined, w = run_with_warnings(lambda: (m + m2 + m3)._js)
check(
    "combine: js",
    combined,
    ["/path/to/js1", "http://media.other.com/path/to/js2", "https://secure.other.com/path/to/js3", "/path/to/js4"],
)
check("combine: no warning", w, [])
combined_css, w = run_with_warnings(lambda: (m + m2 + m3)._css)
check("combine: css['all']", combined_css["all"], ["path/to/css1", "/path/to/css2", "/path/to/css3"])
check("combine: css keys", sorted(combined_css), ["all"])
check("combine: no css warning", w, [])

# #12879: duplicates inside a Media definition are included once once the
# definition is merged (the widget/form path always merges with the empty
# base media). A *raw* single-definition Media keeps its original list object
# (pre-fix behavior, pinned by test_construction's repr check).
m4 = Media(css={"all": ("/path/to/css1", "/path/to/css1")}, js=("/path/to/js1", "/path/to/js1"))
check("dup through merge: js", list((Media() + m4)._js), ["/path/to/js1"])
check("dup through merge: css", (Media() + m4)._css, {"all": ["/path/to/css1"]})
check("dup in raw single-definition Media (passthrough)", m4._js, ("/path/to/js1", "/path/to/js1"))

# test_media_inheritance: widget media extends parent media.
base = Media(css={"all": ("path/to/css1", "/path/to/css2")}, js=("/path/to/js1", "js2", "js3"))
child_def = Media(css={"all": ("/path/to/css3", "path/to/css1")}, js=("/path/to/js1", "/path/to/js4"))
extended, w = run_with_warnings(lambda: (base + child_def)._css)
check("inheritance: css", extended["all"], ["/path/to/css3", "path/to/css1", "/path/to/css2"])
check("inheritance: no warning", w, [])
extended_js, w = run_with_warnings(lambda: (base + child_def)._js)
check("inheritance: js", extended_js, ["/path/to/js1", "js2", "js3", "/path/to/js4"])
check("inheritance js: no warning", w, [])

# docs/topics/forms/media.txt example.
calendar = Media(js=("jQuery.js", "calendar.js", "noConflict.js"))
time = Media(js=("jQuery.js", "time.js", "noConflict.js"))
merged, w = run_with_warnings(lambda: (calendar + time)._js)
check("docs example: calendar + time", merged, ["jQuery.js", "calendar.js", "time.js", "noConflict.js"])
check("docs example: no warning", w, [])

print()
print("== 6. Genuine conflicts still warn, edge cases ==")

# A genuine 3-way cycle must still warn (constraints from each list).
cyc = Media(js=["A.js", "B.js"]) + Media(js=["B.js", "C.js"]) + Media(js=["C.js", "A.js"])
result, caught = run_with_warnings(lambda: cyc._js)
check("3-way cycle warns", [w_.category.__name__ for w_ in caught], ["MediaOrderConflictWarning"])
print("     3-way cycle resolved to: %r" % (result,))
check("3-way cycle result has all elements once", sorted(result), ["A.js", "B.js", "C.js"])

# Genuine 2-way conflict keeps the pinned result and message.
result, caught = run_with_warnings(lambda: (Media(js=["text-editor.js", "text-editor-extras.js"]) + Media(js=["text-editor-extras.js", "text-editor.js"]))._js)
check("genuine 2-way conflict result", result, ["text-editor.js", "text-editor-extras.js"])
check("genuine 2-way conflict warns", [w_.category.__name__ for w_ in caught], ["MediaOrderConflictWarning"])

# Interleaved three-way merge where a valid order exists (issue variant).
a = Media(js=["one.js", "two.js", "three.js"])
b = Media(js=["one.js", "three.js"])
c = Media(js=["one.js", "two.js"])
check_no_warning("one,two,three variant: no warning", lambda: (a + b + c)._js)
check("one,two,three variant: order", (a + b + c)._js, ["one.js", "two.js", "three.js"])

# Empty media edge cases.
check("empty Media js", list(Media()._js), [])
check("empty Media css", Media()._css, {})
check("str(Media())", str(Media()), "")
check("merge() with no args", Media.merge(), [])
check("merge([a], []) keeps order", Media.merge(["a"], []), ["a"])
check("merge([], [a]) keeps order", Media.merge([], ["a"]), ["a"])
check("merge with empty lists interspersed", Media.merge([], ["a"], [], ["b"], []), ["a", "b"])
check("merge single list", Media.merge(["b", "a"]), ["b", "a"])

# Render still works end-to-end.
media = Media(css={"all": ["/path/to/css"]}, js=["/path/to/js"])
check("str(media) round trip", str(media).count("<script"), 1)

# ---------------------------------------------------------------------------
# Differential fuzz: old algorithm vs new algorithm, two-list merges.
# ---------------------------------------------------------------------------
print()
print("== 7. Differential fuzz: old vs new merge (2 lists) ==")


def old_merge(list_1, list_2):
    """Verbatim copy of the pre-fix merge implementation."""
    combined_list = list(list_1)
    last_insert_index = len(list_1)
    for path in reversed(list_2):
        try:
            index = combined_list.index(path)
        except ValueError:
            combined_list.insert(last_insert_index, path)
        else:
            if index > last_insert_index:
                warnings.warn("conflict", MediaOrderConflictWarning)
            last_insert_index = index
    return combined_list


import django.forms.widgets as widgets_module  # noqa: E402

MediaOrderConflictWarning = widgets_module.MediaOrderConflictWarning


def has_cycle(lists):
    """True if the union of the constraints imposed by the lists is cyclic.

    Duplicated elements within a single list are ignored (duplicated media
    definitions are ignored), so only deduplicated consecutive pairs count.
    """
    graph = {}
    for list_ in lists:
        seen = []
        for element in list_:
            if element not in seen:
                if seen:
                    graph.setdefault(element, set()).add(seen[-1])
                seen.append(element)

    def _visit(node, visiting, visited):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, ()):  # noqa: B023
            if _visit(dep, visiting, visited):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    visited, visiting = set(), set()
    return any(_visit(node, visiting, visited) for node in list(graph))


def dedupe(list_):
    result = []
    for element in list_:
        if element not in result:
            result.append(element)
    return result


random.seed(20260906)
pool = list(range(5))
mismatches = warned_both = acyclic = cyclic = 0
for _ in range(20000):
    # Duplicate-free lists: old and new must agree exactly.
    list1 = dedupe(random.choices(pool, k=random.randint(0, 4)))
    list2 = dedupe(random.choices(pool, k=random.randint(0, 4)))
    cyclic_case = has_cycle([list1, list2])
    old_result, old_w = run_with_warnings(lambda: old_merge(list1, list2))
    new_result, new_w = run_with_warnings(lambda: Media.merge(list1, list2))
    old_warned, new_warned = bool(old_w), bool(new_w)
    if cyclic_case:
        cyclic += 1
        if not (old_warned and new_warned):
            mismatches += 1
            print("CYCLE MISMATCH: %r %r old_warned=%s new_warned=%s" % (list1, list2, old_warned, new_warned))
    else:
        acyclic += 1
        if old_result != new_result:
            mismatches += 1
            if mismatches < 10:
                print("ORDER MISMATCH: %r %r old=%r new=%r" % (list1, list2, old_result, new_result))
        if old_warned or new_warned:
            mismatches += 1
            print("SPURIOUS WARNING: %r %r" % (list1, list2))
    if old_warned and new_warned:
        warned_both += 1
print("acyclic cases: %d, cyclic cases: %d, both-warned: %d, mismatches: %d" % (acyclic, cyclic, warned_both, mismatches))
if mismatches:
    failures.append("differential fuzz")

# ---------------------------------------------------------------------------
# Multi-list property fuzz.
# ---------------------------------------------------------------------------
print()
print("== 8. Multi-list property fuzz ==")


def violates(lists, result):
    position = {element: i for i, element in enumerate(result)}
    for list_ in lists:
        seen = []
        for element in list_:
            if element not in seen:
                seen.append(element)
        for before, after in zip(seen, seen[1:]):
            if position[before] > position[after]:
                return (before, after)
    return None


random.seed(11019)
bad = 0
for _ in range(20000):
    lists = [random.choices(pool, k=random.randint(0, 5)) for _ in range(random.randint(1, 5))]
    result, caught = run_with_warnings(lambda: Media.merge(*lists))
    if len(result) != len(set(result)) or set(result) != set(itertools.chain(*lists)):
        bad += 1
        print("NOT A DEDUP PERMUTATION: %r -> %r" % (lists, result))
        continue
    violation = violates(lists, result)
    if violation and not caught:
        bad += 1
        print("UNWARNED VIOLATION: %r -> %r (inversion %r)" % (lists, result, violation))
if bad:
    failures.append("multi-list property fuzz")
print("property violations: %d" % bad)

print()
print("=" * 60)
if failures:
    print("%d/%d checks FAILED: %s" % (len(failures), checks, failures))
    sys.exit(1)
print("All %d checks passed." % checks)
