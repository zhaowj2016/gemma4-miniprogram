Page({
  data: {
    restaurantName: '山隐茶事 · 静安店',
    ratingText: '4.8',
    monthlySalesText: '2,386',
    avgPriceText: '88.00',
    currentCategory: 'tea',
    currentCategoryBanner: '茶饮主理, 一壶一冲',
    categories: [
      { key: 'tea', name: '招牌茶' },
      { key: 'snack', name: '茶点' },
      { key: 'set', name: '套餐' },
      { key: 'dessert', name: '甜品' },
      { key: 'gift', name: '伴手礼' }
    ],
    dishes: [
      {
        id: 'd001',
        coverText: '菜品图',
        name: '明前龙井 · 单泡',
        descText: '头采 50g, 玻璃杯现冲, 茶汤清亮豆香足。',
        tags: ['招牌', '现冲'],
        priceText: '38.00',
        originalText: '',
        qty: 0,
        qtyText: '0'
      },
      {
        id: 'd002',
        coverText: '菜品图',
        name: '凤凰单丛 · 鸭屎香',
        descText: '广东潮州凤凰山头春茶, 蜜兰香, 回甘悠长。',
        tags: ['热门'],
        priceText: '48.00',
        originalText: '',
        qty: 0,
        qtyText: '0'
      },
      {
        id: 'd003',
        coverText: '菜品图',
        name: '桂花乌龙冷泡',
        descText: '12 小时冷泡萃取, 夏日清爽首选。',
        tags: ['夏日'],
        priceText: '28.00',
        originalText: '',
        qty: 0,
        qtyText: '0'
      },
      {
        id: 'd004',
        coverText: '菜品图',
        name: '古法蛋黄酥',
        descText: '酥皮千层, 蛋黄流心, 配茶绝配。',
        tags: ['手工', '当日现做'],
        priceText: '18.00',
        originalText: '22.00',
        qty: 0,
        qtyText: '0'
      }
    ],
    totalQtyText: '0',
    totalAmountText: '0.00'
  },

  onCategoryTap(e) {
    const key = e.currentTarget.dataset.key;
    const nameMap = {
      tea: '茶饮主理, 一壶一冲',
      snack: '手工茶点, 现烤现做',
      set: '精选套餐, 高性价比',
      dessert: '甜品限定, 季节上新',
      gift: '伴手好礼, 体面有面'
    };
    this.setData({
      currentCategory: key,
      currentCategoryBanner: nameMap[key] || ''
    });
  },

  onPlusTap(e) {
    const id = e.currentTarget.dataset.id;
    const list = this.data.dishes.map((d) => {
      if (d.id === id) {
        const next = d.qty + 1;
        return Object.assign({}, d, { qty: next, qtyText: String(next) });
      }
      return d;
    });
    this.recalcCart(list);
  },

  onMinusTap(e) {
    const id = e.currentTarget.dataset.id;
    const list = this.data.dishes.map((d) => {
      if (d.id === id && d.qty > 0) {
        const next = d.qty - 1;
        return Object.assign({}, d, { qty: next, qtyText: String(next) });
      }
      return d;
    });
    this.recalcCart(list);
  },

  recalcCart(list) {
    let total = 0;
    let amount = 0;
    list.forEach((d) => {
      total += d.qty;
      amount += d.qty * parseFloat(d.priceText);
    });
    this.setData({
      dishes: list,
      totalQtyText: String(total),
      totalAmountText: amount.toFixed(2)
    });
  },

  onCartTap() {
    wx.showToast({ title: '查看购物车', icon: 'none' });
  },

  onCheckoutTap() {
    if (parseInt(this.data.totalQtyText, 10) === 0) {
      wx.showToast({ title: '请先点菜', icon: 'none' });
      return;
    }
    wx.showToast({ title: '去结算', icon: 'success' });
  }
});
