// @ts-check

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Sidebar for the SlicePizza documentation. The order of the pages is defined
 * here (not with sidebar_position front matter).
 *
 * The ADRs have their own sidebar: see sidebarsAdr.js.
 *
 * @type {import('@docusaurus/plugin-content-docs').SidebarsConfig}
 */
const sidebars = {
  docsSidebar: [
    'intro',
    'tour',
    {
      type: 'category',
      label: 'Phase 1',
      items: ['phase-1/overview', 'phase-1/api', 'phase-1/docker'],
    },
    {
      type: 'category',
      label: 'Phase 2',
      items: ['phase-2/overview', 'phase-2/site-and-proxy'],
    },
    {
      type: 'category',
      label: 'Phase 3',
      items: [
        'phase-3/overview',
        'phase-3/events',
        'phase-3/notifications',
        'phase-3/kitchen',
      ],
    },
    {
      type: 'category',
      label: 'Phase 4',
      items: ['phase-4/overview', 'phase-4/pipeline', 'phase-4/versions'],
    },
    {
      type: 'category',
      label: 'Phase 5',
      items: ['phase-5/overview'],
    },
    {
      type: 'category',
      label: 'Phase 6',
      items: ['phase-6/overview'],
    },
    {
      type: 'category',
      label: 'Phase 7',
      items: ['phase-7/overview'],
    },
    {
      type: 'category',
      label: 'Phase 8',
      items: ['phase-8/overview'],
    },
  ],
};

export default sidebars;
