Page({
  data: {
    brandName: '云策科技',
    brandTagline: 'CONTACT US',
    heroSubText: '我们期待与您建立联系, 无论是产品咨询, 合作机会, 还是单纯的问候, 都欢迎随时告诉我们。',
    contactCards: {
      phone: {
        iconText: '电',
        name: '客服电话',
        value: '400-100-2008',
        hint: '工作日 9:00 - 18:00'
      },
      email: {
        iconText: '邮',
        name: '商务邮箱',
        value: 'hello@yunce.tech',
        hint: '24 小时内回复'
      },
      wechat: {
        iconText: '微',
        name: '官方微信',
        value: 'yunce_tech',
        hint: '扫码添加企业微信'
      },
      address: {
        iconText: '地',
        name: '总部地址',
        value: '上海 · 静安',
        hint: '南京西路 1788 号'
      }
    },
    hours: [
      { dayText: '周一至周五', timeText: '09:00 - 18:00' },
      { dayText: '周六', timeText: '10:00 - 17:00' },
      { dayText: '周日', timeText: '休息' }
    ],
    formData: { name: '', contact: '', message: '' }
  },

  onContactTap(e) {
    const type = e.currentTarget.dataset.type;
    const nameMap = {
      phone: '拨打客服电话',
      email: '发送邮件',
      wechat: '打开微信二维码',
      address: '查看地图位置'
    };
    wx.showToast({ title: nameMap[type] || '打开', icon: 'none' });
  },

  onNameInput(e) {
    this.setData({ 'formData.name': e.detail.value });
  },

  onContactInput(e) {
    this.setData({ 'formData.contact': e.detail.value });
  },

  onMessageInput(e) {
    this.setData({ 'formData.message': e.detail.value });
  },

  onSubmit() {
    const { name, contact, message } = this.data.formData;
    if (!name) {
      wx.showToast({ title: '请输入您的称呼', icon: 'none' });
      return;
    }
    if (!contact) {
      wx.showToast({ title: '请输入联系方式', icon: 'none' });
      return;
    }
    if (!message) {
      wx.showToast({ title: '请输入留言内容', icon: 'none' });
      return;
    }
    wx.showToast({ title: '留言已发送', icon: 'success' });
    this.setData({ formData: { name: '', contact: '', message: '' } });
  }
});
