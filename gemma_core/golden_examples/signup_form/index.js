Page({
  data: {
    title: '周末亲子绘画活动报名',
    formData: { name: '', phone: '' },
    errors: { name: '', phone: '' }
  },

  onNameInput(e) {
    this.setData({ 'formData.name': e.detail.value });
  },

  onPhoneInput(e) {
    this.setData({ 'formData.phone': e.detail.value });
  },

  onSubmit() {
    const { name, phone } = this.data.formData;
    const errors = { name: '', phone: '' };
    if (!name) {
      errors.name = '请输入姓名';
    }
    if (!/^1\d{10}$/.test(phone)) {
      errors.phone = '请输入正确的 11 位手机号';
    }
    this.setData({ errors: errors });
    if (errors.name || errors.phone) {
      return;
    }
    // 第一阶段只做本地 mock 提交, 不发真实网络请求
    wx.showToast({ title: '报名成功', icon: 'success' });
  }
});
