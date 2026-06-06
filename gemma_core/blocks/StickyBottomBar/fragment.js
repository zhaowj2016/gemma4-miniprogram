/* BLOCK_SPEC_JSON
{"data":{"stickyBottomBarTitle":"Ready to continue","stickyBottomBarDesc":"Mock action only","stickyBottomBarButtonText":"Continue"},"methods":{"onStickyBottomBarTap":"function() { this.setData({ stickyBottomBarButtonText: 'Selected' }); }"}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    stickyBottomBarTitle: 'Ready to continue',
    stickyBottomBarDesc: 'Mock action only',
    stickyBottomBarButtonText: 'Continue'
  },
  onStickyBottomBarTap: function() {
    this.setData({ stickyBottomBarButtonText: 'Selected' });
  }
});
