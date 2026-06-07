Page({
  data: {
    // 状态管理
    activeCategory: 'all',
    cartCount: 0,
    totalAmount: 0,
    isLoading: false,
    swiperCurrent: 0,

    // 店铺基础信息 (嵌套对象)
    shopInfo: {
      name: 'Aura Coffee 极光咖啡',
      slogan: '匠心萃取，定义纯粹的味觉美学',
      rating: '4.9',
      deliveryTime: '20-30 min',
      address: '上海市静安区梧桐路 88 号'
    },

    // 轮播图数据
    banners: [
      {
        id: 'b1',
        image: 'https://images.unsplash.com/photo-1497515114629-f71d768fd07c?w=375&q=80',
        title: '冬日限定 · 桂花拿铁',
        subTitle: '捕捉秋末的最后一抹香甜'
      },
      {
        id: 'b2',
        image: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=375&q=80',
        title: '埃塞俄比亚 · 耶加雪菲',
        subTitle: '花香与柑橘的完美交织'
      },
      {
        id: 'b3',
        image: 'https://images.unsplash.com/photo-1497636577773-f1231844b336?w=375&q=80',
        title: '会员专享 · 升级计划',
        subTitle: '加入 Aura Club 享受 8 折权益'
      }
    ],

    // 分类数据
    categories: [
      { id: 'all', name: '全部' },
      { id: 'espresso', name: '意式经典' },
      { id: 'handbrew', name: '精品手冲' },
      { id: 'coldbrew', name: '冷萃系列' },
      { id: 'dessert', name: '精致甜点' },
      { id: 'beans', name: '咖啡豆' }
    ],

    // 商品列表数据
    products: [
      {
        id: 'p1',
        category: 'espresso',
        name: '海盐焦糖拿铁',
        desc: '顶层海盐奶盖搭配浓郁焦糖，咸甜交织',
        price: 32,
        priceText: '32.00',
        image: 'https://images.unsplash.com/photo-1481833761820-0509d3217039?w=375&q=80',
        qty: 0,
        tag: '人气推荐'
      },
      {
        id: 'p2',
        category: 'espresso',
        name: '经典美式咖啡',
        desc: '选用中深烘焙豆，纯正的咖啡原味',
        price: 26,
        priceText: '26.00',
        image: 'https://images.unsplash.com/photo-1498804103079-a6351b050096?w=375&q=80',
        qty: 0,
        tag: ''
      },
      {
        id: 'p3',
        category: 'handbrew',
        name: '瑰夏- Panama Geisha',
        desc: '极致的茉莉花香与柠檬酸度，顶级之选',
        price: 88,
        priceText: '88.00',
        image: 'https://images.unsplash.com/photo-1497515114629-f71d768fd07c?w=375&q=80',
        qty: 0,
        tag: '限量'
      },
      {
        id: 'p4',
        category: 'coldbrew',
        name: '柑橘冷萃咖啡',
        desc: '12小时低温慢萃，清爽如晨露',
        price: 38,
        priceText: '38.00',
        image: 'https://images.unsplash.com/photo-1495774856032-8b90bbb32b32?w=375&q=80',
        qty: 0,
        tag: '清爽'
      },
      {
        id: 'p5',
        category: 'dessert',
        name: '巴斯克焦糖芝士蛋糕',
        desc: '外焦里嫩，浓郁奶香在舌尖化开',
        price: 42,
        priceText: '42.00',
        image: 'https://images.unsplash.com/photo-1559305616-3f99cd43e353?w=375&q=80',
        qty: 0,
        tag: '甜点之王'
      },
      {
        id: 'p6',
        category: 'espresso',
        name: '燕麦拿铁',
        desc: '植物基燕麦奶，健康低脂，口感丝滑',
        price: 35,
        priceText: '35.00',
        image: 'https://images.unsplash.com/photo-1442550528053-c431ecb55509?w=375&q=80',
        qty: 0,
        tag: '健康'
      }
    ]
  },

  // 切换分类
  onCategoryTap(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ activeCategory: id });
  },

  // 数量增加
  addQty(e) {
    const id = e.currentTarget.dataset.id;
    const products = this.data.products;
    const index = products.findIndex(p => p.id === id);
    
    products[index].qty += 1;
    this.calculateTotal();
    this.setData({ products });
  },

  // 数量减少
  minusQty(e) {
    const id = e.currentTarget.dataset.id;
    const products = this.data.products;
    const index = products.findIndex(p => p.id === id);
    
    if (products[index].qty > 0) {
      products[index].qty -= 1;
      this.calculateTotal();
      this.setData({ products });
    }
  },

  // 计算总价和数量
  calculateTotal() {
    let total = 0;
    let count = 0;
    this.data.products.forEach(p => {
      total += p.price * p.qty;
      count += p.qty;
    });
    this.setData({
      totalAmount: total,
      cartCount: count
    });
  },

  // 提交订单
  onSubmitOrder() {
    if (this.data.cartCount === 0) {
      wx.showToast({
        title: '请先选择咖啡',
        icon: 'none'
      });
      return;
    }
    
    wx.showLoading({ title: '订单处理中...' });
    setTimeout(() => {
      wx.hideLoading();
      wx.showModal({
        title: '下单成功',
        content: '您的咖啡正在精心制作中，请耐心等待。',
        showCancel: false,
        confirmText: '太棒了',
        success: () => {
          // 重置购物车
          const products = this.data.products.map(p => ({...p, qty: 0}));
          this.setData({
            products,
            cartCount: 0,
            totalAmount: 0
          });
        }
      });
    }, 1500);
  },

  // 轮播图切换
  onSwiperChange(e) {
    this.setData({ swiperCurrent: e.detail.current });
  }
});