Page({
  data: {
    title: '领券中心',
    updateTimeText: '00:00',
    coupons: [
      {
        id: 'c001',
        amountText: '50',
        conditionText: '满 300 可用',
        name: '全场通用券',
        scopeText: '适用于全品类商品',
        expireText: '2026-07-30',
        status: 'available'
      },
      {
        id: 'c002',
        amountText: '120',
        conditionText: '满 500 可用',
        name: '茶饮品类专享',
        scopeText: '仅限茶饮, 茶具, 茶点类商品',
        expireText: '2026-06-30',
        status: 'available'
      },
      {
        id: 'c003',
        amountText: '20',
        conditionText: '满 99 可用',
        name: '新人首单券',
        scopeText: '适用于店铺全部商品',
        expireText: '2026-06-15',
        status: 'claimed'
      },
      {
        id: 'c004',
        amountText: '200',
        conditionText: '满 1000 可用',
        name: '高客单尊享',
        scopeText: '适用于家电, 数码 3C 类目',
        expireText: '2026-08-30',
        status: 'available'
      }
    ],
    rules: [
      '1. 每张优惠券仅限领取一次, 领取后请在有效期内使用',
      '2. 优惠券不与其他优惠同享, 结算时系统自动选取最优组合',
      '3. 使用优惠券的订单发生退款时, 券将原路退回账户',
      '4. 平台保留对活动的最终解释权'
    ]
  },

  onClaimTap(e) {
    const id = e.currentTarget.dataset.id;
    const list = this.data.coupons.map((c) => {
      if (c.id === id && c.status === 'available') {
        return Object.assign({}, c, { status: 'claimed' });
      }
      return c;
    });
    this.setData({ coupons: list });
    wx.showToast({ title: '领取成功', icon: 'success' });
  }
});
