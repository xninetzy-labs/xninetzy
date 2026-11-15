# code-review — §80

## 80. Final Principle

The code review engine should behave like:

```text
DIFF ANALYZER
+
RULE ENFORCER
+
BEHAVIOR REVIEWER
+
ARCHITECTURE REVIEWER
+
SECURITY ROUTER
+
TEST / REGRESSION ANALYZER
```

not:

```text
STYLE LINTER
```

The quality bar is:

```text
diff evidence
+
repository context
+
project rules
+
behavioral reasoning
+
architecture evidence
+
security evidence
+
test evidence
+
regression analysis
```

A strong review does not merely say:

```text
"LGTM"
```

or:

```text
"fix this"
```

It explains:

```text
what changed
why it matters
what evidence supports the finding
what boundary is affected
what should change
how the fix can be verified
```

### and gives a deterministic verdict based on the repository's actual merge policy.
