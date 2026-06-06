Page({
  data: {
    // 状态管理
    activeTab: 'gallery', // gallery, ai_services, booking
    currentSwiper: 0,
    isLoading: false,
    cartCount: 2,
    isLiked: {}, // 存储每个项目的点赞状态 {id: true/false}

    // 用户信息
    userProfile: {
      name: 'AI 婚礼美学工作室',
      tagline: '用科技定义永恒浪漫',
      rating: '4.9',
      experience: '8年'
    },

    // 顶部轮播图
    banners: [
      {
        id: 1,
        url: 'https://images.unsplash.com/photo-1519741497674-611481863552?w=375&q=80',
        title: '光影之约',
        desc: 'AI 驱动的电影级光影重构'
      },
      {
        id: 2,
        url: 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=375&q=80',
        title: '数字永恒',
        desc: '将瞬间转化为永恒的艺术资产'
      },
      {
        id: 3,
        url: 'https://images.unsplash.com/photo-1465495910483-fb6667a23f7d?w=375&q=80',
        title: '未来婚礼',
        desc: '虚拟场景定制与智能构图'
      },
      {
        id: 4,
        url: 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=375&q=80',
        title: '情绪捕捉',
        desc: '深度学习技术精准还原情感'
      }
    ],

    // 核心AI服务卡片
    aiServices: [
      {
        id: 's1',
        title: 'AI 氛围重塑',
        desc: '一键将照片转换为赛博朋克、油画或极简主义风格',
        icon: '✨',
        price: '¥199',
        tag: '最热门'
      },
      {
        id: 's2',
        title: '智能场景迁移',
        desc: '无需实地拍摄，将背景迁移至全球顶尖婚礼场地',
        icon: '🌍',
        price: '¥399',
        tag: '黑科技'
      },
      {
        id: 's3',
        title: '面部情感优化',
        desc: '利用AI微调表情，捕捉最自然的笑容与深情',
        icon: '💖',
        price: '¥299',
        tag: '精细化'
      },
      {
        id: 's4',
        title: '全自动相册编排',
        desc: '基于故事线的智能选图与排版，生成数字画册',
        icon: '📖',
        price: '¥599',
        tag: '高效'
      },
      {
        id: 's5',
        title: '虚拟光影增强',
        desc: '模拟黄金小时光线，为婚礼照片注入神圣感',
        icon: '☀️',
        price: '¥199',
        tag: '光影'
      },
      {
        id: 's6',
        title: 'AI 穿搭模拟',
        desc: '提前预览不同礼服在实际场景中的视觉效果',
        icon: '👗',
        price: '¥499',
        tag: '定制'
      }
    ],

    // 摄影套餐
    packages: [
      {
        id: 'p1',
        name: '极简数字包',
        price: '1,999',
        features: ['AI 基础精修 50 张', '单场景数字迁移', '电子画册 1 册'],
        recommended: false
      },
      {
        id: 'p2',
        name: '至臻光影包',
        price: '4,999',
        features: ['AI 全量精修 200 张', '多场景虚拟增强', '实体高级画册', '1对1 风格定制'],
        recommended: true
      },
      {
        id: 'p3',
        name: '未来艺术包',
        price: '9,999',
        features: ['全流程 AI 数字化管理', '全球虚拟场景定制', '电影级短片制作', '终身云端存储'],
        recommended: false
      }
    ],

    // 作品集数据
    gallery: [
      { id: 101, url: 'https://images.unsplash.com/photo-1532712938310-34cb3982ef74?w=375&q=80', title: '晨曦之吻' },
      { id: 102, url: 'https://images.unsplash.com/photo-1583939003579-730e3918a45a?w=375&q=80', title: '夜色誓言' },
      { id: 103, url: 'https://images.unsplash.com/photo-1515934751635-c81c6bc9aee2?w=375&q=80', title: '纯白礼赞' },
      { id: 104, url: 'https://images.unsplash.com/photo-1544078751-556558567531?w=375&q=80', title: '林间之梦' },
      { id: 105, url: 'https://images.unsplash.com/photo-1522673607200-1648832cee75?w=375&q=80', title: '永恒瞬间' },
      { id: 106, url: 'https://images.unsplash.com/photo-1519741497674-611481863552?w=375&q=80', title: '光影交织' }
    ]
  },

  // 切换 Tab
  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  // 轮播图切换
  onSwiperChange(e) {
    this.setData({ currentSwiper: e.detail.current });
  },

  // 点赞逻辑
  onLikeTap(e) {
    const id = e.currentTarget.dataset.id;
    const currentStatus = this.data.isLiked[id] || false;
    this.setData({
      [`isLiked.${id}`]: !currentStatus
    });
  },

  // 服务选择
  onServiceSelect(e) {
    const service = e.currentTarget.dataset.service;
    wx.showToast({
      title: '已选择' + service.title,
      icon: 'none'
    });
  },

  // 套餐预约
  onBookPackage(e) {
    const pkgName = e.currentTarget.dataset.name;
    wx.showModal({
      title: '确认预约',
      content: '您确定要预约 ' + pkgName + ' 吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showToast({ title: '预约成功', icon: 'success' });
        }
      }
    });
  }
});