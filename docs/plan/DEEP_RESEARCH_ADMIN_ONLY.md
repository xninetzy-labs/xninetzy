# Deep Research Admin Only

Tujuan: membatasi `/deep-research` agar hanya admin utama, sender bernama Misbahul, atau admin grup yang bisa menjalankan riset berat.

Command:
• `/research <topik>` boleh untuk semua user, search ringan.
• `/deep-research <topik>` admin-only.

Permission:
• `ADMIN_JID`
• `ADMIN_NAMES`
• group metadata `isGroupAdmin` / `groupAdmins`

Jika ditolak, user diarahkan ke `/research`, YouTube search ringan, atau penjelasan ringkas.

Batasan: fallback MCP group admin sudah tersedia, tetapi jalur command mengandalkan metadata WA payload.
