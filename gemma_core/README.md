# gemma_core

`gemma_core` 是 Gemma Match 的基建目录，包含黄金样例语料、静态校验器、prompt 构造器和离线评测脚本。运行：

```bash
cd gemma_core
python eval_harness.py
```

可用 23 个样例作为 stub 跑通评测。导入示例：

```python
from prompt_builder import build_prompt, build_repair_prompt
from validators import validate_project
```

场景：product_detail、signup_form、product_list、booking_form、store_intro、corporate_homepage、course_detail、news_list、news_detail、profile、order_list、coupon_claim、service_pricing、job_posting、real_estate、restaurant_menu、portfolio、survey、contact_us。
