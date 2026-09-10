# django__django-11099 — UsernameValidator allows trailing newline

## Root cause
`ASCIIUsernameValidator` and `UnicodeUsernameValidator` (django/contrib/auth/validators.py)
used regex `^[\w.@+-]+$`. In Python regex, `$` also matches just before a trailing
newline, so usernames ending in `\n` were accepted although only `[A-Za-z0-9.@+-]`
characters should be allowed.

## Fix
Changed both validators' regex to `\A[\w.@+-]+\Z`:
- `\A` anchors at the true string start (equivalent to `^` here since no MULTILINE)
- `\Z` anchors at the absolute string end and, unlike `$`, never matches before a
  trailing newline.

## Files touched
- django/contrib/auth/validators.py (2 lines, the two regex attributes)

## Verification
- runs/verify.py loads validators.py directly (bypassing the heavy
  django.contrib.auth package init) and checks: plain username `abc.1@x` accepted;
  `abc\n` rejected — for BOTH validators. Output: ALL_OK.
- Fix is identical to the upstream resolution of this ticket.

## Confidence
High.
