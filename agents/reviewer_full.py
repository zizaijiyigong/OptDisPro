"""
ReviewerFullAgent - 完整代码审查智能体

该智能体负责审查代码并输出修改后的完整代码文件，而不是代码片段。
"""

import ast
import sys
import traceback
from agents.prompt.reviewer_full_prompt import ReviewerFull_role, ReviewerFull_instruction


class ReviewerFullAgent:
    """
    完整代码审查智能体
    
    负责审查代码质量，检查错误，并输出修改后的完整代码文件
    """
    
    def __init__(self, llm_client=None):
        """
        初始化ReviewerFullAgent
        
        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
        
    def review_complete_code(self, complete_code, user_instruction, error_log=None):
        """
        审查完整代码并输出修改后的完整代码
        
        Args:
            complete_code (str): 完整的代码
            user_instruction (str): 用户指令
            error_log (str): 错误日志信息
            
        Returns:
            dict: 审查结果和修改后的完整代码
        """
        print(f"🔍 开始完整代码审查...")
        
        # 首先进行快速语法检查
        syntax_valid, syntax_error = self.quick_syntax_check(complete_code, "完整代码")
        
        if self.llm_client:
            # 使用LLM进行代码审查
            return self._llm_review_complete_code(
                user_instruction, 
                complete_code, 
                error_log or syntax_error
            )
        else:
            # 使用模拟审查
            return self._mock_review_complete_code(
                user_instruction, 
                complete_code, 
                error_log or syntax_error
            )
    
    def _llm_review_complete_code(self, user_instruction, complete_code, log_info):
        """
        使用LLM审查完整代码
        
        Args:
            user_instruction (str): 用户指令
            complete_code (str): 完整代码
            log_info (str): 日志信息
            
        Returns:
            dict: 审查结果
        """
        try:
            prompt = ReviewerFull_role + "\n\n" + ReviewerFull_instruction.format(
                code=complete_code,
                user_instruction=user_instruction,
                loginfo=log_info or "无报错信息"
            )
            
            # 调用大模型进行审查，使用智能体特定配置
            response = self.llm_client.generate(
                prompt=prompt,
                agent_type="reviewer"
            )
            
            # 解析审查结果
            review_result = self._parse_review_result(response)
            
            print(f"📊 审查状态: {review_result['status']}")
            if review_result['analysis']:
                print(f"📝 分析结果: {review_result['analysis']}")
            
            return review_result
            
        except Exception as e:
            print(f"❌ LLM审查出错: {e}")
            return self._mock_review_complete_code(user_instruction, complete_code, log_info)
    
    
    def _generate_corrected_code(self, original_code, issues):
        """
        生成修正后的代码
        
        Args:
            original_code (str): 原始代码
            issues (list): 问题列表
            
        Returns:
            str: 修正后的代码
        """
        corrected_code = original_code
        
        # 添加必要的导入
        import_lines = []
        if any('numpy' in issue for issue in issues):
            import_lines.append("import numpy as np")
        if any('OpenDSS' in issue for issue in issues):
            import_lines.append("import opendssdirect as dss")
            import_lines.append("from opendssdirect import *")
        
        if import_lines:
            imports = '\n'.join(import_lines) + '\n\n'
            if not corrected_code.startswith('import'):
                corrected_code = imports + corrected_code
        
        # 添加缺少的函数定义
        if any('目标函数' in issue for issue in issues):
            if 'def targetfunction' not in corrected_code:
                target_func = """
    def targetfunction(self, x):
        \"\"\"
        目标函数
        
        Args:
            x: 优化变量
            
        Returns:
            float: 目标函数值
        \"\"\"
        try:
            # TODO: 实现具体的目标函数逻辑
            return 0.0
        except Exception as e:
            print(f"目标函数计算出错: {e}")
            return float('inf')
