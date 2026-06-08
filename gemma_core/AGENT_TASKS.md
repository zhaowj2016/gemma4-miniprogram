# 两个 Agent 的并行任务包

## 放在哪里(重要,防冲突)
把本文件夹整个放进你现有项目仓库,作为一个**专用子文件夹**,例如:

    你的项目/
    └── gemma_core/        ← 把本包解压到这里, 两个 agent 的工作目录都设成这个文件夹
        ├── validators.py
        ├── golden_examples/
        ├── BUILD_SPEC.md
        └── AGENT_TASKS.md (本文件)

- 两个 agent 的**工作目录都设成 gemma_core/**,并遵守"只在本文件夹新建文件、不修改任何已有文件"的护栏 → 与你已有代码零冲突。
- app 运行时用:`from gemma_core.validators import validate_project`(想要包导入就在 gemma_core/ 放一个空的 __init__.py)。
- 不要建在仓库外面的独立文件夹——app 运行时要用到这些文件。

---

## 提示词 A —— 贴给 MiniMax(造语料 / 数据)

你的任务:为微信小程序生成器扩充一批"黄金样例语料",用作 few-shot 池 + 评测集。
工作目录就是本文件夹(gemma_core/),只在这里面新建文件,不要碰任何已有文件。

可用资源(本目录已有):
- validators.py(静态校验器,你的唯一裁判)
- golden_examples/product_detail/ 和 golden_examples/signup_form/(已有范例,照风格写)
- BUILD_SPEC.md 第 6 节(约束清单)

每个样例 = 一个页面的三个文件:index.wxml / index.wxss / index.js(脚手架其余文件固定,不用管)。

覆盖场景(已有的 商品详情、活动报名 不重复,其余尽量做):
商品列表、预约表单、门店介绍、企业官网首页、课程详情、图文资讯列表、图文详情、
个人中心、订单列表、优惠券领取、服务报价、招聘岗位、房源展示、餐饮菜单、作品集、问卷收集、联系我们。

硬约束(违反即废样例):
- 禁止 HTML 标签(<div> <p> <span> <img> <a> <ul> <li> 等),一律 view/text
- 禁止在 {{ }} 里调函数(如 {{price.toFixed(2)}}),格式化在 JS 里做好存成字符串
- swiper 用 current,不是 current-index
- 禁止 wx.login / wx.request / wx.requestPayment / wx.getLocation / wx.cloud
- 数据全用本地 mock;只用基础组件;有底部操作的用吸边底栏 + safe-area;用 rpx

【强制】每写完一个样例,用校验器跑一遍,只保留通过的:
    from validators import validate_project
    files = {'pages/index/index.wxml': WXML, 'pages/index/index.wxss': WXSS, 'pages/index/index.js': JS}
    r = validate_project(files, full_project=False)
    # r.ok 必须为 True;若 r.hard_errors 非空,修到通过,否则丢弃

输出:
1. 每个通过的样例 → golden_examples/<场景英文名>/{index.wxml,index.wxss,index.js}
2. corpus_index.json:数组,每项 {name, description, keywords:[触发关键词]}
3. benchmark_prompts.json:数组,每项 {scenario, prompt:"用户大白话描述"}

数量目标:12-18 个通过校验的样例。
完成标准:N(≥12)个样例全部通过校验 + 两个 JSON 写好。

---

## 提示词 B —— 贴给 Codex(Goal 模式,造评测和 prompt 模块)

你的任务:构建评测 harness 和 few-shot prompt 模块,作为新增独立文件。
工作目录就是本文件夹(gemma_core/)。

【最重要的护栏】
- 绝对不要修改 app.py、现有界面、validators.py 或任何已存在的文件。
- 只新建下面两个文件。validators.validate_project 是判定对错的唯一标准。

任务 1:prompt_builder.py
- build_prompt(user_prompt): 从 golden_examples/ 读样例,按关键词(对照 corpus_index.json,没有就按文件名)挑 1-2 个最相关的当 few-shot,拼成系统 prompt = 约束清单 + 选中样例 + 用户需求。
- build_repair_prompt(user_prompt, page_files, errors): 把校验错误喂回去,要求只修错、全量重出三文件。
- 约束清单写进系统 prompt:只用基础组件;禁 HTML 标签;禁 {{}} 里调函数;swiper 用 current;禁 wx.login/request/requestPayment/getLocation/cloud;数据用本地 mock。

任务 2:eval_harness.py
- 读 benchmark_prompts.json(不存在就退化为直接校验 golden_examples/ 每个样例,证明 harness 能跑)。
- 可插拔:接收 generate_fn(prompt)->{'wxml','wxss','js'};没接真实 Gemma 客户端时默认用 stub(返回对应 golden 样例),保证离线能跑通。
- 每条:generate -> validate_project(..., full_project=False),最后打印表:场景 | 首次 PASS/FAIL | hard_errors 数。

完成标准:两文件建好;python eval_harness.py 能端到端跑(至少 dry 模式)并打印通过率表;未改动任何已有文件。
