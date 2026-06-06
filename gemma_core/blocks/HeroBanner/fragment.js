/* BLOCK_SPEC_JSON
{"data":{"heroBannerCurrent":0,"heroBannerSlides":[{"id":"h1","eyebrow":"Featured","title":"Smart launch kit","desc":"A polished mini-program section assembled from local mock data."},{"id":"h2","eyebrow":"New","title":"Modular page flow","desc":"Plan, fill, assemble, validate, and repair with stable blocks."}]},"methods":{"onHeroBannerChange":"function(e) { this.setData({ heroBannerCurrent: e.detail.current }); }"}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    heroBannerCurrent: 0,
    heroBannerSlides: [
      { id: 'h1', eyebrow: 'Featured', title: 'Smart launch kit', desc: 'A polished mini-program section assembled from local mock data.' },
      { id: 'h2', eyebrow: 'New', title: 'Modular page flow', desc: 'Plan, fill, assemble, validate, and repair with stable blocks.' }
    ]
  },
  onHeroBannerChange: function(e) {
    this.setData({ heroBannerCurrent: e.detail.current });
  }
});
