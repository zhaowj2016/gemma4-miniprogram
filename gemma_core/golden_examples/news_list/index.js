Page({
  data: {
    channelName: '科技资讯',
    updateTimeText: '08:30',
    currentTab: 'all',
    tabs: [
      { key: 'all', name: '全部', countText: '' },
      { key: 'ai', name: 'AI', countText: '128' },
      { key: 'mobile', name: '移动', countText: '64' },
      { key: 'cloud', name: '云服务', countText: '42' },
      { key: 'startup', name: '创业', countText: '37' }
    ],
    featured: {
      coverText: '头条封面',
      tagText: '深度',
      title: '国产大模型密集上新: 多模态能力集体跃迁, 行业落地进入下半场',
      sourceText: '科技日报',
      timeText: '12 分钟前',
      viewCountText: '8.6万'
    },
    articles: [
      {
        id: 'a001',
        title: 'iOS 19 预览版发布, 重点优化 AI 助手与系统级搜索',
        summaryText: '苹果在 WWDC 上公布多项系统级 AI 能力, 涉及照片, 备忘录, 邮件等核心应用。',
        sourceText: '极客公园',
        timeText: '1 小时前',
        viewCountText: '3.2万',
        coverText: '配图一'
      },
      {
        id: 'a002',
        title: 'Meta 推出新一代开源大模型, 性能逼近闭源旗舰',
        summaryText: '在多个公开榜单上, 新模型与 GPT-5 系列持平, 训练成本下降 40%。',
        sourceText: '机器之心',
        timeText: '2 小时前',
        viewCountText: '1.8万',
        coverText: '配图二'
      },
      {
        id: 'a003',
        title: '国内云厂商集体降价, 中小企业上云成本进一步压缩',
        summaryText: '阿里云, 腾讯云, 火山引擎相继发布新一季优惠策略。',
        sourceText: '财经早知道',
        timeText: '今天 07:30',
        viewCountText: '5.4千',
        coverText: '配图三'
      },
      {
        id: 'a004',
        title: '小米汽车 5 月交付破 3 万, 新势力格局再生变数',
        summaryText: 'Y 系列首月交付即过万, 成为现象级产品。',
        sourceText: '汽车之家',
        timeText: '昨天',
        viewCountText: '12.6万',
        coverText: ''
      }
    ]
  },

  onTabTap(e) {
    this.setData({ currentTab: e.currentTarget.dataset.key });
  },

  onFeaturedTap() {
    wx.showToast({ title: '打开头条文章', icon: 'none' });
  },

  onArticleTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '打开文章 ' + id, icon: 'none' });
  }
});
