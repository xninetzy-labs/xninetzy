export type NavItem = {
  title: string;
  description: string;
  href: string;
  eyebrow?: string;
};

export type NavGroup = {
  title: string;
  items: NavItem[];
};

export const navigation: NavGroup[] = [
  {
    title: 'Mulai',
    items: [
      { title: 'Pengenalan', description: 'Konsep dan kemampuan Xninetzy.', href: '/docs/introduction/' },
      { title: 'Quick start', description: 'Jalankan stack pertama kali.', href: '/docs/getting-started/' },
      { title: 'Konfigurasi', description: 'Environment dan persistence.', href: '/docs/configuration/' },
      { title: 'Arsitektur', description: 'Service, alur data, dan batas sistem.', href: '/docs/architecture/' }
    ]
  },
  {
    title: 'Integrasi',
    items: [
      { title: 'WhatsApp', description: 'Chat, group, media, dan command.', href: '/docs/whatsapp/' },
      { title: 'Obsidian', description: 'Vault, note, knowledge, dan guard.', href: '/docs/obsidian/' },
      { title: 'HEBAT / Moodle', description: 'Course, activity, file, dan tugas.', href: '/docs/hebat/' }
    ]
  },
  {
    title: 'AI & developer tools',
    items: [
      { title: 'Provider LLM', description: 'Flaz dan provider lain.', href: '/docs/providers/' },
      { title: 'MCP global', description: 'Codex, Claude, dan OpenCode.', href: '/docs/mcp/' },
      { title: 'Coding agents', description: 'Jalankan runtime coding dari WA.', href: '/docs/coding-agents/' }
    ]
  },
  {
    title: 'Operasional',
    items: [
      { title: 'HTTP API', description: 'Endpoint AI dan WA engine.', href: '/docs/api/' },
      { title: 'Testing', description: 'Test suite dan quality gates.', href: '/docs/testing/' },
      { title: 'Backup & restore', description: 'Snapshot, verifikasi, retensi, dan recovery.', href: '/docs/backup-restore/' },
      { title: 'Keamanan', description: 'Hardening dan threat boundaries.', href: '/docs/security/' },
      { title: 'Troubleshooting', description: 'Diagnosis masalah umum.', href: '/docs/troubleshooting/' }
    ]
  }
];

export const flatNavigation = navigation.flatMap((group) =>
  group.items.map((item) => ({ ...item, eyebrow: group.title }))
);

export function normalizePath(pathname: string): string {
  return pathname.endsWith('/') ? pathname : `${pathname}/`;
}

export function pageNeighbors(pathname: string): { previous?: NavItem; next?: NavItem } {
  const normalized = normalizePath(pathname);
  const index = flatNavigation.findIndex((item) => item.href === normalized);

  if (index === -1) return {};

  return {
    previous: flatNavigation[index - 1],
    next: flatNavigation[index + 1]
  };
}
