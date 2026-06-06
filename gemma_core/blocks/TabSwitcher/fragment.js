/* BLOCK_SPEC_JSON
{"data":{"tabSwitcherTabs":[{"id":"overview","label":"Overview"},{"id":"details","label":"Details"},{"id":"faq","label":"FAQ"}],"tabSwitcherActiveTitle":"Overview","tabSwitcherActiveDesc":"Segmented local state without remote APIs."},"methods":{"onTabSwitcherTap":"function() { this.setData({ tabSwitcherActiveTitle: 'Details', tabSwitcherActiveDesc: 'Updated by a local mock handler.' }); }"}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    tabSwitcherTabs: [
      { id: 'overview', label: 'Overview' },
      { id: 'details', label: 'Details' },
      { id: 'faq', label: 'FAQ' }
    ],
    tabSwitcherActiveTitle: 'Overview',
    tabSwitcherActiveDesc: 'Segmented local state without remote APIs.'
  },
  onTabSwitcherTap: function() {
    this.setData({ tabSwitcherActiveTitle: 'Details', tabSwitcherActiveDesc: 'Updated by a local mock handler.' });
  }
});
