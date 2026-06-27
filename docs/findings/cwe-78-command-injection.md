# CWE-78: Command injection found by data-flow analysis

**Tool:** CodeQL (semantic SAST) · **Severity:** Critical · **Missed by:** pattern-based scanning

## Summary

CodeQL traced untrusted input from an external **source** to a command-execution
**sink** across multiple function boundaries — a path that pattern-based scanning did
not flag, because no single line looked dangerous in isolation. This is the canonical
case for taint-tracking: the vulnerability lives in the *flow*, not in any one
statement.

## The flow

CodeQL's data-flow analysis follows tainted data through assignments, function calls,
and returns:

```
source            user-controlled input enters the program
   │
   ▼
   ├─ passed to a helper function (no validation)
   │
   ▼
   ├─ concatenated into a command string
   │
   ▼
sink              string reaches a shell-exec call (e.g. os.system / subprocess shell=True)
```

Because the source and sink sit in **different functions**, a pattern rule scoped to a
single function or a regex over one line cannot connect them. CodeQL models the call
graph and propagates taint across it, so the source→sink path surfaces as one finding.

## Why pattern-matching missed it

A pattern engine (e.g. Semgrep with a default ruleset) flags *shapes of code*: "a call
to `os.system` with a non-literal argument." If the dangerous call is wrapped behind a
helper, or the tainted value is assembled a few hops upstream, the shape at the sink
looks benign and the source looks like ordinary input handling. Neither line alone
trips the rule.

## Takeaway

- **Semantic analysis earns its slower runtime** on exactly this class — cross-function,
  flow-dependent injection — where the bug is the *connection* between safe-looking parts.
- **Query-suite choice matters.** `security-extended` raises precision; `security-and-quality`
  widens coverage. Pick by whether the repo can absorb more findings to triage or needs a
  tighter, higher-confidence signal.
- **Remediation:** validate/escape at the trust boundary and avoid shell interpolation —
  pass arguments as a list to `subprocess` with `shell=False`, not a concatenated string.
