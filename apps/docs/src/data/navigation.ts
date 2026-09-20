export type NavItem = {
  title: string;
  description: string;
  href: string;
  badge?: 'new' | 'updated' | 'core';
};

export type NavGroup = {
  title: string;
  items: NavItem[];
};

export const navigation: NavGroup[] = [
  {
    title: 'Start',
    items: [
      { title: 'Introduction', description: 'Xninetzy concepts and capabilities.', href: '/docs/introduction/', badge: 'core' },
      { title: 'MCP system reference', description: 'Transports, registry, gateway, tasks, trace, security.', href: '/docs/mcp-system/', badge: 'new' },
      { title: 'Quick start', description: 'Run the stack for the first time.', href: '/docs/getting-started/' },
      { title: 'Configuration', description: 'Environment, paths, and safety knobs.', href: '/docs/configuration/' },
      { title: 'Architecture', description: 'Services, data flow, and system boundaries.', href: '/docs/architecture/', badge: 'core' }
    ]
  },
  {
    title: 'Reference',
    items: [
      { title: 'Skill catalog', description: '70 built-in skills, one row each, with repair pointers.', href: '/docs/skills/', badge: 'updated' },
      { title: 'Skill repair runbook', description: 'Fix broken SKILL.md YAML outside Claude Code.', href: '/KNOWN_ISSUES.md', badge: 'new' },
      { title: 'Known issues', description: 'Authoritative tracker (ISS-NNN IDs).', href: '/KNOWN_ISSUES.md', badge: 'new' },
      { title: 'Changelog', description: 'Per-version release notes.', href: '/CHANGELOG.md', badge: 'new' }
    ]
  },
  {
    title: 'Integrations',
    items: [
      { title: 'Obsidian', description: 'Vault, notes, knowledge, and filesystem guards.', href: '/docs/obsidian/' },
      { title: 'HEBAT / Moodle', description: 'Courses, activities, files, and assignments.', href: '/docs/hebat/' },
      { title: 'Cyber Campus', description: 'Portal tools, grade tokens, and KRS War.', href: '/docs/cyber-campus/' },
      { title: 'OS kernel', description: 'Capture, triage, and the attention queue.', href: '/docs/os-kernel/' },
      { title: 'Learning roadmaps', description: 'Adaptive planning, concepts, and recall.', href: '/docs/learning-roadmaps/' }
    ]
  },
  {
    title: 'AI & developer tools',
    items: [
      { title: 'Chat model selection', description: 'Host supplies the model; HTTP bridge fallback is optional.', href: '/docs/providers/' },
      { title: 'Global MCP', description: 'Codex, Claude Code, and OpenCode.', href: '/docs/mcp/', badge: 'core' },
      { title: 'Lightning agent', description: 'Rewards, strategy ranking, and regression.', href: '/docs/lightning/' },
      { title: 'Shared skills', description: 'Built-in and open-source skills across clients.', href: '/docs/skills/', badge: 'updated' }
    ]
  },
  {
    title: 'Operations',
    items: [
      { title: 'HTTP API', description: 'FastAPI surface for /api/chat, reminders, debug.', href: '/docs/api/' },
      { title: 'Action policy', description: 'Auto, approval, manual, and final gates.', href: '/docs/action-policy/' },
      { title: 'Testing', description: 'Test suites and quality gates.', href: '/docs/testing/' },
      { title: 'Automation', description: 'Briefings, reviews, leases, and freshness.', href: '/docs/automation/' },
      { title: 'Data intelligence', description: 'Profile, quality, tables, dashboards.', href: '/docs/data-intelligence/' },
      { title: 'Learning & evolution', description: 'Evaluation, learning, lightning, patches, rollback.', href: '/docs/learning-system/' },
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
