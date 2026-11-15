# xninetzy-security-testing — §48

## 48. Interaction Protocol

When the owner requests a network assessment:

```text
1. Parse target.
2. Normalize target.
3. Check protected target policy.
4. Build ScopeManifest.
5. Determine assessment profile.
6. Check private-target requirements.
7. Check scanner availability.
8. Create ephemeral security session.
9. Lock target lease.
10. Execute least-invasive phase first.
11. Expand only within declared scope/profile.
12. Correlate evidence.
13. Validate findings.
14. Generate report.
15. Emit audit summary.
16. Store regression candidates.
```

Do not ask repetitive questions that are already explicitly answered by the current scope.

---
