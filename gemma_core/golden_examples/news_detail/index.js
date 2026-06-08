Page({
  data: {
    tagText: '深度',
    title: '国产大模型密集上新: 多模态能力集体跃迁, 行业落地进入下半场',
    sourceText: '科技日报',
    timeText: '2026-06-04',
    viewCountText: '8.6万',
    paragraphs: [
      '进入 2026 年下半年, 国产大模型在多模态理解, 长上下文记忆, 工具调用稳定性三个维度上迎来集中突破, 数十家厂商在两个月内相继发布新一代旗舰。',
      '本轮更新呈现出几个共同趋势: 上下文窗口普遍提升至 200K 以上, 视频理解能力从"识别物体"进化到"理解事件", 而企业级私有化部署成本进一步下降。',
      '从应用层看, 真正拉开差距的不再是基础模型本身, 而是基于行业 know-how 的工程化能力。能够把模型能力嵌入到企业核心业务流程中的玩家, 正在赢得更大的合同。'
    ],
    quoteText: '大模型的竞争从参数规模, 走向了场景深度。能够把 AI 真正嵌入业务流的公司, 才能在下一轮拿到红利。',
    closingText: '据多家头部投资机构透露, 2026 年下半年, AI 应用层融资将更看重"看得见的 ROI", 单纯的 API 套壳项目将面临严峻的估值修正。',
    isLiked: false,
    isFavorited: false,
    likeBtnText: '点赞',
    favBtnText: '收藏',
    related: [
      {
        id: 'a002',
        title: '从 Demo 到 1 个亿 ARR: 一家 AI 创业公司的 18 个月',
        timeText: '昨天',
        viewCountText: '2.3万'
      },
      {
        id: 'a003',
        title: '多模态大模型如何在制造业落地? 三个真实案例',
        timeText: '3 天前',
        viewCountText: '1.5万'
      }
    ],
    commentCountText: '128',
    comments: [
      {
        id: 'cm001',
        avatarText: '陈',
        name: '陈工',
        text: '分析得很到位, 我们公司就在做 AI 落地, 体感完全一致。',
        timeText: '2 小时前'
      },
      {
        id: 'cm002',
        avatarText: '林',
        name: '林子',
        text: '期待后续能讲讲具体行业的落地方法论。',
        timeText: '5 小时前'
      }
    ],
    draftText: ''
  },

  onLikeTap() {
    const next = !this.data.isLiked;
    this.setData({
      isLiked: next,
      likeBtnText: next ? '已点赞' : '点赞'
    });
  },

  onFavTap() {
    const next = !this.data.isFavorited;
    this.setData({
      isFavorited: next,
      favBtnText: next ? '已收藏' : '收藏'
    });
  },

  onShareTap() {
    wx.showToast({ title: '已复制文章链接', icon: 'success' });
  },

  onRelatedTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.showToast({ title: '跳转到 ' + id, icon: 'none' });
  },

  onDraftInput(e) {
    this.setData({ draftText: e.detail.value });
  },

  onSendTap() {
    const text = this.data.draftText.trim();
    if (!text) {
      wx.showToast({ title: '评论内容不能为空', icon: 'none' });
      return;
    }
    wx.showToast({ title: '评论已发布', icon: 'success' });
    this.setData({ draftText: '' });
  }
});
