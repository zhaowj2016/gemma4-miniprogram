Page({
  data: {
    heroEyebrow: 'SINCE 2014',
    heroTitle: '让数据驱动\n每一次业务增长',
    heroSubText: '我们提供从数据治理到智能分析的一站式企业服务, 已陪伴 200+ 行业客户完成数字化升级。',
    primaryBtnText: '了解产品',
    secondaryBtnText: '观看案例',
    servicesTitle: '从咨询到落地, 全链路陪伴',
    services: [
      {
        iconText: 'A',
        title: '数据中台',
        descText: '打通全渠道数据资产, 沉淀企业级指标体系'
      },
      {
        iconText: 'B',
        title: '智能分析',
        descText: 'AI 驱动的指标归因与业务洞察'
      },
      {
        iconText: 'C',
        title: '行业方案',
        descText: '零售 / 金融 / 制造等多行业最佳实践'
      },
      {
        iconText: 'D',
        title: '实施服务',
        descText: '驻场 + 远程, 7x24 响应式交付'
      }
    ],
    aboutTitle: '深耕行业 11 年',
    aboutText: '团队核心成员来自一线互联网公司与咨询机构, 累计交付 300+ 项目, 多次入选行业优秀案例库。我们相信数据是一切科学决策的起点。',
    stats: [
      { valueText: '300+', labelText: '交付项目' },
      { valueText: '200+', labelText: '服务客户' },
      { valueText: '11', labelText: '行业经验(年)' }
    ],
    clientsTitle: '他们选择了我们',
    clients: ['招商银行', '中信证券', '美的集团', '安踏体育', '永辉超市', '波司登'],
    ctaTitle: '准备好开始你的数据之旅了吗?',
    ctaSubText: '留下联系方式, 我们的顾问 1 个工作日内回复',
    brandShortName: '云策科技'
  },

  onPrimaryTap() {
    wx.showToast({ title: '跳转到产品介绍', icon: 'none' });
  },

  onSecondaryTap() {
    wx.showToast({ title: '播放案例视频', icon: 'none' });
  },

  onServiceTap(e) {
    const index = e.currentTarget.dataset.index;
    wx.showToast({ title: '查看服务 ' + (index + 1), icon: 'none' });
  },

  onContactTap() {
    wx.showToast({ title: '跳转到联系页面', icon: 'none' });
  }
});
