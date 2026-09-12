import subprocess

# 12 v1 failures: worktree -> (test file, failing test names)
CASES = {
    "django__django-11001": ("django/db/models/sql/compiler.py", "django/db/models/fields/json.py",
                             ["test_order_by_multiline_sql", "test_order_of_operations"]),
    "django__django-11019": ("tests/forms_tests/tests/test_media.py",),
    "django__django-11283": ("tests/auth_tests/test_migrations.py",),
    "django__django-11564": ("tests/settings_tests/tests.py",),
    "django__django-11630": ("tests/check_framework/test_model_checks.py",),
    "django__django-11797": ("tests/lookup/tests.py",),
    "django__django-12308": ("tests/admin_utils/tests.py",),
    "django__django-12589": ("tests/aggregation/tests.py",),
    "django__django-12856": ("tests/invalid_models_tests/test_models.py",),
    "pylint-dev__pylint-6506": ("tests/config/test_config.py",),
    "pytest-dev__pytest-5103": ("testing/test_assertrewrite.py",),
    "pytest-dev__pytest-5221": ("testing/python/fixtures.py",),
}

TEST_NAMES = {
    "django__django-11001": ["test_order_by_multiline_sql", "test_order_of_operations"],
    "django__django-11019": ["test_combine_media", "test_construction", "test_form_media"],
    "django__django-11283": ["test_migrate_with_existing_target_permission"],
    "django__django-11564": ["test_add_script_name_prefix", "test_not_prefixed"],
    "django__django-11630": ["test_collision_across_apps_database_routers_installed",
                             "test_collision_in_same_app_database_routers_installed"],
    "django__django-11797": ["test_exact_query_rhs_with_selected_columns"],
    "django__django-12308": ["test_json_display_for_field", "test_label_for_field"],
    "django__django-12589": ["test_group_by_exists_annotation", "test_group_by_subquery_annotation"],
    "django__django-12856": ["test_unique_constraint_pointing_to_m2m_field",
                             "test_unique_constraint_pointing_to_missing_field",
                             "test_unique_constraint_pointing_to_non_local_field"],
    "pylint-dev__pylint-6506": ["test_unknown_option_name", "test_unknown_short_option_name"],
    "pytest-dev__pytest-5103": ["test_unroll_expression", "test_unroll_generator",
                                "test_unroll_list_comprehension"],
    "pytest-dev__pytest-5221": ["test_show_fixtures_verbose"],
}

W = r"D:\mio\worktrees"

for iid, files in CASES.items():
    wt = W + "\\" + iid
    names = TEST_NAMES.get(iid, [])
    found = {}
    for f in files:
        for n in names:
            try:
                r = subprocess.run(
                    ["git", "-C", wt, "grep", "-c", "def " + n + "(", "HEAD", "--", f],
                    capture_output=True, text=True)
                if r.returncode == 0 and r.stdout.strip():
                    found[n] = "PUBLIC(base)"
            except Exception:
                pass
    missing = [n for n in names if n not in found]
    print(iid)
    for n in names:
        tag = "PUBLIC(base 有此测试)" if n in found else "HIDDEN(test_patch 新增或改写)"
        print("  ", n, "->", tag)
    if missing:
        pass
