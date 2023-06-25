import re
import subprocess
import json
import tempfile

gen_vbscript_function = {
  "name": "gen_vbscript",
  "description": "Use VBScript to complete the above user request",
  "parameters": {
    "type": "object",
    "properties": {
      "code": {
        "type": "string",
        "description": "VBScript code for user request",
      },
    },
    "required": ["code"]
  }
}


class Agent:
    def __init__(self):
        self.name = "vbscript"
        self.description = "生成和运行VBScript脚本"
        
    def run(self, question, context, mygpt, model_config_yaml, **kwarg):

        pattern = r"```vbscript(.*?)```"
        # 是否运行脚本判断
        if len(context) > 0:
            pre_answer = context[-1][1]
            matches = re.findall(pattern, pre_answer, re.DOTALL)
            if len(matches) == 1:
                if "y" in question.lower():
                    answer = "已执行  \n"
                    pattern = r"```vbscript(.*?)```"
                    answer += self.run_script(matches[0])
                    return question, answer, [], ""
                elif "n" in question.lower():
                    answer = "取消执行"
                    return question, answer, [], ""
        
        # 响应用户请求，生成脚本
        prompt = f"""
        user request:{question}
Use VBScript to complete the above user request. 
All the output code is contained in a single markdown code block, marked with ```vbscript ```."""
        
        out = mygpt.llm(prompt, 
                        context=context,
                        functions=[gen_vbscript_function],
                        function_call={"name": "gen_vbscript"})

        # 后处理,格式化输出
        out_obj = json.loads(out)
        code = out_obj['code']

        out = f"""```vbscript
{code}
```"""

        matches = re.findall(pattern, out, re.DOTALL)
        if len(matches) == 1: 
            answer = out + "  \n" + "是否执行脚本(y/n)"
        else:
            answer = out + "  \n" + "生成的代码似乎有问题，建议重新生成"
        
        return question, answer, [], ""

    def run_script(self, script):
        try:
            # 创建一个临时.vbs文件
            with tempfile.NamedTemporaryFile(suffix=".vbs", delete=False, mode="w") as temp_file:
                temp_file.write(script)
                temp_file_name = temp_file.name

            # 使用cscript执行临时.vbs文件
            return subprocess.check_output(['cscript', '//NoLogo', temp_file_name]).decode("utf-8")
    
        except subprocess.CalledProcessError as e:
            return f"An error occurred: {e}"