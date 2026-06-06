Page({
  data: {
    title: '选择适合你的方案',
    subtitleText: '所有方案均支持 7 天无理由退款',
    billing: 'month',
    plans: [
      {
        id: 'p1',
        name: '免费版',
        descText: '适合个人尝鲜体验',
        priceText: '0',
        originalText: '',
        cycleText: '永久免费',
        recommended: false,
        recommendedText: '',
        btnText: '当前方案',
        features: [
          '基础 5 个项目管理',
          '社区标准模板',
          '1 GB 云存储空间'
        ]
      },
      {
        id: 'p2',
        name: '专业版',
        descText: '中小团队首选',
        priceText: '99',
        originalText: '129',
        cycleText: '月',
        recommended: true,
        recommendedText: '最受欢迎',
        btnText: '立即升级',
        features: [
          '不限数量项目协作',
          '高级数据看板与导出',
          '50 GB 团队存储空间',
          '工作日 8 小时在线客服',
          '10 人团队席位'
        ]
      },
      {
        id: 'p3',
        name: '企业版',
        descText: '为大型组织量身定制',
        priceText: '399',
        originalText: '499',
        cycleText: '月',
        recommended: false,
        recommendedText: '',
        btnText: '联系销售',
        features: [
          '包含专业版全部能力',
          'SSO 单点登录与审计日志',
          '专属客户成功经理',
          '无限团队席位',
          '99.9% SLA 在线保障'
        ]
      }
    ],
    faqs: [
      {
        id: 'f1',
        q: '升级后可以退款吗?',
        a: '购买后 7 天内未使用任何付费功能, 可在设置页一键申请退款, 款项原路返回。'
      },
      {
        id: 'f2',
        q: '团队成员需要单独付费吗?',
        a: '专业版包含 10 个席位, 企业版不限席位。所有成员均可使用同一套餐内全部功能。'
      },
      {
        id: 'f3',
        q: '是否支持开具发票?',
        a: '支持开具增值税普通发票与专用发票, 可在账户管理中填写开票资料, 3 个工作日内寄出。'
      }
    ]
  },

  onToggleTap(e) {
    this.setData({ billing: e.currentTarget.dataset.mode });
  },

  onChooseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '已选择套餐 ' + id, icon: 'success' });
  }
});
