Page({
  data: {
    areaName: '浦东 · 联洋板块',
    propertyCountText: '186',
    currentFilter: 'all',
    filters: [
      { key: 'all', name: '全部' },
      { key: 'new', name: '新上' },
      { key: 'discount', name: '降价' },
      { key: 'school', name: '学区房' },
      { key: 'subway', name: '近地铁' }
    ],
    properties: [
      {
        id: 'h001',
        coverText: '房源实景',
        tagText: '新上',
        photoCountText: '12',
        title: '仁恒河滨城 · 南北通透三房, 满五唯一',
        roomCountText: '3',
        hallCountText: '2',
        areaText: '128',
        floorText: '中高楼层 / 共 28 层',
        tags: ['南北通透', '精装修', '满五唯一'],
        priceText: '1,580',
        unitPriceText: '12.3 万',
        subwayText: '距 2 号线 500m',
        schoolText: '对口进才实验小学'
      },
      {
        id: 'h002',
        coverText: '房源实景',
        tagText: '降价',
        photoCountText: '8',
        title: '世茂滨江花园 · 经典两房, 江景可看',
        roomCountText: '2',
        hallCountText: '1',
        areaText: '95',
        floorText: '高楼层 / 共 32 层',
        tags: ['江景', '近地铁', '随时看房'],
        priceText: '988',
        unitPriceText: '10.4 万',
        subwayText: '距 4 号线 280m',
        schoolText: '对口陆家嘴附小'
      },
      {
        id: 'h003',
        coverText: '房源实景',
        tagText: '',
        photoCountText: '15',
        title: '香江花园 · 经典复式, 送私家花园',
        roomCountText: '4',
        hallCountText: '2',
        areaText: '186',
        floorText: '1-2 层 / 共 6 层',
        tags: ['复式', '花园', '车位'],
        priceText: '2,180',
        unitPriceText: '11.7 万',
        subwayText: '距 7 号线 800m',
        schoolText: '对口福山外国语小学'
      }
    ]
  },

  onFilterTap(e) {
    this.setData({ currentFilter: e.currentTarget.dataset.key });
  },

  onPropertyTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '打开房源 ' + id, icon: 'none' });
  }
});
