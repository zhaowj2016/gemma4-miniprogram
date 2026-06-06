Page({
  data: {
    specialtyText: 'BRAND IDENTITY · 品牌视觉',
    designerName: '何子衿',
    taglineText: '专注新消费品牌的视觉系统建设, 9 年品牌全案经验, 服务过 50 + 头部新消费团队。',
    projectCountText: '60+',
    clientCountText: '50+',
    awardCountText: '12',
    currentCategory: 'all',
    categories: [
      { key: 'all', name: '全部' },
      { key: 'logo', name: 'Logo & VI' },
      { key: 'package', name: '包装' },
      { key: 'web', name: '网页' },
      { key: 'space', name: '空间' }
    ],
    works: [
      {
        id: 'w001',
        coverText: '主视觉',
        coverColor: 'linear-gradient(135deg, #ff9a9e, #fad0c4)',
        title: '半日闲茶饮 · 品牌升级',
        subText: 'Logo · 包装 · 门店',
        featured: true
      },
      {
        id: 'w002',
        coverText: '包装',
        coverColor: 'linear-gradient(135deg, #a8edea, #fed6e3)',
        title: '山隐 · 茶礼盒',
        subText: '包装设计',
        featured: false
      },
      {
        id: 'w003',
        coverText: '网页',
        coverColor: 'linear-gradient(135deg, #84fab0, #8fd3f4)',
        title: '云策科技官网',
        subText: '品牌官网',
        featured: false
      },
      {
        id: 'w004',
        coverText: '空间',
        coverColor: 'linear-gradient(135deg, #d299c2, #fef9d7)',
        title: '半日闲 · 杭州首店',
        subText: '空间导视',
        featured: false
      },
      {
        id: 'w005',
        coverText: 'Logo',
        coverColor: 'linear-gradient(135deg, #fbc2eb, #a6c1ee)',
        title: '原野户外 · 标志升级',
        subText: 'Logo & VI',
        featured: false
      }
    ],
    process: [
      {
        indexText: '01',
        name: '需求沟通',
        descText: '了解品牌现状, 业务目标, 预算与时间计划'
      },
      {
        indexText: '02',
        name: '策略梳理',
        descText: '竞品调研, 用户画像, 视觉策略输出'
      },
      {
        indexText: '03',
        name: '设计执行',
        descText: '概念提案, 视觉细化, 多轮评审'
      },
      {
        indexText: '04',
        name: '落地陪跑',
        descText: '物料监修, 媒体应用, 上线后跟踪'
      }
    ]
  },

  onCategoryTap(e) {
    this.setData({ currentCategory: e.currentTarget.dataset.key });
  },

  onWorkTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '打开作品 ' + id, icon: 'none' });
  },

  onMsgTap() {
    wx.showToast({ title: '打开私信', icon: 'none' });
  },

  onHireTap() {
    wx.showToast({ title: '发送合作邀请', icon: 'success' });
  }
});
