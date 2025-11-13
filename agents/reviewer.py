#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer智能体
负责检查生成的代码，发现语法错误和逻辑问题
"""

from .prompt.reviewer_prompt import Reviewer_instruction, Reviewer_role
from .code_template import CodeTemplate

class ReviewerAgent:
    """Reviewer智能体 - 代码审查者"""
    
    def __init__(self, llm_client=None):
        """
        初始化Reviewer智能体
        
        Args:
            llm_client: 大语言模型客户端接口
        """
        self.llm_client = llm_client
        self.prompt_template = Reviewer_role
        self.code_template = CodeTemplate()
        
    def review_code_snippets(self, code_snippets, context=None):
        """
        审查代码片段质量和正确性
        
        Args:
            code_snippets (dict): 代码片段字典
            context (dict): 上下文信息
            
        Returns:
            dict: 审查结果
        """
        print(f"🔍 Reviewer正在审查代码...")
        
        # 提取代码片段
        objective_function_code = code_snippets.get('OBJECTIVE_FUNCTION', '')
        solver_code = code_snippets.get('OPTIMIZATION_ALGORITHM', '')
        user_instruction = context.get('user_requirements', '') if context else ''
        
        # 使用CodeTemplate拼接完整代码
        try:
            complete_code = self.code_template.insert_code_snippets_robust(code_snippets)
            
            # 统计代码信息
            line_count = len(complete_code.split('\n'))
            snippet_count = len([k for k, v in code_snippets.items() if v])
            
            print(f"✅ 代码拼接成功，共{line_count}行，包含{snippet_count}个代码片段")
            
        except Exception as e:
            print(f"❌ 代码拼接异常: {e}")
            return {
                'status': 'NEEDS_MODIFICATION',
                'analysis': f"代码拼接异常: {e}",
                'issues': [f"代码拼接异常: {e}"],
                'suggestions': ["检查代码片段格式", "确保代码片段完整性"],
                'corrected_code': code_snippets,
                'original_code': code_snippets
            }
        
        # 构造完整prompt，包含拼接后的完整代码
        prompt = Reviewer_instruction.format(
            code=complete_code,
            user_instruction=user_instruction,
            loginfo=""
        )
        full_prompt = self.prompt_template + "\n" + prompt
        
        if self.llm_client:
            # 调用大模型进行审查，使用智能体特定配置
            review_result = self.llm_client.generate(
                prompt=full_prompt,
                agent_type="reviewer"
            )
            parsed_result = self._parse_review_result(review_result)
            
            # 根据审查结果返回修正后的代码
            if parsed_result['status'] == 'NEEDS_MODIFICATION':
                print(f"⚠️  发现 {len(parsed_result['issues'])} 个问题，需要修改")
                print(f"📝 分析: {parsed_result['analysis']}")
                
                # 构建修正后的代码片段
                corrected_snippets = code_snippets.copy()
                
                # 应用目标函数修正
                if parsed_result['corrected_objective_function'] and parsed_result['corrected_objective_function'] != '无需修改':
                    corrected_snippets['OBJECTIVE_FUNCTION'] = parsed_result['corrected_objective_function']
                    print("✅ 已应用目标函数修正")
                
                # 应用优化算法修正（合并solver_code和user_problem）
                if parsed_result['corrected_optimization_algorithm'] and parsed_result['corrected_optimization_algorithm'] != '无需修改':
                    corrected_snippets['OPTIMIZATION_ALGORITHM'] = parsed_result['corrected_optimization_algorithm']
                    print("✅ 已应用优化算法修正")
                
                return {
                    'status': 'NEEDS_MODIFICATION',
                    'issues': parsed_result['issues'],
                    'suggestions': parsed_result['suggestions'],
                    'analysis': parsed_result['analysis'],
                    'corrected_code': corrected_snippets,
                    'original_code': code_snippets,
                    'complete_code': complete_code,
                    'corrected_objective_function': parsed_result['corrected_objective_function'],
                    'corrected_solver_code': parsed_result['corrected_solver_code'],
                    'corrected_user_problem': parsed_result['corrected_user_problem']
                }
            else:
                print(f"✅ 代码审查通过")
                return {
                    'status': 'PASS',
                    'analysis': parsed_result['analysis'],
                    'comments': '代码检查通过，无需修改。',
                    'corrected_code': code_snippets,  # 返回原始代码
                    'complete_code': complete_code
                }
        else:
            # 模拟审查（用于测试）
            return self._mock_review_code(user_instruction, objective_function_code, solver_code, complete_code)
    
    def review_code(self, user_instruction, objective_function_code, solver_code):
        """
        审查代码质量和正确性（兼容旧接口）
        
        Args:
            user_instruction (str): 用户指令
            objective_function_code (str): 目标函数代码
            solver_code (str): 求解算法代码
            
        Returns:
            dict: 审查结果
        """
        code_snippets = {
            'OBJECTIVE_FUNCTION': objective_function_code,
            'OPTIMIZATION_ALGORITHM': solver_code
        }
        context = {'user_requirements': user_instruction}
        
        return self.review_code_snippets(code_snippets, context)
    
    def _mock_review_code(self, user_instruction, objective_function_code, solver_code, complete_code):
        """
        模拟代码审查（用于测试）
        
        Args:
            user_instruction (str): 用户指令
            objective_function_code (str): 目标函数代码
            solver_code (str): 求解算法代码
            complete_code (str): 完整代码
            
        Returns:
            dict: 审查结果
        """
        issues = []
        suggestions = []
        corrected_objective = objective_function_code
        corrected_solver = solver_code
        
        # 基础语法检查
        try:
            compile(objective_function_code, '<objective>', 'exec')
        except SyntaxError as e:
            issues.append(f"[语法错误] 目标函数代码语法错误: {e}")
            suggestions.append("修正目标函数的语法错误")
        
        try:
            compile(solver_code, '<solver>', 'exec')
        except SyntaxError as e:
            issues.append(f"[语法错误] 求解器代码语法错误: {e}")
            suggestions.append("修正求解器的语法错误")
        
        # 检查完整代码的语法
        try:
            compile(complete_code, '<complete>', 'exec')
        except SyntaxError as e:
            issues.append(f"[语法错误] 完整代码语法错误: {e}")
            suggestions.append("检查代码片段拼接后的语法")
        
        # 逻辑检查
        if 'def targetfunction' not in objective_function_code and 'def objective_function' not in objective_function_code:
            issues.append("[逻辑错误] 目标函数缺少targetfunction或objective_function函数定义")
            suggestions.append("添加targetfunction函数定义")
            # 添加函数定义
            corrected_objective = f"""def targetfunction(self, x):
    {objective_function_code}"""
        
        if 'def solve_optimization' not in solver_code:
            issues.append("[逻辑错误] 求解器缺少solve_optimization函数定义")
            suggestions.append("添加solve_optimization函数定义")
        
        # 检查用户意图匹配
        instruction_lower = user_instruction.lower()
        if any(keyword in instruction_lower for keyword in ['最大化', 'maximize', 'max']):
            if 'return -' not in objective_function_code and 'maximize' not in objective_function_code.lower():
                issues.append("[逻辑错误] 用户要求最大化，但目标函数可能未正确处理")
                suggestions.append("对于最大化问题，考虑返回负值或使用最大化算法")
        
        # 检查异常处理
        if 'try:' not in objective_function_code and 'except' not in objective_function_code:
            issues.append("[健壮性] 目标函数缺少异常处理")
            suggestions.append("添加try-except块处理OpenDSS计算可能出现的异常")
            # 添加异常处理
            if 'def targetfunction' in corrected_objective:
                corrected_objective = corrected_objective.replace(
                    'def targetfunction(self, x):',
                    '''def targetfunction(self, x):
    try:'''
                )
                corrected_objective += '''
    except Exception as e:
        print(f"目标函数计算出错: {e}")
        return float('inf')
'''
        
        if issues:
            print(f"⚠️  发现 {len(issues)} 个问题")
            analysis = f"发现{len(issues)}个问题需要修改"
            
            # 构建修正后的完整代码
            corrected_complete_code = complete_code
            if corrected_objective != objective_function_code:
                # 替换目标函数部分
                corrected_complete_code = corrected_complete_code.replace(
                    objective_function_code, corrected_objective
                )
            if corrected_solver != solver_code:
                # 替换求解器部分
                corrected_complete_code = corrected_complete_code.replace(
                    solver_code, corrected_solver
                )
            
            return {
                'status': 'NEEDS_MODIFICATION',
                'analysis': analysis,
                'issues': issues,
                'suggestions': suggestions,
                'corrected_code': {
                    'OBJECTIVE_FUNCTION': corrected_objective,
                    'OPTIMIZATION_ALGORITHM': corrected_solver
                },
                'original_code': {
                    'OBJECTIVE_FUNCTION': objective_function_code,
                    'OPTIMIZATION_ALGORITHM': solver_code
                },
                'complete_code': complete_code,
                'corrected_complete_code': corrected_complete_code
            }
        else:
            print(f"✅ 代码审查通过")
            return {
                'status': 'PASS',
                'analysis': '代码检查通过，无需修改',
                'comments': '代码检查通过，无需修改。',
                'corrected_code': {
                    'OBJECTIVE_FUNCTION': objective_function_code,
                    'OPTIMIZATION_ALGORITHM': solver_code
                },
                'complete_code': complete_code
            }
    
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
            'corrected_objective_function': '',
            'corrected_solver_code': '',
            'corrected_user_problem': '',
            'comments': ''
        }
        
        current_section = None
        in_code_block = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # 检查是否是新的section开始
            if stripped_line.startswith('REVIEW_STATUS:'):
                result['status'] = stripped_line.split(':', 1)[1].strip()
                in_code_block = False
            elif stripped_line.startswith('ANALYSIS:'):
                result['analysis'] = stripped_line.split(':', 1)[1].strip()
                in_code_block = False
            elif stripped_line.startswith('ISSUES:'):
                current_section = 'issues'
                in_code_block = False
            elif stripped_line.startswith('SUGGESTIONS:'):
                current_section = 'suggestions'
                in_code_block = False
            elif stripped_line.startswith('CORRECTED_OBJECTIVE_FUNCTION:'):
                current_section = 'corrected_objective_function'
                in_code_block = True
            elif stripped_line.startswith('CORRECTED_SOLVER_CODE:'):
                current_section = 'corrected_solver_code'
                in_code_block = True
            elif stripped_line.startswith('CORRECTED_USER_PROBLEM:'):
                current_section = 'corrected_user_problem'
                in_code_block = True
            elif stripped_line.startswith('COMMENTS:'):
                result['comments'] = stripped_line.split(':', 1)[1].strip()
                in_code_block = False
            elif current_section and (stripped_line or in_code_block):
                # 处理各个section的内容
                if current_section == 'issues':
                    if stripped_line != '无':
                        result['issues'].append(stripped_line)
                elif current_section == 'suggestions':
                    if stripped_line != '无':
                        result['suggestions'].append(stripped_line)
                elif current_section == 'corrected_objective_function':
                    if stripped_line != '无需修改':
                        # 保持原始缩进
                        result['corrected_objective_function'] += line + '\n'
                elif current_section == 'corrected_solver_code':
                    if stripped_line != '无需修改':
                        # 保持原始缩进
                        result['corrected_solver_code'] += line + '\n'
                elif current_section == 'corrected_user_problem':
                    if stripped_line != '无需修改':
                        # 保持原始缩进
                        result['corrected_user_problem'] += line + '\n'
            elif not stripped_line and in_code_block:
                # 在代码块中保留空行
                if current_section == 'corrected_objective_function':
                    result['corrected_objective_function'] += '\n'
                elif current_section == 'corrected_solver_code':
                    result['corrected_solver_code'] += '\n'
                elif current_section == 'corrected_user_problem':
                    result['corrected_user_problem'] += '\n'
        
        # 清理代码字符串
        result['corrected_objective_function'] = result['corrected_objective_function'].strip()
        result['corrected_solver_code'] = result['corrected_solver_code'].strip()
        result['corrected_user_problem'] = result['corrected_user_problem'].strip()
        
        # 合并solver_code和user_problem为optimization_algorithm
        optimization_algorithm_parts = []
        if result['corrected_solver_code']:
            optimization_algorithm_parts.append(result['corrected_solver_code'])
        if result['corrected_user_problem']:
            optimization_algorithm_parts.append(result['corrected_user_problem'])
        
        result['corrected_optimization_algorithm'] = '\n\n'.join(optimization_algorithm_parts)
        
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
    
    def _extract_code_snippets_from_complete(self, complete_code):
        """
        从完整代码中提取代码片段
        
        Args:
            complete_code (str): 完整的代码
            
        Returns:
            dict: 提取的代码片段
        """
        code_snippets = {
            'OBJECTIVE_FUNCTION': '',
            'OPTIMIZATION_ALGORITHM': ''
        }
        
        lines = complete_code.split('\n')
        current_section = None
        current_code = []
        
        for line in lines:
            # 检测目标函数开始
            if 'def targetfunction' in line or 'def objective_function' in line:
                current_section = 'OBJECTIVE_FUNCTION'
                current_code = []
                continue
            
            # 检测求解器函数开始
            elif 'def solve_optimization' in line:
                current_section = 'OPTIMIZATION_ALGORITHM'
                current_code = []
                continue
            
            # 检测函数结束（下一个函数开始或文件结束）
            elif line.strip().startswith('def ') and current_section:
                # 保存当前函数代码
                if current_section == 'OBJECTIVE_FUNCTION':
                    code_snippets['OBJECTIVE_FUNCTION'] = '\n'.join(current_code).strip()
                elif current_section == 'OPTIMIZATION_ALGORITHM':
                    code_snippets['OPTIMIZATION_ALGORITHM'] = '\n'.join(current_code).strip()
                
                # 开始新函数
                if 'targetfunction' in line or 'objective_function' in line:
                    current_section = 'OBJECTIVE_FUNCTION'
                elif 'solve_optimization' in line:
                    current_section = 'OPTIMIZATION_ALGORITHM'
                current_code = []
                continue
            
            # 收集当前函数的代码
            elif current_section:
                current_code.append(line)
        
        # 保存最后一个函数的代码
        if current_section == 'OBJECTIVE_FUNCTION':
            code_snippets['OBJECTIVE_FUNCTION'] = '\n'.join(current_code).strip()
        elif current_section == 'OPTIMIZATION_ALGORITHM':
            code_snippets['OPTIMIZATION_ALGORITHM'] = '\n'.join(current_code).strip()
        
        return code_snippets 