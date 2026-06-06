# 生成 按钮
def create_miniprogram_button(props: list, text_content: str):
    props_str = " ".join(props)
    button_code = f"<button {props_str}>{text_content}</button>"
    return {"status": "success", "code": button_code}

# 生成 输入框
def create_miniprogram_input(props: list, placeholder: str):
    props_str = " ".join(props)
    input_code = f"<input {props_str} placeholder='{placeholder}'/>"
    return {"status": "success", "code": input_code}

# 组装 表单（把输入框、按钮拼成一页）
def assemble_miniprogram_form(components: list):
    form_code = "<form bindsubmit='formSubmit'>\n"
    for comp in components:
        form_code += f"  {comp}\n"
    form_code += "</form>"
    return {"status": "success", "code": form_code}

# 测试代码
if __name__ == "__main__":
    btn = create_miniprogram_button(['type="primary"', 'color="red"'], "登录")
    print("按钮代码：", btn["code"])