Page({
  data: {
    banners: ['图片一', '图片二', '图片三'],
    currentIndex: 0,
    productName: 'ProSound X 智能降噪运动耳机',
    priceText: '499.00',          // 金额在 JS 里格式化好, 不在 WXML 里调 toFixed
    originalPriceText: '799.00',
    tags: ['主动降噪', 'IPX7 防水', '超长续航'],
    descriptionText: '采用新一代 AI 降噪芯片, 有效隔绝环境噪音; 人体工学设计佩戴稳固, 蓝牙 5.3 连接稳定, 适合运动与通勤等多种场景。'
  },

  onLoad() {},

  onSwiperChange(e) {
    this.setData({ currentIndex: e.detail.current });
  },

  onAddToCart() {
    wx.showToast({ title: '已加入购物车', icon: 'success' });
  }
});
