#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manager智能体
负责统筹管理整个优化流程，判断是否终止、修正或继续
"""

from .prompt.manager_prompt import Manager_role

class ManagerAgent:
    """Manager智能体 - 流程管理者"""
    
    def __init__(self, llm_client=None, max_iterations=5):
        """
        初始化Manager智能体
        
        Args:
            llm_client: 大语言模型客户端接口
            max_iterations (int): 最大迭代次数
        """
        self.llm_client = llm_client
        self.prompt_template = Manager_role
        self.max_iterations = max_iterations
        self.iteration_count = 0
        
    def make_decision(self, user_instruction, execution_result, optimization_result=None, error_info=None):
        """
        根据当前状态做出流程决策
        
        Args:
            user_instruction (str): 用户指令
            execution_result (dict): 代码执行结果
            optimization_result (dict): 优化结果
            error_info (str): 错误信息
            
        Returns:
            dict: 决策结果，包含decision字段：
                - 'TERMINATE_SUCCESS': 成功终止
                - 'TERMINATE_FAILURE': 失败终止
                - 'NEED_CORRECTION': 需要修正
                - 'CONTINUE_OPTIMIZATION': 继续优化
        """
        self.iteration_count += 1
        print(f"🎯 Manager正在分析第{self.iteration_count}轮结果...")
        
        # 构造完整prompt
        full_prompt = self.prompt_template.format(
            input=user_instruction,
            result=str(execution_result) + "\n" + str(optimization_result or "无"),
            his_input=f"第{self.iteration_count}轮迭代"
        )
        
        if self.llm_client:
            # 调用大模型做决策，使用智能体特定配置
            decision_result = self.llm_client.generate(
                prompt=full_prompt,
                agent_type="manager"
            )
            return self._parse_decision_result(decision_result)
        else:
            # 模拟决策（用于测试）
            return self._mock_decision(user_instruction, execution_result, optimization_result, error_info)
    
    def _mock_decision(self, user_instruction, execution_result, optimization_result, error_info):
        """
        模拟决策过程（用于测试）
        
        Args:
            user_instruction (str): 用户指令
            execution_result (dict): 执行结果
            optimization_result (dict): 优化结果
            error_info (str): 错误信息
            
        Returns:
            dict: 决策结果
        """
        # 检查是否超过最大迭代次数
        if self.iteration_count >= self.max_iterations:
            print(f"⚠️ 已达到最大迭代次数 ({self.max_iterations})")
            return {
                'decision': 'TERMINATE_FAILURE',
                'reason': f'已达到最大迭代次数 ({self.max_iterations})，无法进一步改进',
                'next_action': '终止优化，报告当前最佳结果',
                'feedback': '由于迭代次数限制，优化过程终止。请检查问题设置或增加迭代次数。'
            }
        
        # 检查是否有严重错误
        if error_info and any(keyword in error_info.lower() 
                             for keyword in ['syntax error', '语法错误', 'import error', 'module not found']):
            print(f"❌ 发现严重错误: {error_info}")
            return {
                'decision': 'NEED_CORRECTION',
                'reason': '代码存在语法错误或导入错误，需要修正',
                'next_action': '调用Reviewer修正代码错误',
                'feedback': f'代码执行出错：{error_info}，正在尝试修正...'
            }
        
        # 检查执行结果
        if not execution_result or not execution_result.get('success', False):
            print(f"⚠️ 执行失败")
            return {
                'decision': 'NEED_CORRECTION',
                'reason': '代码执行失败，可能存在逻辑错误',
                'next_action': '分析错误原因，调用Reviewer修正代码',
                'feedback': '代码执行失败，正在分析问题并尝试修正...'
            }
        
        # 检查多算法结果
        if optimization_result and 'all_algorithm_results' in optimization_result:
            all_results = optimization_result['all_algorithm_results']
            if 'all_results' in all_results:
                successful_algorithms = []
                failed_algorithms = []
                
                for alg_name, alg_result in all_results['all_results'].items():
                    if 'error' not in alg_result:
                        successful_algorithms.append(alg_name)
                    else:
                        failed_algorithms.append(alg_name)
                
                print(f"📊 算法执行情况: 成功{len(successful_algorithms)}个，失败{len(failed_algorithms)}个")
                
                # 如果有成功的算法
                if successful_algorithms:
                    if len(successful_algorithms) >= len(all_results['all_results']) * 0.5:
                        print(f"✅ 大部分算法成功执行，可以终止")
                        return {
                            'decision': 'TERMINATE_SUCCESS',
                            'reason': f'多算法优化成功，{len(successful_algorithms)}/{len(all_results["all_results"])}个算法成功执行',
                            'next_action': '输出所有算法结果给用户',
                            'feedback': f'多算法优化完成！成功算法: {", ".join(successful_algorithms)}'
                        }
                    else:
                        print(f"🔄 部分算法成功，尝试改进")
                        return {
                            'decision': 'CONTINUE_OPTIMIZATION',
                            'reason': '部分算法成功执行，可以尝试改进失败的算法',
                            'next_action': '调整算法参数或尝试其他算法',
                            'feedback': f'部分算法成功，继续优化...'
                        }
                else:
                    print(f"❌ 所有算法都执行失败")
                    if self.iteration_count <= 2:
                        return {
                            'decision': 'CONTINUE_OPTIMIZATION',
                            'reason': '所有算法失败，但可以尝试改进',
                            'next_action': '检查算法实现，调整参数',
                            'feedback': '所有算法失败，正在尝试改进...'
                        }
                    else:
                        return {
                            'decision': 'TERMINATE_FAILURE',
                            'reason': '多次尝试后所有算法仍失败',
                            'next_action': '报告失败结果，建议用户检查问题设置',
                            'feedback': '优化过程遇到困难，可能需要调整问题设置。'
                        }
        
        # 检查优化结果质量
        if optimization_result:
            success = optimization_result.get('success', False)
            objective_value = optimization_result.get('objective_value')
            
            if success and objective_value is not None:
                # 检查结果是否合理
                if objective_value == float('inf') or objective_value == float('-inf'):
                    print(f"⚠️ 优化结果异常: {objective_value}")
                    return {
                        'decision': 'NEED_CORRECTION',
                        'reason': '优化结果异常（无穷大/无穷小），可能存在数值问题',
                        'next_action': '检查目标函数实现，改进数值稳定性',
                        'feedback': '优化结果异常，正在检查和改进算法...'
                    }
                
                # 成功情况
                print(f"✅ 优化成功，目标值: {objective_value}")
                return {
                    'decision': 'TERMINATE_SUCCESS',
                    'reason': f'优化算法收敛，得到合理的目标函数值 {objective_value}',
                    'next_action': '输出最终优化结果给用户',
                    'feedback': f'优化成功完成！根据指令"{user_instruction}"，找到最优解，目标函数值为 {objective_value:.6f}'
                }
            else:
                # 优化未成功但可以尝试改进
                if self.iteration_count <= 2:
                    print(f"🔄 优化未完全成功，尝试改进...")
                    return {
                        'decision': 'CONTINUE_OPTIMIZATION',
                        'reason': '当前优化结果不理想，但可以尝试不同的算法或参数',
                        'next_action': '调整优化算法参数或尝试其他算法',
                        'feedback': '正在尝试改进优化算法...'
                    }
                else:
                    print(f"⚠️ 多次尝试后仍未成功")
                    return {
                        'decision': 'TERMINATE_FAILURE',
                        'reason': '多次尝试后优化仍未成功',
                        'next_action': '报告当前最佳结果，建议用户检查问题设置',
                        'feedback': '优化过程遇到困难，可能需要调整问题设置或约束条件。'
                    }
        
        # 默认情况 - 继续尝试
        return {
            'decision': 'CONTINUE_OPTIMIZATION',
            'reason': '当前状态未明确，继续尝试优化',
            'next_action': '继续执行优化流程',
            'feedback': '正在继续优化过程...'
        }
    
    def _parse_decision_result(self, decision_text):
        """
        解析大模型返回的决策结果
        
        Args:
            decision_text (str): 决策结果文本
            
        Returns:
            dict: 结构化的决策结果
        """
        lines = decision_text.strip().split('\n')
        
        result = {
            'decision': 'CONTINUE_OPTIMIZATION',
            'reason': '',
            'next_action': '',
            'feedback': ''
        }
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('DECISION:'):
                result['decision'] = line.split(':', 1)[1].strip()
            elif line.startswith('REASON:'):
                result['reason'] = line.split(':', 1)[1].strip()
            elif line.startswith('NEXT_ACTION:'):
                result['next_action'] = line.split(':', 1)[1].strip()
            elif line.startswith('FEEDBACK:'):
                result['feedback'] = line.split(':', 1)[1].strip()
        
        return result

    
