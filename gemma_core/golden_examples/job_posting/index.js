Page({
  data: {
    departmentText: '云策科技 / 数据中台部',
    jobTitle: '高级前端工程师 (React / 小程序方向)',
    tags: ['React', 'TypeScript', '小程序', '可视化'],
    locationText: '上海',
    experienceText: '5 年及以上',
    educationText: '本科及以上',
    salaryText: '30K - 55K · 14 薪',
    headcountText: '2 人',
    publishDateText: '2026-06-02',
    responsibilities: [
      '负责数据可视化产品前端架构设计与核心模块开发',
      '深入业务场景, 与产品, 设计, 后端紧密协作, 推动需求高质量落地',
      '参与团队前端工程化建设, 包括组件库, 脚手架, 性能优化',
      '承担 code review 与新人指导, 提升团队整体工程能力'
    ],
    requirements: [
      '计算机或相关专业本科及以上学历, 5 年以上前端开发经验',
      '精通 React, TypeScript, 熟悉主流状态管理方案',
      '有完整的小程序或 H5 移动端项目经验, 了解性能优化与兼容性处理',
      '具备数据可视化项目经验者优先 (ECharts / AntV / D3 等)',
      '良好的工程素养与沟通能力, 能在复杂业务中保持清晰的判断'
    ],
    benefits: [
      { iconText: '薪', title: '14 薪 + 绩效', descText: '年终奖与项目奖' },
      { iconText: '股', title: '期权激励', descText: '核心员工股权池' },
      { iconText: '假', title: '弹性假期', descText: '10 天带薪年假' },
      { iconText: '健', title: '商业医疗', descText: '员工 + 直系亲属' }
    ],
    teamText: '我们是一支由 30 + 工程师组成的数据产品团队, 负责公司核心数据中台与可视化产品的研发。团队倡导工程文化, 重视代码质量, 鼓励技术创新, 提供完善的成长路径与导师机制。'
  },

  onChatTap() {
    wx.showToast({ title: '打开与 HR 的对话', icon: 'none' });
  },

  onApplyTap() {
    wx.showToast({ title: '跳转到简历投递页', icon: 'success' });
  }
});
