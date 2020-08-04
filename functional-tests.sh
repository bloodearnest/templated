#!/bin/bash
set -eu

CONTEXT=$(mktemp)
ENVFILE=$(mktemp)
RESULT=$(mktemp)
TEMPLATE=$(mktemp)
REIFY=${REIFY:-./reify}

OK="\e[32mOK  \e[0m"
FAIL="\e[31mFAIL\e[0m"

echo "'{{ test }}' '{{ env['TEST'] }}'" > "$TEMPLATE"

run()
{
    # shellcheck disable=SC2068
    $REIFY "$TEMPLATE" $@ -o "$RESULT"
}

assert()
{
    echo -n "$1..."
    test "$(<"$RESULT")" = "$2" && echo -e "$OK" || echo -e "$FAIL: $(<"$RESULT") != $2"
}

assert_mode()
{
    echo -n "$1..."
    test "$(stat -c %a "$RESULT")" = "$2" && echo -e "$OK" || echo -e "$FAIL: $(stat -c %a "$RESULT") != $2"
}

$REIFY "$TEMPLATE" > "$RESULT"
assert "default output is stdout" "'' ''"

$REIFY "$TEMPLATE" -o - > "$RESULT"
assert "'-' is stdout" "'' ''"

run
assert "no context" "'' ''"

echo 'test: stdin' | run
assert "context from stdin" "'stdin' ''"

echo 'test: file' > "$CONTEXT"
run -c "$CONTEXT"
assert "context from file" "'file' ''"

run test=extra
assert "context from extra" "'extra' ''"

TEST=envvar run
assert "context from envvar" "'' 'envvar'"

echo 'TEST=envfile' > "$ENVFILE"
run  -e "$ENVFILE"
assert "context from envfile" "'' 'envfile'"

echo 'test: file' > "$CONTEXT"
echo 'test: stdin' | run  -c "$CONTEXT"
assert "file overrides stdin" "'file' ''"

echo 'test: file' > "$CONTEXT"
run  test=extra -c "$CONTEXT"
assert "extra overrides file" "'extra' ''"

echo 'test: stdin' | run  test=extra
assert "extra overrides stdin" "'extra' ''"

echo "" | run
assert "empty stdin" "'' ''"

echo "" | run --charm-config config.yaml
assert "charm config" "'charm default' ''"

(umask 022; run)
assert_mode "default mode is 0666 - umask" 644

(umask 022; run -m 400)
assert_mode "mode 0400" 400
