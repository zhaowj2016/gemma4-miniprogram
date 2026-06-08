Page({
  data: {
    serviceName: '中医推拿调理',
    priceText: '298.00',
    durationText: '60',
    selectedDate: '06-06',
    dateOptions: [
      { dateText: '06-05', weekText: '周四', dayText: '5' },
      { dateText: '06-06', weekText: '周五', dayText: '6' },
      { dateText: '06-07', weekText: '周六', dayText: '7' },
      { dateText: '06-08', weekText: '周日', dayText: '8' },
      { dateText: '06-09', weekText: '周一', dayText: '9' },
      { dateText: '06-10', weekText: '周二', dayText: '10' }
    ],
    selectedSlot: '14:00-15:00',
    slotOptions: [
      '09:00-10:00', '10:00-11:00', '11:00-12:00',
      '14:00-15:00', '15:00-16:00', '16:00-17:00',
      '17:00-18:00', '19:00-20:00', '20:00-21:00'
    ],
    formData: { name: '', phone: '', note: '' }
  },

  onDateTap(e) {
    this.setData({ selectedDate: e.currentTarget.dataset.date });
  },

  onSlotTap(e) {
    this.setData({ selectedSlot: e.currentTarget.dataset.slot });
  },

  onNameInput(e) {
    this.setData({ 'formData.name': e.detail.value });
  },

  onPhoneInput(e) {
    this.setData({ 'formData.phone': e.detail.value });
  },

  onNoteInput(e) {
    this.setData({ 'formData.note': e.detail.value });
  },

  onSubmit() {
    const { name, phone } = this.data.formData;
    if (!name) {
      wx.showToast({ title: '请输入联系人姓名', icon: 'none' });
      return;
    }
    if (!/^1\d{10}$/.test(phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' });
      return;
    }
    if (!this.data.selectedSlot) {
      wx.showToast({ title: '请选择时段', icon: 'none' });
      return;
    }
    wx.showToast({ title: '预约成功', icon: 'success' });
  }
});
