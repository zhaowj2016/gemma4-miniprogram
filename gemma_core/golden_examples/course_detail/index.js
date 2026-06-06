Page({
  data: {
    categoryText: '商业 / 领导力',
    courseName: '管理者必修课: 从业务骨干到团队 Leader',
    studentCountText: '2,386',
    ratingText: '4.9',
    priceText: '499.00',
    lessonCountText: '24',
    durationText: '8',
    introText: '本课程由资深组织发展专家主讲, 系统拆解从骨干员工到团队管理者的核心能力跃迁路径。课程包含 6 大模块, 24 节精讲, 配合真实管理案例与情景演练, 帮助学员在 8 周内完成思维模式与日常管理动作的双重升级。',
    learnPoints: [
      '建立系统性的管理思维框架, 跳出"业务高手"陷阱',
      '掌握 1 对 1 沟通, 团队复盘, 目标拆解等高频管理动作',
      '学会识别团队不同阶段的人才需求, 制定差异化培养方案',
      '获得可直接套用的 20+ 管理工具模板与话术'
    ],
    outline: [
      {
        indexText: '01',
        title: '管理者角色认知',
        descText: '从交付者到赋能者的三大思维转变'
      },
      {
        indexText: '02',
        title: '目标与计划管理',
        descText: 'OKR 拆解, 节奏管理, 团队周会设计'
      },
      {
        indexText: '03',
        title: '团队沟通与反馈',
        descText: 'GROW 模型, 非暴力沟通, 复盘会议'
      },
      {
        indexText: '04',
        title: '人才识别与培养',
        descText: '9 宫格工具, IDP 个人发展计划制定'
      }
    ],
    teacher: {
      avatarText: '林',
      name: '林思涵',
      titleText: '前阿里 P9 组织发展专家',
      bioText: '15 年互联网大厂管理经验, 主导过 8 个 0 到 1 团队搭建, 多次获得集团优秀管理者称号。'
    },
    comments: [
      {
        id: 'c001',
        name: '张同学',
        ratingText: '5.0',
        text: '作为刚晋升的新经理, 这门课帮我理清了头绪, 模板直接能用。'
      },
      {
        id: 'c002',
        name: '王同学',
        ratingText: '4.8',
        text: '案例很真实, 老师讲得接地气, 不是空泛的理论。'
      }
    ],
    isFavorited: false
  },

  onFavTap() {
    this.setData({ isFavorited: !this.data.isFavorited });
    wx.showToast({
      title: this.data.isFavorited ? '已加入收藏' : '已取消收藏',
      icon: 'none'
    });
  },

  onEnrollTap() {
    wx.showToast({ title: '跳转到报名页', icon: 'none' });
  }
});
