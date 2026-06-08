/* BLOCK_SPEC_JSON
{"data":{"emptyStateTitle":"Nothing here yet","emptyStateDesc":"Use this block when lists or searches have no local mock results.","emptyStateButtonText":"Refresh mock"},"methods":{"onEmptyStateTap":"function() { this.setData({ emptyStateButtonText: 'Refreshed' }); }"}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    emptyStateTitle: 'Nothing here yet',
    emptyStateDesc: 'Use this block when lists or searches have no local mock results.',
    emptyStateButtonText: 'Refresh mock'
  },
  onEmptyStateTap: function() {
    this.setData({ emptyStateButtonText: 'Refreshed' });
  }
});
