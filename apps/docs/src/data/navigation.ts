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
    title: 'Start',
    items: [
      { title: 'Introduction', description: 'Xninetzy concepts and capabilities.', href: '/docs/introduction/' },
      { title: 'Quick start', description: 'Run the stack for the first time.', href: '/docs/getting-started/' },
      { title: 'Configuration', description: 'Environment and persistence.', href: '/docs/configuration/' },
      { title: 'Architecture', description: 'Services, data flow, and system boundaries.', href: '/docs/architecture/' }
    ]
  },
  {
    title: 'Integrations',
    items: [
      { title: 'WhatsApp', description: 'Chat, groups, media, and commands.', href: '/docs/whatsapp/' },
      { title: 'Obsidian', description: 'Vault, notes, knowledge, and filesystem guards.', href: '/docs/obsidian/' },
      { title: 'HEBAT / Moodle', description: 'Courses, activities, files, and assignments.', href: '/docs/hebat/' },
      { title: 'OS kernel', description: 'Capture, triage, and the attention queue.', href: '/docs/os-kernel/' },
      { title: 'Learning roadmap', description: 'Adaptive planning and source linkage.', href: '/docs/learning-roadmaps/' }
    ]
  },
  {
    title: 'AI & developer tools',
    items: [
      { title: 'LLM providers', description: 'Flaz and other providers.', href: '/docs/providers/' },
      { title: 'Global MCP', description: 'Codex, Claude, and OpenCode.', href: '/docs/mcp/' },
      { title: 'Coding agents', description: 'Run coding runtimes from WhatsApp.', href: '/docs/coding-agents/' },
      { title: 'Lightning agent', description: 'Rewards, strategy ranking, and regression.', href: '/docs/lightning/' },
      { title: 'Shared skills', description: 'Built-in and open-source skills shared across interfaces.', href: '/docs/skills/' }
    ]
  },
  {
    title: 'Operations',
    items: [
      { title: 'HTTP API', description: 'AI and WhatsApp engine endpoints.', href: '/docs/api/' },
      { title: 'Testing', description: 'Test suites and quality gates.', href: '/docs/testing/' },
      { title: 'Automation', description: 'Briefings, reviews, job leases, and freshness.', href: '/docs/automation/' },
      { title: 'Local data', description: 'Private per-installation SQLite data.', href: '/docs/local-data/' },
      { title: 'Backup & restore', description: 'Snapshots, verification, retention, and recovery.', href: '/docs/backup-restore/' },
      { title: 'Security', description: 'Hardening and threat boundaries.', href: '/docs/security/' },
      { title: 'Troubleshooting', description: 'Diagnose common problems.', href: '/docs/troubleshooting/' }
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
