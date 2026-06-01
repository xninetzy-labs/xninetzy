CONFIRMATION_REQUIRED_ACTIONS = {
    "overwrite_note",
    "rename_note",
    "move_note",
    "delete_note",
    "bulk_edit",
    "bulk_reminder_create",
    "enable_recurring_workflow",
    "send_wa_to_other",
    "change_group",
}


def requires_confirmation(action: str | None) -> bool:
    return bool(action and action in CONFIRMATION_REQUIRED_ACTIONS)
