Page({
  data: {
    banners: ['门头环境', '主理区域', '细节陈设'],
    bannerIndex: 0,
    storeName: '山隐茶事 · 静安店',
    ratingText: '4.8',
    avgPriceText: '88.00',
    categoryText: '茶饮 · 简餐',
    addressText: '上海市静安区南京西路 1788 号 9 楼 901 室',
    features: [
      '原产地直采, 茶叶新鲜看得见',
      '独立茶艺师, 一对一冲泡指导',
      '静谧包间, 适合商务洽谈',
      '提供茶道体验课程, 接受团体预约'
    ],
    hours: [
      { dayText: '周一至周五', timeText: '10:00 - 22:00' },
      { dayText: '周六', timeText: '09:30 - 23:00' },
      { dayText: '周日', timeText: '09:30 - 23:00' }
    ],
    reviews: [
      {
        id: 'r001',
        name: '陈先生',
        ratingText: '5.0',
        text: '环境很安静, 茶艺师专业, 适合一个人来放空。',
        dateText: '2026-05-21'
      },
      {
        id: 'r002',
        name: '林女士',
        ratingText: '4.8',
        text: '点了大红袍, 茶汤清亮; 配的茶点很精致。',
        dateText: '2026-05-18'
      }
    ]
  },

  onBannerChange(e) {
    this.setData({ bannerIndex: e.detail.current });
  },

  onCallTap() {
    wx.showToast({ title: '拨打店铺电话', icon: 'none' });
  },

  onMapTap() {
    wx.showToast({ title: '查看地图位置', icon: 'none' });
  },

  onShareTap() {
    wx.showToast({ title: '已复制店铺链接', icon: 'success' });
  }
});
