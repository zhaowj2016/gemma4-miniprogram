Page({
  data: {
    // 状态管理
    activeTab: 'tasting', // 'tasting' (主厨精选) 或 'alacarte' (单点菜单)
    cartCount: 0,
    totalPrice: 0,
    isLoading: false,
    currentBannerIndex: 0,

    // 顶部轮播图 - 匹配高档餐厅视觉 (参考图片中的对比度与构图)
    banners: [
      {
        url: 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=375&q=80',
        title: '星级主厨之作',
        desc: '探索味蕾的极致艺术'
      },
      {
        url: 'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=375&q=80',
        title: '季节限定菜单',
        desc: '旬之味，自然之礼'
      },
      {
        url: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=375&q=80',
        title: '顶级食材甄选',
        desc: '全球寻觅，匠心呈现'
      }
    ],

    // 实时播报活动
    broadcasts: [
      '【预约提醒】本周五主厨特别晚宴仅余 2 位',
      '【季节限定】黑松露系列菜单现已开启预订',
      '【会员礼遇】米其林三星会员可享专属侍酒师服务',
      '【新店动态】我们的新酒窖已正式开放参观'
    ],
    currentBroadcastIndex: 0,

    // 菜单数据
    menu: {
      tasting: [
        {
          id: 't1',
          name: '极境 · 赏味套餐',
          desc: '包含 9 道精选佳肴，由主厨根据当日新鲜食材定制',
          price: 2880,
          image: 'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=375&q=80',
          tags: ['主厨推荐', '极致体验'],
          qty: 0
        },
        {
          id: 't2',
          name: '晨曦 · 午后套餐',
          desc: '轻盈的味觉旅程，适合商务午餐与精致社交',
          price: 1280,
          image: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=375&q=80',
          tags: ['优雅', '轻盈'],
          qty: 0
        },
        {
          id: 't3',
          name: '深海 · 探秘菜单',
          desc: '聚焦全球顶奢海产，呈现海洋的纯净与深邃',
          price: 2180,
          image: 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=375&q=80',
          tags: ['海鲜', '限定'],
          qty: 0
        },
        {
          id: 't4',
          name: '大地 · 颂歌套餐',
          desc: '顶级和牛与时令菌类，演绎大地的丰饶',
          price: 1880,
          image: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=375&q=80',
          tags: ['和牛', '经典'],
          qty: 0
        }
      ],
      alacarte: [
        {
          id: 'a1',
          name: '奥西特拉鲟鱼子酱',
          desc: '搭配传统配料与手工脆饼，纯正咸鲜',
          price: 880,
          image: 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=375&q=80',
          tags: ['前菜'],
          qty: 0
        },
        {
          id: 'a2',
          name: 'A5级极致和牛 M9+',
          desc: '低温慢煮后高温炙烤，入口即化',
          price: 1280,
          image: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=375&q=80',
          tags: ['主菜'],
          qty: 0
        },
        {
          id: 'a3',
          name: '蓝龙虾配柠檬黄油',
          desc: '捕获自布列塔尼海域，鲜甜弹牙',
          price: 980,
          image: 'https://images.unsplash.com/photo-1553621042-f6e147245754?w=375&q=80',
          tags: ['主菜'],
          qty: 0
        },
        {
          id: 'a4',
          name: '金箔巧克力球',
          desc: '70% 纯黑巧克力搭配 24K 食用金箔',
          price: 320,
          image: 'https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=375&q=80',
          tags: ['甜点'],
          qty: 0
        },
        {
          id: 'a5',
          name: '黑松露慢炖烩饭',
          desc: '顶级佩里戈尔黑松露，浓郁奶香',
          price: 680,
          image: 'https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=375&q=80',
          tags: ['经典'],
          qty: 0
        }
      ]
    }
  },

  onLoad() {
    // 启动播报轮播
    setInterval(() => {
      const nextIndex = (this.data.currentBroadcastIndex + 1) % this.data.broadcasts.length;
      this.setData({ currentBroadcastIndex: nextIndex });
    }, 4000);
  },

  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  onPlus(e) {
    const id = e.currentTarget.dataset.id;
    const category = this.data.activeTab;
    const list = this.data.menu[category].map(item => {
      if (item.id === id) {
        return { ...item, qty: item.qty + 1 };
      }
      return item;
    });
    this.updateCart(category, list);
  },

  onMinus(e) {
    const id = e.currentTarget.dataset.id;
    const category = this.data.activeTab;
    const list = this.data.menu[category].map(item => {
      if (item.id === id && item.qty > 0) {
        return { ...item, qty: item.qty - 1 };
      }
      return item;
    });
    this.updateCart(category, list);
  },

  updateCart(category, newList) {
    const updatedMenu = { ...this.data.menu, [category]: newList };
    
    // 计算总数和总价
    let totalQty = 0;
    let totalPrice = 0;
    
    Object.values(updatedMenu).forEach(catList => {
      catList.forEach(item => {
        totalQty += item.qty;
        totalPrice += item.qty * item.price;
      });
    });

    this.setData({
      menu: updatedMenu,
      cartCount: totalQty,
      totalPrice: totalPrice
    });
  },

  onSwiperChange(e) {
    this.setData({ currentBannerIndex: e.detail.current });
  },

  onCheckout() {
    if (this.data.cartCount === 0) {
      wx.showToast({ title: '请先选择佳肴', icon: 'none' });
      return;
    }
    wx.showLoading({ title: '正在预约席位...' });
    setTimeout(() => {
      wx.hideLoading();
      wx.showToast({ title: '预约成功', icon: 'success' });
    }, 1500);
  }
});