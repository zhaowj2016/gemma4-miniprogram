Page({
  data: {
    // 状态管理
    currentBanner: 0,
    activeTab: 'all',
    cartCount: 5,
    isLoading: false,
    isFavorite: [],
    searchKeyword: '',

    // 品牌配置
    brandName: 'AURA COUTURE',
    brandSlogan: '定义极致优雅，定制专属风范',
    brandCity: '上海 · 静安',

    // 统计数据 (New)
    stats: [
      { label: '服务客户', value: '12,000+', icon: '👥', color: '#1a2b4c' },
      { label: '顶级工匠', value: '85+', icon: '✂️', color: '#c5a059' },
      { label: '面料甄选', value: '200+', icon: '🧵', color: '#1a2b4c' },
      { label: '品牌年限', value: '15年', icon: '⏳', color: '#c5a059' }
    ],

    // 轮播图数据 (Expanded)
    banners: [
      {
        id: 'b1',
        imageUrl: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=375&q=80',
        title: '春季高定系列',
        subtitle: '匠心手作，诠释现代极简主义',
        category: 'New Arrival',
        discount: '8.5折',
        endTime: '2023-12-31'
      },
      {
        id: 'b2',
        imageUrl: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=375&q=80',
        title: '私人形象顾问',
        subtitle: '1对1专业分析，重塑个人气质',
        category: 'Service',
        discount: '限时特惠',
        endTime: '2023-11-15'
      },
      {
        id: 'b3',
        imageUrl: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=375&q=80',
        title: '数字化衣橱管理',
        subtitle: '让每一件珍藏，都能在恰当时刻闪光',
        category: 'Tech',
        discount: '首单半价',
        endTime: '2023-12-01'
      },
      {
        id: 'b4',
        imageUrl: 'https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=375&q=80',
        title: '顶级面料甄选',
        subtitle: '来自全球顶级纺织工坊的纯粹触感',
        category: 'Material',
        discount: '尊享礼遇',
        endTime: '2023-12-20'
      },
      {
        id: 'b5',
        imageUrl: 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=375&q=80',
        title: '礼服定制服务',
        subtitle: '记录人生高光时刻的完美剪裁',
        category: 'Custom',
        discount: '预约立减',
        endTime: '2023-11-30'
      },
      {
        id: 'b6',
        imageUrl: 'https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=375&q=80',
        title: '冬日羊绒系列',
        subtitle: '温暖与尊贵在此刻完美交织',
        category: 'Winter',
        discount: '会员特供',
        endTime: '2024-01-10'
      }
    ],

    // 功能类目 (Expanded)
    categories: [
      { id: 'c1', name: '形象定制', icon: '✨', color: '#1a2b4c', desc: '全方位气质升级', order: 1 },
      { id: 'c2', name: '手工量体', icon: '📏', color: '#c5a059', desc: '精准到毫米的剪裁', order: 2 },
      { id: 'c3', name: '衣橱管理', icon: '👗', color: '#1a2b4c', desc: '数字化穿搭方案', order: 3 },
      { id: 'c4', name: '奢侈护理', icon: '💎', color: '#c5a059', desc: '还原面料最初光泽', order: 4 },
      { id: 'c5', name: '趋势咨询', icon: '📅', color: '#1a2b4c', desc: '全球时尚前瞻', order: 5 },
      { id: 'c6', name: '会员特权', icon: '👑', color: '#c5a059', desc: '至尊等级专属礼遇', order: 6 },
      { id: 'c7', name: '面料预约', icon: '🧵', color: '#1a2b4c', desc: '全球稀缺面料预订', order: 7 },
      { id: 'c8', name: '礼品定制', icon: '🎁', color: '#c5a059', desc: '传递至高礼遇之情', order: 8 }
    ],

    // 核心服务卡片 (Expanded)
    services: [
      {
        id: 's1',
        title: '全维度形象诊断',
        desc: '由资深形象专家通过体型、肤色及气质分析，制定年度穿搭方案。',
        price: '2,999',
        tag: '热门',
        image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=375&q=80',
        duration: '120min',
        rating: 4.9,
        sales: 1200,
        city: '上海',
        expert: 'Sophia'
      },
      {
        id: 's2',
        title: '顶级西装手工量体',
        desc: '采用萨维尔街传统工艺，32项精准测量，打造第二层皮肤。',
        price: '8,800',
        tag: '经典',
        image: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=375&q=80',
        duration: '90min',
        rating: 5.0,
        sales: 850,
        city: '北京',
        expert: 'Master Julian'
      },
      {
        id: 's3',
        title: '数字化衣橱升级',
        desc: '专业团队上门整理，数字化录入所有单品，智能生成搭配建议。',
        price: '4,500',
        tag: '高效',
        image: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=375&q=80',
        duration: '180min',
        rating: 4.8,
        sales: 430,
        city: '上海',
        expert: 'Elena'
      },
      {
        id: 's4',
        title: '高级面料定制方案',
        desc: '全球甄选 Loro Piana, Scabal 等顶级面料，定制专属质感。',
        price: '12,000',
        tag: '奢华',
        image: 'https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=375&q=80',
        duration: '60min',
        rating: 4.9,
        sales: 210,
        city: '广州',
        expert: 'Marco'
      },
      {
        id: 's5',
        title: '奢侈品衣物深度护理',
        desc: '针对真丝、羊绒等娇贵面料的专业洗护，还原面料最初光泽。',
        price: '888',
        tag: '专业',
        image: 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=375&q=80',
        duration: '3-5天',
        rating: 4.7,
        sales: 3100,
        city: '全国',
        expert: 'CareTeam'
      },
      {
        id: 's6',
        title: '季节性趋势私人报告',
        desc: '基于当前全球时尚趋势，为您定制下个季度的采购建议清单。',
        price: '1,200',
        tag: '前卫',
        image: 'https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=375&q=80',
        duration: '60min',
        rating: 4.6,
        sales: 670,
        city: '上海',
        expert: 'Chloe'
      },
      {
        id: 's7',
        title: '至尊礼服定制礼包',
        desc: '包含量体、面料挑选、三次试衣及终身维护服务。',
        price: '25,000',
        tag: '至尊',
        image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=375&q=80',
        duration: '120min',
        rating: 5.0,
        sales: 120,
        city: '北京',
        expert: 'Julian'
      },
      {
        id: 's8',
        title: '商务社交形象升级',
        desc: '针对高管阶层，打造具有权威感与亲和力的职场形象。',
        price: '5,600',
        tag: '职场',
        image: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=375&q=80',
        duration: '150min',
        rating: 4.8,
        sales: 940,
        city: '上海',
        expert: 'Victoria'
      }
    ],

    // 精英会员 (Expanded)
    members: [
      { name: '陈女士', level: '黑金会员', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&q=80', city: '上海', joinDate: '2021-05', points: 15600 },
      { name: '李先生', level: '至尊会员', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&q=80', city: '北京', joinDate: '2020-11', points: 28400 },
      { name: '张女士', level: '金钻会员', avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&q=80', city: '深圳', joinDate: '2022-02', points: 8900 },
      { name: '王先生', level: '黑金会员', avatar: 'https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=100&q=80', city: '杭州', joinDate: '2021-08', points: 12300 },
      { name: '赵女士', level: '至尊会员', avatar: 'https://images.unsplash.com/photo-1520813792240-56fc4a3765a7?w=100&q=80', city: '上海', joinDate: '2019-03', points: 45000 },
      { name: '孙先生', level: '金钻会员', avatar: 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=100&q=80', city: '成都', joinDate: '2022-06', points: 7200 },
      { name: '周女士', level: '黑金会员', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&q=80', city: '广州', joinDate: '2021-12', points: 11000 },
      { name: '吴先生', level: '至尊会员', avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&q=80', city: '上海', joinDate: '2020-01', points: 33000 }
    ],

    // 推荐套餐 (New)
    recommendations: [
      {
        id: 'r1',
        title: '年度形象管理套餐',
        items: '诊断 + 3次定制 + 数字化管理',
        price: '19,999',
        originalPrice: '25,000',
        image: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=375&q=80',
        tag: '超值'
      },
      {
        id: 'r2',
        title: '职场精英起步礼包',
        items: '量体 + 2件商务衬衫 + 形象咨询',
        price: '6,800',
        originalPrice: '8,500',
        image: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=375&q=80',
        tag: '推荐'
      },
      {
        id: 'r3',
        title: '奢华面料体验礼盒',
        items: '面料采样 + 1次定制服务 + 护理券',
        price: '3,200',
        originalPrice: '4,000',
        image: 'https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=375&q=80',
        tag: '稀缺'
      },
      {
        id: 'r4',
        title: '至尊年度私享计划',
        items: '全年度不限次咨询 + 5件高定',
        price: '88,000',
        originalPrice: '100,000',
        image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=375&q=80',
        tag: '顶奢'
      },
      {
        id: 'r5',
        title: '季节焕新护理套餐',
        items: '10件奢侈品深层洗护 + 整理',
        price: '4,500',
        originalPrice: '6,000',
        image: 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=375&q=80',
        tag: '实用'
      },
      {
        id: 'r6',
        title: '礼服定制专项计划',
        items: '设计草图 + 3次试衣 + 礼服一件',
        price: '15,000',
        originalPrice: '18,000',
        image: 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=375&q=80',
        tag: '浪漫'
      }
    ]
  },

  // 轮播图切换
  onSwiperChange(e) {
    this.setData({ currentBanner: e.detail.current });
  },

  // 类目切换
  onCategoryTap(e) {
    const { id } = e.currentTarget.dataset;
    this.setData({ activeTab: id });
    wx.showToast({ title: '正在为您筛选...', icon: 'none' });
  },

  // 收藏逻辑
  toggleFavorite(e) {
    const { id } = e.currentTarget.dataset;
    let favs = this.data.isFavorite;
    const index = favs.indexOf(id);
    if (index > -1) {
      favs.splice(index, 1);
    } else {
      favs.push(id);
    }
    this.setData({ isFavorite: favs });
  },

  // 预约服务
  onBookService(e) {
    const { title } = e.currentTarget.dataset;
    wx.showModal({
      title: '预约确认',
      content: `您即将预约 [${title}]，是否进入时间选择界面？`,
      confirmColor: '#c5a059',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '加载日历...' });
          setTimeout(() => {
            wx.hideLoading();
            wx.showToast({ title: '跳转预约日历', icon: 'none' });
          }, 800);
        }
      }
    });
  },

  // 底部主操作
  onMainAction(e) {
    const { action } = e.currentTarget.dataset;
    if (action === 'cart') {
      wx.showToast({ title: `您有 ${this.data.cartCount} 项预约待确认`, icon: 'none' });
    } else if (action === 'profile') {
      wx.showToast({ title: '进入个人中心', icon: 'none' });
    } else if (action === 'search') {
      wx.showToast({ title: '激活搜索功能', icon: 'none' });
    }
  },

  // 搜索输入
  onSearchInput(e) {
    this.setData({ searchKeyword: e.detail.value });
  }
});