Page({
  data: {
    categoryName: '精选好物',
    productCountText: '48',
    currentFilter: 'all',
    filters: [
      { key: 'all', name: '全部' },
      { key: 'new', name: '新品' },
      { key: 'hot', name: '热销' },
      { key: 'sale', name: '促销' },
      { key: 'recommend', name: '推荐' }
    ],
    products: [
      {
        id: 'p001',
        coverText: '主图一',
        tagText: '热销',
        title: '智能保温杯',
        subText: '316 不锈钢 / 24h 保温',
        priceText: '129.00',
        salesText: '1.2万'
      },
      {
        id: 'p002',
        coverText: '主图二',
        tagText: '',
        title: '便携蓝牙音箱',
        subText: 'IPX7 防水 / 续航 12h',
        priceText: '259.00',
        salesText: '3.4千'
      },
      {
        id: 'p003',
        coverText: '主图三',
        tagText: '新品',
        title: '人体工学椅',
        subText: '腰托可调 / 静音轮',
        priceText: '899.00',
        salesText: '628'
      },
      {
        id: 'p004',
        coverText: '主图四',
        tagText: '促销',
        title: '速干运动 T 恤',
        subText: '透气 / 多色可选',
        priceText: '79.00',
        salesText: '8.9千'
      }
    ]
  },

  onFilterTap(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ currentFilter: key });
  },

  onProductTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '查看商品 ' + id, icon: 'none' });
  }
});
