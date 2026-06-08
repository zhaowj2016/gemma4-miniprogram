Page({
  data: {
    avatarText: '云',
    userName: '云中客',
    userIdText: 'gemma_884210',
    levelText: 'VIP 3 会员',
    followCountText: '128',
    fansCountText: '2.4k',
    likeCountText: '6.8w',
    collectCountText: '342',
    orderTypes: [
      { key: 'pay', name: '待付款', iconText: '付', badgeText: '2' },
      { key: 'ship', name: '待发货', iconText: '发', badgeText: '' },
      { key: 'receive', name: '待收货', iconText: '收', badgeText: '5' },
      { key: 'review', name: '待评价', iconText: '评', badgeText: '' },
      { key: 'service', name: '售后', iconText: '退', badgeText: '' }
    ],
    menuList: [
      { key: 'coupon', name: '我的优惠券', iconText: '券', extraText: '6 张' },
      { key: 'address', name: '收货地址', iconText: '地', extraText: '' },
      { key: 'wallet', name: '我的钱包', iconText: '钱', extraText: '¥328.50' },
      { key: 'fav', name: '我的收藏', iconText: '心', extraText: '' },
      { key: 'history', name: '浏览历史', iconText: '历', extraText: '' },
      { key: 'service', name: '在线客服', iconText: '客', extraText: '' },
      { key: 'feedback', name: '意见反馈', iconText: '意', extraText: '' },
      { key: 'setting', name: '设置', iconText: '设', extraText: '' }
    ]
  },

  onEditTap() {
    wx.showToast({ title: '编辑个人资料', icon: 'none' });
  },

  onStatTap(e) {
    const key = e.currentTarget.dataset.key;
    wx.showToast({ title: '查看 ' + key, icon: 'none' });
  },

  onOrderEntryTap() {
    wx.showToast({ title: '查看全部订单', icon: 'none' });
  },

  onOrderTypeTap(e) {
    const key = e.currentTarget.dataset.key;
    wx.showToast({ title: '查看 ' + key + ' 订单', icon: 'none' });
  },

  onMenuTap(e) {
    const key = e.currentTarget.dataset.key;
    wx.showToast({ title: '打开 ' + key, icon: 'none' });
  }
});
