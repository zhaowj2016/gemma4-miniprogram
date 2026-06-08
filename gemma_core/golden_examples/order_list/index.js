Page({
  data: {
    currentTab: 'all',
    tabs: [
      { key: 'all', name: '全部' },
      { key: 'pay', name: '待付款' },
      { key: 'ship', name: '待发货' },
      { key: 'receive', name: '待收货' },
      { key: 'review', name: '待评价' }
    ],
    orders: [
      {
        id: 'o001',
        shopName: '山隐茶事旗舰店',
        statusText: '待发货',
        statusClass: 'status-warn',
        coverText: '商品图',
        goodsTitle: '明前龙井 头采 50g 礼盒装',
        specText: '50g / 盒 · 礼盒版',
        priceText: '328.00',
        qtyText: '1',
        totalText: '328.00',
        actionText: '提醒发货',
        showCancel: true
      },
      {
        id: 'o002',
        shopName: '云策自营',
        statusText: '待收货',
        statusClass: 'status-info',
        coverText: '商品图',
        goodsTitle: '智能保温杯 · 316 不锈钢',
        specText: '深空灰 / 500ml',
        priceText: '129.00',
        qtyText: '2',
        totalText: '258.00',
        actionText: '确认收货',
        showCancel: false
      },
      {
        id: 'o003',
        shopName: '原野户外',
        statusText: '已完成',
        statusClass: 'status-success',
        coverText: '商品图',
        goodsTitle: '徒步登山鞋 防水透气',
        specText: '42 码 / 黑色',
        priceText: '599.00',
        qtyText: '1',
        totalText: '599.00',
        actionText: '评价晒单',
        showCancel: false
      },
      {
        id: 'o004',
        shopName: '小林数码',
        statusText: '已取消',
        statusClass: 'status-muted',
        coverText: '商品图',
        goodsTitle: '蓝牙耳机 Pro · 主动降噪',
        specText: '白色',
        priceText: '499.00',
        qtyText: '1',
        totalText: '499.00',
        actionText: '再次购买',
        showCancel: false
      }
    ]
  },

  onTabTap(e) {
    this.setData({ currentTab: e.currentTarget.dataset.key });
  },

  onCancelTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确认取消订单 ' + id + ' ?',
      confirmText: '确认取消',
      cancelText: '再想想',
      success: () => {
        wx.showToast({ title: '订单已取消', icon: 'success' });
      }
    });
  },

  onTrackTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '查看 ' + id + ' 物流', icon: 'none' });
  },

  onActionTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '处理订单 ' + id, icon: 'none' });
  }
});
