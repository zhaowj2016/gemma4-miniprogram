Page({
  data: {
    title: '用户使用习惯调研',
    subtitleText: '大约需要 3 分钟, 您的反馈对我们很重要',
    currentIndex: 0,
    questions: [
      {
        type: 'single',
        title: '您最常在哪种场景下使用我们的小程序?',
        required: true,
        options: ['工作日的通勤路上', '工作日的午休时间', '周末的空闲时间', '晚上睡觉前']
      },
      {
        type: 'multi',
        title: '您使用过小程序的哪些功能? (可多选)',
        required: true,
        options: ['浏览商品', '在线下单', '查看订单', '联系客服', '参与活动', '分享给好友']
      },
      {
        type: 'single',
        title: '整体而言, 您对小程序的满意度如何?',
        required: true,
        options: ['非常满意', '比较满意', '一般', '不太满意', '很不满意']
      },
      {
        type: 'text',
        title: '您最希望我们接下来优化哪个方面?',
        required: false
      }
    ],
    answers: ['', [], '', ''],
    currentAnswer: '',
    multiAnswerMap: {}
  },

  onLoad() {
    this.refreshCurrentQuestion();
  },

  refreshCurrentQuestion() {
    const idx = this.data.currentIndex;
    const q = this.data.questions[idx];
    const ans = this.data.answers[idx];
    this.setData({
      currentQuestion: q,
      currentAnswer: q.type === 'multi' ? '' : (ans || ''),
      multiAnswerMap: q.type === 'multi' ? this.toMap(ans || []) : {},
      currentIndexText: String(idx + 1),
      totalText: String(this.data.questions.length),
      isLast: idx === this.data.questions.length - 1,
      progressText: this.computeProgress(idx)
    });
  },

  toMap(arr) {
    const m = {};
    (arr || []).forEach((v) => { m[v] = true; });
    return m;
  },

  computeProgress(idx) {
    const total = this.data.questions.length;
    const pct = Math.round(((idx + 1) / total) * 100);
    return pct + '%';
  },

  onSingleSelect(e) {
    const val = e.currentTarget.dataset.value;
    const idx = this.data.currentIndex;
    const answers = this.data.answers.slice();
    answers[idx] = val;
    this.setData({
      currentAnswer: val,
      answers: answers
    });
  },

  onMultiSelect(e) {
    const val = e.currentTarget.dataset.value;
    const idx = this.data.currentIndex;
    const cur = this.data.answers[idx] || [];
    const has = cur.indexOf(val) >= 0;
    const next = has ? cur.filter((x) => x !== val) : cur.concat([val]);
    const answers = this.data.answers.slice();
    answers[idx] = next;
    this.setData({
      answers: answers,
      multiAnswerMap: this.toMap(next)
    });
  },

  onTextInput(e) {
    const idx = this.data.currentIndex;
    const answers = this.data.answers.slice();
    answers[idx] = e.detail.value;
    this.setData({
      currentAnswer: e.detail.value,
      answers: answers
    });
  },

  onPrevTap() {
    if (this.data.currentIndex === 0) {
      wx.showToast({ title: '已经是第一题', icon: 'none' });
      return;
    }
    this.setData({ currentIndex: this.data.currentIndex - 1 });
    this.refreshCurrentQuestion();
  },

  onNextTap() {
    const idx = this.data.currentIndex;
    const q = this.data.questions[idx];
    const ans = this.data.answers[idx];
    if (q.required) {
      if (q.type === 'multi' && (!ans || ans.length === 0)) {
        wx.showToast({ title: '请至少选择一项', icon: 'none' });
        return;
      }
      if ((q.type === 'single' || q.type === 'text') && !ans) {
        wx.showToast({ title: '请回答本道题', icon: 'none' });
        return;
      }
    }
    if (this.data.isLast) {
      wx.showToast({ title: '问卷已提交, 感谢反馈', icon: 'success' });
      return;
    }
    this.setData({ currentIndex: this.data.currentIndex + 1 });
    this.refreshCurrentQuestion();
  }
});