"""
                # 在类定义中添加目标函数
                if 'class ' in corrected_code:
                    lines = corrected_code.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('class ') and i < len(lines) - 1:
                            lines.insert(i + 1, target_func)
                            break
                    corrected_code = '\n'.join(lines)
                else:
                    corrected_code += target_func
        
        if any('求解函数' in issue for issue in issues):
            if 'def solve_optimization' not in corrected_code:
                solver_func = """
    def solve_optimization(self, bounds):
        \"\"\"
        求解优化问题
        
        Args:
            bounds: 变量边界
            
        Returns:
            优化结果
        \"\"\"
        # TODO: 实现具体的求解算法
        pass
"""
                # 在类定义中添加求解函数
                if 'class ' in corrected_code:
                    lines = corrected_code.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('class ') and i < len(lines) - 1:
                            lines.insert(i + 1, solver_func)
                            break
                    corrected_code = '\n'.join(lines)
                else:
                    corrected_code += solver_func
        
        return corrected_code
    
    def _parse_review_result(self, review_text):
        """
        解析大模型返回的审查结果
        
        Args:
            review_text (str): 审查结果文本
            
        Returns:
            dict: 结构化的审查结果
        """
        lines = review_text.strip().split('\n')
        
        result = {
            'status': 'UNKNOWN',
            'analysis': '',
            'issues': [],
            'suggestions': [],
            'corrected_complete_code': '',
            'comments': ''
        }
        
        current_section = None
        in_code_block = False
        code_block_started = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # 检查是否是新的section开始
            if stripped_line.startswith('REVIEW_STATUS:'):
                result['status'] = stripped_line.split(':', 1)[1].strip()
                in_code_block = False
                code_block_started = False
            elif stripped_line.startswith('ANALYSIS:'):
                result['analysis'] = stripped_line.split(':', 1)[1].strip()
                in_code_block = False
                code_block_started = False
            elif stripped_line.startswith('ISSUES:'):
                current_section = 'issues'
                in_code_block = False
                code_block_started = False
            elif stripped_line.startswith('SUGGESTIONS:'):
                current_section = 'suggestions'
                in_code_block = False
                code_block_started = False
            elif stripped_line.startswith('CORRECTED_COMPLETE_CODE:'):
                current_section = 'corrected_complete_code'
                in_code_block = True
                code_block_started = False
            elif stripped_line.startswith('COMMENTS:'):
                result['comments'] = stripped_line.split(':', 1)[1].strip()
                in_code_block = False
                code_block_started = False
            elif current_section and (stripped_line or in_code_block):
                # 处理各个section的内容
                if current_section == 'issues':
                    if stripped_line != '无':
                        result['issues'].append(stripped_line)
                elif current_section == 'suggestions':
                    if stripped_line != '无':
                        result['suggestions'].append(stripped_line)
                elif current_section == 'corrected_complete_code':
                    if stripped_line != '无需修改':
                        # 处理markdown代码块标记
                        if in_code_block and not code_block_started:
                            # 检查是否是代码块开始标记
                            if stripped_line.startswith('```'):
                                code_block_started = True
                                continue  # 跳过这行
                            else:
                                code_block_started = True
                        
                        # 检查是否是代码块结束标记
                        if code_block_started and stripped_line.startswith('```'):
                            continue  # 跳过这行
                        
                        # 添加代码内容（保持原始缩进）
                        result['corrected_complete_code'] += line + '\n'
            elif not stripped_line and in_code_block:
                # 在代码块中保留空行
                if current_section == 'corrected_complete_code' and code_block_started:
                    result['corrected_complete_code'] += '\n'
        
        # 清理代码字符串
        result['corrected_complete_code'] = result['corrected_complete_code'].strip()
        
        # 如果没有解析到状态，尝试从分析中推断
        if result['status'] == 'UNKNOWN':
            if result['issues'] and result['issues'] != ['无']:
                result['status'] = 'NEEDS_MODIFICATION'
            else:
                result['status'] = 'PASS'
        
        return result
    
    def quick_syntax_check(self, code, code_type="unknown"):
        """
        快速语法检查
        
        Args:
            code (str): 代码字符串
            code_type (str): 代码类型描述
            
        Returns:
            tuple: (是否通过, 错误信息)
        """
        try:
            compile(code, f'<{code_type}>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"{code_type}语法错误: 第{e.lineno}行 - {e.msg}"
        except Exception as e:
            return False, f"{code_type}编译错误: {e}" 