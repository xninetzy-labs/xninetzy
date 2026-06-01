"""Lightning Agent — lightweight self-improvement loop.

MVP: log execution traces, capture user feedback, turn negative feedback /
recurring errors into improvement *proposals*, and require admin approval before
applying. Applying a 'rule' proposal creates a user_rule (safe, reversible).
No global prompt/behavior is changed automatically.
"""
