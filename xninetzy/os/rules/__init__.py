"""User rules / policy defense system.

Lets the user define behavioral rules ("jangan ...", "selalu ...", style rules)
that are stored in SQLite and injected into the agent prompt so the assistant
actually obeys them. Safety-type rules cannot be overridden by normal users.
"""
