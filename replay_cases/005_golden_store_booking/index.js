// ============================================================
// 高级门店预约页 · 逻辑（MUSE 美学空间 · 高级造型沙龙）
// 全部数据为本地 mock；不调用任何联网 / 登录 / 支付 / 云函数等真实能力 API。
// 设计要点：
//   1. 服务 / 造型师 / 日期 / 时段 / 作品 / 会员卡等组块均可点选并有反馈。
//   2. 派生文案（summary / selectedSlotName / noteLen 等）在 JS 算好再 setData，
//      WXML 的 {{}} 内不写表达式方法调用。
//   3. 三类基础交互：switchTab（tab 切换）/ 手机号 input + 备注 textarea 绑定 /
//      onConfirm（校验 + wx.showToast）。
// ============================================================
Page({
  data: {
    scrolled: false,
    nav: { title: 'MUSE 美学空间' },

    activeTab: 'home',
    tabs: [
      { key: 'home', label: '首页', icon: 'home' },
      { key: 'service', label: '服务', icon: 'service' },
      { key: 'cases', label: '案例', icon: 'cases' },
      { key: 'mine', label: '我的', icon: 'mine' }
    ],

    // ① 门店主视觉
    heroCurrent: 0,
    heroImages: [
      { id: 1, src: 'https://images.unsplash.com/photo-1599387737838-626bf0d1f1f3?w=600&q=80' },
      { id: 2, src: 'https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?w=600&q=80' },
      { id: 3, src: 'https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=600&q=80' }
    ],
    store: {
      name: 'MUSE 美学空间',
      tagline: '预约制高级造型沙龙 · 一人一镜独立空间',
      statusText: '营业中 · 今日可约',
      rating: '4.96',
      avgPrice: '420',
      distance: '1.2km',
      hoursShort: '10–21',
      address: '上海市静安区南京西路 1788 号 晶采世纪大厦 18F'
    },

    // ③ 服务项目
    selectedService: 1,
    selectedServiceName: '已选「设计师剪发」',
    servicesPick: [
      { id: 1, name: '设计师剪发', desc: '一对一面诊 · 头型脸型定制方案', duration: '约 60 分钟', price: '288', hot: true, src: 'https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=600&q=80' },
      { id: 2, name: '植物养护染', desc: '低敏植物染膏 · 含护理与造型', duration: '约 150 分钟', price: '880', hot: false, src: 'https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=600&q=80' },
      { id: 3, name: '头皮深层 SPA', desc: '头皮检测 + 净化 + 头肩颈舒缓', duration: '约 90 分钟', price: '468', hot: true, src: 'https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600&q=80' }
    ],

    // ④ 造型师
    selectedStylist: 2,
    selectedStylistName: 'Vincent',
    stylists: [
      { id: 1, name: 'Aaron', title: '总监 · 12年', rating: '4.9', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80' },
      { id: 2, name: 'Vincent', title: '首席 · 9年', rating: '5.0', avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&q=80' },
      { id: 3, name: 'Mia', title: '色彩专家 · 7年', rating: '4.9', avatar: 'https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=600&q=80' },
      { id: 4, name: 'Leo', title: '高级造型 · 6年', rating: '4.8', avatar: 'https://images.unsplash.com/photo-1520813792240-56fc4a3765a7?w=600&q=80' }
    ],

    // ⑤ 日期
    selectedDate: 2,
    dates: [
      { id: 1, week: '今天', day: '6/08', few: false },
      { id: 2, week: '周一', day: '6/09', few: false },
      { id: 3, week: '周二', day: '6/10', few: true },
      { id: 4, week: '周三', day: '6/11', few: false },
      { id: 5, week: '周四', day: '6/12', few: false },
      { id: 6, week: '周五', day: '6/13', few: true }
    ],

    // ⑥ 时段
    selectedSlot: 3,
    selectedSlotName: '14:00',
    slots: [
      { id: 1, time: '10:30', full: false, tip: '可约' },
      { id: 2, time: '12:00', full: true, tip: '' },
      { id: 3, time: '14:00', full: false, tip: '可约' },
      { id: 4, time: '15:30', full: false, tip: '剩 1' },
      { id: 5, time: '17:00', full: true, tip: '' },
      { id: 6, time: '19:30', full: false, tip: '可约' }
    ],

    // ⑦ 表单
    form: { phone: '', note: '' },
    noteLen: 0,

    // ⑧ 门店环境
    galleryCount: 12,
    environment: [
      'https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=600&q=80',
      'https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600&q=80',
      'https://images.unsplash.com/photo-1522337660859-02fbefca4702?w=600&q=80',
      'https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=600&q=80'
    ],

    // ⑨ 评价
    reviews: [
      {
        id: 1, name: '是阿吱呀', service: '设计师剪发', stylist: 'Vincent',
        stars: [{ i: 1, on: true }, { i: 2, on: true }, { i: 3, on: true }, { i: 4, on: true }, { i: 5, on: true }],
        avatar: 'https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=600&q=80',
        text: 'Vincent 真的会沟通，面诊很久才下剪，剪完显脸小一圈。空间是独立卡座，全程没有被推销，很舒服。',
        hasImg: true,
        imgs: ['https://images.unsplash.com/photo-1522337660859-02fbefca4702?w=600&q=80', 'https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=600&q=80']
      },
      {
        id: 2, name: 'Cherry_', service: '植物养护染', stylist: 'Mia',
        stars: [{ i: 1, on: true }, { i: 2, on: true }, { i: 3, on: true }, { i: 4, on: true }, { i: 5, on: true }],
        avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=600&q=80',
        text: '染膏味道很淡，头皮完全不刺激。颜色比预想的还好看，出门收到好多夸赞，已经约下次了。',
        hasImg: false, imgs: []
      },
      {
        id: 3, name: '林木木', service: '头皮深层SPA', stylist: 'Aaron',
        stars: [{ i: 1, on: true }, { i: 2, on: true }, { i: 3, on: true }, { i: 4, on: true }, { i: 5, on: false }],
        avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&q=80',
        text: '做完头皮检测才知道自己出油的原因，SPA 手法很专业，头肩颈一起放松，做完整个人都轻了。',
        hasImg: true, imgs: ['https://images.unsplash.com/photo-1599387737838-626bf0d1f1f3?w=600&q=80']
      }
    ],

    summary: '设计师剪发 · 6/09 14:00',

    // 服务 Tab
    serviceGroups: [
      {
        id: 1, title: '剪 · 造型',
        items: [
          { id: 1, name: '总监剪发', desc: '资深总监亲自操刀', duration: '60min', price: '388' },
          { id: 2, name: '设计师剪发', desc: '一对一定制方案', duration: '60min', price: '288' },
          { id: 3, name: '刘海 / 局部修剪', desc: '快速修整', duration: '20min', price: '68' }
        ]
      },
      {
        id: 2, title: '染 · 烫',
        items: [
          { id: 4, name: '植物养护染', desc: '低敏染膏含护理', duration: '150min', price: '880' },
          { id: 5, name: '高级灰冷棕', desc: '进口色乳 · 含漂', duration: '210min', price: '1280' },
          { id: 6, name: '空气感软烫', desc: '韩式无痕烫', duration: '180min', price: '980' }
        ]
      },
      {
        id: 3, title: '护 · 养',
        items: [
          { id: 7, name: '头皮深层 SPA', desc: '检测 + 净化 + 舒缓', duration: '90min', price: '468' },
          { id: 8, name: '角蛋白深层修护', desc: '受损发质急救', duration: '60min', price: '398' }
        ]
      }
    ],
    selectedCard: 2,
    vipCards: [
      { id: 1, name: '体验卡', desc: '充 1000 享 9 折', price: '1000', value: '1100' },
      { id: 2, name: '臻享卡', desc: '充 3000 享 8 折 + 专属顾问', price: '3000', value: '3600' },
      { id: 3, name: '至尊卡', desc: '充 6000 享 7 折 + 免费养护', price: '6000', value: '8000' }
    ],

    // 案例 Tab
    worksTab: 'hair',
    worksTabs: [
      { key: 'hair', label: '剪 · 造型' },
      { key: 'color', label: '染 · 色彩' }
    ],
    worksHair: [
      { id: 1, title: '法式慵懒卷', by: 'Vincent', src: 'https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600&q=80' },
      { id: 2, title: '锁骨微钩', by: 'Aaron', src: 'https://images.unsplash.com/photo-1522337660859-02fbefca4702?w=600&q=80' },
      { id: 3, title: '空气八字刘海', by: 'Leo', src: 'https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=600&q=80' },
      { id: 4, title: '利落男士纹理', by: 'Vincent', src: 'https://images.unsplash.com/photo-1599387737838-626bf0d1f1f3?w=600&q=80' }
    ],
    worksColor: [
      { id: 1, title: '高级灰亚麻', by: 'Mia', src: 'https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?w=600&q=80' },
      { id: 2, title: '冷棕渐变', by: 'Mia', src: 'https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=600&q=80' },
      { id: 3, title: '雾感奶茶色', by: 'Leo', src: 'https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=600&q=80' },
      { id: 4, title: '深海蓝挑染', by: 'Aaron', src: 'https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=600&q=80' }
    ],

    // 我的 Tab
    me: {
      name: '林一一',
      tag: '臻享卡会员 · 累计到店 18 次',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&q=80',
      balance: '2860',
      coupons: '4',
      points: '1280',
      next: { service: '设计师剪发 + 头皮SPA', time: '6月9日 周一 14:00', stylist: 'Vincent' }
    },
    menus: [
      { label: '我的预约', icon: 'calendar', extra: '1 个进行中' },
      { label: '我的卡券', icon: 'coupon', extra: '4 张' },
      { label: '到店记录', icon: 'clock', extra: '' },
      { label: '帮助与反馈', icon: 'help', extra: '' }
    ]
  },

  onPageScroll(e) {
    const next = e.scrollTop > 60;
    if (next !== this.data.scrolled) this.setData({ scrolled: next });
  },

  // ---------- 互动①：tabBar 切换 ----------
  switchTab(e) { this.setData({ activeTab: e.currentTarget.dataset.tab }); },

  onBack() { wx.showToast({ title: '返回上一页', icon: 'none' }); },
  onShare() { wx.showToast({ title: '已生成门店名片', icon: 'none' }); },
  onHeroChange(e) { this.setData({ heroCurrent: e.detail.current }); },
  onPreviewStore() { wx.showToast({ title: '查看门店实景', icon: 'none' }); },
  onReviewsTab() { wx.showToast({ title: '查看全部评价', icon: 'none' }); },
  onNavigate() { wx.showToast({ title: '为你打开导航', icon: 'none' }); },
  onHours() { wx.showToast({ title: '营业时间 10:00–21:00', icon: 'none' }); },

  // ---------- 预约四级选择 ----------
  onSelectService(e) {
    const id = e.currentTarget.dataset.id;
    const it = this.data.servicesPick.find(s => s.id === id);
    this.setData({ selectedService: id, selectedServiceName: it ? '已选「' + it.name + '」' : '' });
    this._refreshSummary();
  },
  onSelectStylist(e) {
    const id = e.currentTarget.dataset.id;
    const it = this.data.stylists.find(s => s.id === id);
    this.setData({ selectedStylist: id, selectedStylistName: it ? it.name : '' });
    wx.showToast({ title: '已选 ' + (it ? it.name : ''), icon: 'none' });
  },
  onSelectDate(e) {
    this.setData({ selectedDate: e.currentTarget.dataset.id });
    this._refreshSummary();
  },
  onSelectSlot(e) {
    if (e.currentTarget.dataset.full) {
      wx.showToast({ title: '该时段已约满', icon: 'none' });
      return;
    }
    const id = e.currentTarget.dataset.id;
    const it = this.data.slots.find(s => s.id === id);
    this.setData({ selectedSlot: id, selectedSlotName: it ? it.time : '' });
    this._refreshSummary();
  },
  _refreshSummary() {
    const sv = this.data.servicesPick.find(s => s.id === this.data.selectedService);
    const dt = this.data.dates.find(d => d.id === this.data.selectedDate);
    const sl = this.data.slots.find(s => s.id === this.data.selectedSlot);
    const parts = [];
    if (sv) parts.push(sv.name);
    if (dt) parts.push(dt.day);
    if (sl) parts.push(sl.time);
    this.setData({ summary: parts.length ? parts.join(' · ') : '请选择服务与时段' });
  },

  // ---------- 互动②：input / textarea 双向绑定 ----------
  onPhoneInput(e) { this.setData({ 'form.phone': e.detail.value }); },
  onNoteInput(e) {
    const v = e.detail.value;
    this.setData({ 'form.note': v, noteLen: v.length });
  },

  onAllPhotos() { wx.showToast({ title: '查看全部环境照', icon: 'none' }); },
  onPreviewEnv() { wx.showToast({ title: '查看大图', icon: 'none' }); },
  onReview() { wx.showToast({ title: '展开评价', icon: 'none' }); },

  // ---------- 服务 Tab ----------
  onPriceItem(e) { wx.showToast({ title: e.currentTarget.dataset.name, icon: 'none' }); },
  onSelectCard(e) { this.setData({ selectedCard: e.currentTarget.dataset.id }); },
  onBuyCard() { wx.showToast({ title: '开卡（演示）', icon: 'none' }); },

  // ---------- 案例 Tab ----------
  onWorksTab(e) { this.setData({ worksTab: e.currentTarget.dataset.key }); },
  onWork() { wx.showToast({ title: '查看作品详情', icon: 'none' }); },

  // ---------- 我的 Tab ----------
  onSettings() { wx.showToast({ title: '设置', icon: 'none' }); },
  onBalance() { wx.showToast({ title: '卡内余额明细', icon: 'none' }); },
  onCoupons() { wx.showToast({ title: '我的优惠券', icon: 'none' }); },
  onPoints() { wx.showToast({ title: '积分中心', icon: 'none' }); },
  onMyBooking() { wx.showToast({ title: '预约详情', icon: 'none' }); },
  onReschedule() { wx.showToast({ title: '申请改约', icon: 'none' }); },
  onCheckin() { wx.showToast({ title: '到店核销成功', icon: 'success' }); },
  onMenu(e) { wx.showToast({ title: e.currentTarget.dataset.label, icon: 'none' }); },

  onConsult() { wx.showToast({ title: '正在接入顾问', icon: 'none' }); },

  // ---------- 互动③：确认预约 button → wx.showToast（带校验） ----------
  onConfirm() {
    if (!this.data.selectedSlot) {
      wx.showToast({ title: '请选择预约时段', icon: 'none' });
      return;
    }
    if (!/^1\d{10}$/.test(this.data.form.phone)) {
      wx.showToast({ title: '请填写正确手机号', icon: 'none' });
      return;
    }
    wx.showToast({ title: '预约成功', icon: 'success' });
  }
});
