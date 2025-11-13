#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多智能体系统
协调各个智能体协作生成和优化代码片段
"""

from .designer import DesignerAgent
from .solver import SolverAgent
from .reviewer import ReviewerAgent
from .reviewer_full import ReviewerFullAgent
from .manager import ManagerAgent
from .code_executor import CodeExecutor
from .llm_client import LLMClient
import time

class MultiAgentSystem:
    """多智能体系统"""
    
    def __init__(self):
        """初始化多智能体系统"""
        # 创建共享的LLM客户端
        self.llm_client = LLMClient()
        
        # 初始化各个智能体，共享LLM客户端
        self.designer = DesignerAgent(llm_client=self.llm_client)
        self.solver = SolverAgent(llm_client=self.llm_client)
        self.reviewer = ReviewerAgent(llm_client=self.llm_client)
        self.reviewer_full = ReviewerFullAgent(llm_client=self.llm_client)
        self.manager = ManagerAgent(llm_client=self.llm_client)
        self.code_executor = CodeExecutor()
        
        # 代码存储字典
        self.codebook = {
            'objective_functions': [],  # 存储历史目标函数代码
            'optimization_algorithms': [],  # 存储历史优化算法代码
            'complete_codes': [],  # 存储历史完整代码
            'corrected_codes': [],  # 存储修正后的代码
            'current': {  # 当前轮次的代码
                'objective_function': None,
                'optimization_algorithm': None,
                'complete_code': None,
                'corrected_code': None
            }
        }
        
        # 工作流状态
        self.workflow_state = {
            'current_iteration': 0,
            'max_iterations': 3,
            'user_requirements': '',
            'code_snippets': {},
            'review_history': [],
            'execution_history': [],
            'correction_history': [],  # 添加修正历史记录
            'final_result': None,
            'multi_algorithm_results': {},  # 存储多种算法的结果
            'termination_reason': None,
            'final_iteration_result': None
        }
        
        print("🤖 多智能体系统初始化完成")
        print(f"   智能体: Designer, Solver, Reviewer, Manager")
        print(f"   基础代码: Network_code.py（固定模板）")
        print(f"   最大迭代次数: {self.workflow_state['max_iterations']}")
        print(f"   支持多种优化算法并行执行")
        print(f"   LLM配置: {self.llm_client.get_model_info()}")
    
    def solve_optimization_problem(self, user_requirements, max_iterations=5):
        """
        解决优化问题的主工作流程
        
        工作流程:
        1. 初次协作: 执行完整的设计-求解-审查-执行流程
        2. Manager驱动循环: 根据Manager决策执行相应操作，直到满足终止条件
        
        Args:
            user_requirements (str): 用户需求描述
            max_iterations (int): 最大迭代次数
            
        Returns:
            dict: 最终结果
        """
        print(f"\n🎯 开始解决优化问题")
        print(f"用户需求: {user_requirements}")
        print(f"最大迭代次数: {max_iterations}")
        
        # 初始化工作流状态
        self._initialize_workflow(user_requirements, max_iterations)
        
        try:
            # 第一步: 执行初次完整协作
            print(f"\n🚀 === 第 1 轮: 初次完整协作 ===")
            current_result = self.execute_single_round_with_full_reviewer(user_requirements)
            self.workflow_state['current_iteration'] = 1
            
            # 第二步: 进入Manager驱动的决策循环
            while self.workflow_state['current_iteration'] < max_iterations:
                print(f"\n🧠 === Manager决策阶段 (轮次 {self.workflow_state['current_iteration']}) ===")
                
                # Manager分析当前结果并做出决策
                manager_decision = self.manager.make_decision(
                    user_instruction=user_requirements,
                    execution_result=current_result.get('execution_result', {}),
                    optimization_result=current_result.get('multi_algorithm_results', {}),
                    error_info=current_result.get('error')
                )
                
                print(f"📋 Manager决策: {manager_decision.get('decision', 'UNKNOWN')}")
                if manager_decision.get('feedback'):
                    print(f"💭 决策反馈: {manager_decision['feedback']}")
                
                # 根据Manager决策执行相应操作
                next_result = self._execute_manager_decision(manager_decision, current_result, user_requirements)
                
                # 检查是否应该终止
                if self._should_terminate(manager_decision, next_result):
                    self._finalize_workflow(manager_decision, next_result)
                    break
                
                # 更新当前结果，准备下一轮决策
                current_result = next_result
                self.workflow_state['current_iteration'] += 1
                
            else:
                # 达到最大迭代次数
                print(f"\n⏰ 达到最大迭代次数 ({max_iterations})，终止流程")
                self._finalize_workflow({'decision': 'TERMINATE_MAX_ITERATIONS'}, current_result)
            
            return self._generate_final_result()
            
        except Exception as e:
            print(f"❌ 工作流程出现异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"工作流程异常: {e}",
                'workflow_state': self.workflow_state
            }
    
    def _execute_manager_decision(self, manager_decision, current_result, user_requirements):
        """
        执行Manager的决策
        
        Args:
            manager_decision (dict): Manager的决策
            current_result (dict): 当前执行结果
            user_requirements (str): 用户需求
            
        Returns:
            dict: 执行决策后的结果
        """
        decision_type = manager_decision.get('decision', '')
        
        print(f"\n🎯 执行Manager决策: {decision_type}")
        
        if decision_type == 'NEED_CORRECTION':
            # 需要修正代码
            return self._execute_correction_with_reviewer_full(manager_decision, current_result)
            
        elif decision_type == 'UPDATE_SOLVER':
            # 需要更新求解器
            return self._regenerate_solver_code(manager_decision)
            
        elif decision_type in ['TERMINATE_SUCCESS', 'TERMINATE_FAILURE']:
            # 终止决策，返回当前结果
            return current_result
            
        else:
            # 未知决策类型，返回当前结果并记录警告
            print(f"⚠️ 未知的Manager决策类型: {decision_type}")
            return current_result
    
    def _should_terminate(self, manager_decision, execution_result):
        """
        判断是否应该终止工作流程
        
        Args:
            manager_decision (dict): Manager的决策
            execution_result (dict): 执行结果
            
        Returns:
            bool: 是否应该终止
        """
        decision_type = manager_decision.get('decision', '')
        
        # 明确的终止决策
        if decision_type in ['TERMINATE_SUCCESS', 'TERMINATE_FAILURE']:
            return True
        
        # 如果执行成功且Manager未要求继续修正，则终止
        if execution_result.get('success') and decision_type not in ['NEED_CORRECTION', 'UPDATE_SOLVER']:
            print(f"✅ 执行成功，自动终止")
            return True
        
        return False
    
    def _finalize_workflow(self, final_decision, final_result):
        """
        完成工作流程的最终化设置
        
        Args:
            final_decision (dict): 最终的Manager决策
            final_result (dict): 最终执行结果
        """
        self.workflow_state['termination_reason'] = final_decision.get('decision', 'UNKNOWN')
        self.workflow_state['final_iteration_result'] = final_result
        
        termination_reason = self.workflow_state['termination_reason']
        
        if termination_reason == 'TERMINATE_SUCCESS':
            print(f"🎉 工作流程成功完成!")
        elif termination_reason == 'TERMINATE_FAILURE':
            print(f"❌ 工作流程失败终止")
        elif termination_reason == 'TERMINATE_MAX_ITERATIONS':
            print(f"⏰ 达到最大迭代次数终止")
        else:
            print(f"🔚 工作流程终止，原因: {termination_reason}")
    
    def _generate_final_result(self):
        """
        生成最终结果
        
        Returns:
            dict: 最终结果
        """
        final_result = self.workflow_state.get('final_iteration_result', {})
        termination_reason = self.workflow_state.get('termination_reason', 'UNKNOWN')
        
        # 判断最终成功状态
        final_success = (
            termination_reason == 'TERMINATE_SUCCESS' or 
            (final_result.get('success') and termination_reason != 'TERMINATE_FAILURE')
        )
        
        result = {
            'success': final_success,
            'termination_reason': termination_reason,
            'total_iterations': self.workflow_state['current_iteration'],
            'final_execution_result': final_result.get('execution_result'),
            'final_complete_code': (
                final_result.get('corrected_complete_code') or 
                final_result.get('complete_code') or 
                final_result.get('initial_complete_code')
            ),
            'workflow_state': self.workflow_state,
            'codebook_summary': self.get_codebook_summary()
        }
        
        # 添加错误信息（如果有）
        if not final_success and final_result.get('error'):
            result['error'] = final_result['error']
        
        print(f"\n📊 最终结果:")
        print(f"   成功状态: {'✅' if final_success else '❌'}")
        print(f"   终止原因: {termination_reason}")
        print(f"   总迭代次数: {self.workflow_state['current_iteration']}")
        if result.get('error'):
            print(f"   错误信息: {result['error']}")
        
        # 打印codebook状态
        self.print_codebook_status()
        
        return result
    
    def _initialize_workflow(self, user_requirements, max_iterations):
        """初始化工作流状态"""
        self.code_executor.set_base_code_template()
        self.workflow_state['user_requirements'] = user_requirements
        self.workflow_state['current_iteration'] = 0
        self.workflow_state['max_iterations'] = max_iterations
    

    
    def _execute_correction_with_reviewer_full(self, manager_decision, iteration_result):
        """
        使用ReviewerFullAgent执行修正流程
        
        Args:
            manager_decision (dict): Manager的决策结果
            iteration_result (dict): 上一轮的执行结果
            
        Returns:
            dict: 修正后的执行结果
        """
        print(f"\n🔧 使用ReviewerFullAgent执行修正流程...")
        
        # 获取Manager的反馈建议
        feedback = manager_decision.get('feedback', '')
        print(f"📝 Manager反馈: {feedback}")
        
        # 获取错误日志
        error_log = self._prepare_error_log(manager_decision, iteration_result)
        
        try:
            # 获取需要修正的完整代码
            complete_code_to_correct = None
            
            # 优先使用当前轮次生成的完整代码
            if iteration_result.get('corrected_complete_code'):
                complete_code_to_correct = iteration_result['corrected_complete_code']
                print(f"📄 使用当前轮次的修正代码作为基础")
            elif iteration_result.get('initial_complete_code'):
                complete_code_to_correct = iteration_result['initial_complete_code']
                print(f"📄 使用当前轮次的初始代码作为基础")
            elif self.codebook['current']['complete_code']:
                complete_code_to_correct = self.codebook['current']['complete_code']
                print(f"📄 使用codebook中的当前完整代码作为基础")
            else:
                return {
                    'success': False,
                    'error': '找不到可修正的完整代码'
                }
            
            # 准备ReviewerFullAgent的上下文，包含历史信息
            user_requirements = self.workflow_state.get('user_requirements', '')
            
            
            # 使用ReviewerFullAgent进行修正
            print(f"\n🕵️ ReviewerFullAgent修正代码...")
            review_result = self.reviewer_full.review_complete_code(
                complete_code=complete_code_to_correct,
                user_instruction=user_requirements,
                error_log=error_log
            )
            
            print(f"📊 修正状态: {review_result['status']}")
            if review_result.get('analysis'):
                print(f"📝 分析结果: {review_result['analysis']}")
            
            # 处理修正结果
            if review_result['status'] == 'NEEDS_MODIFICATION' and review_result.get('corrected_complete_code'):
                corrected_code = review_result['corrected_complete_code']
                
                # 存储修正后的代码到 codebook
                self.codebook['current']['corrected_code'] = corrected_code
                self.codebook['corrected_codes'].append({
                    'iteration': self.workflow_state['current_iteration'] + 1,
                    'code': corrected_code,
                    'timestamp': time.time(),
                    'manager_feedback': feedback,
                    'error_log': error_log,
                    'correction_type': 'reviewer_full'
                })
                
                print(f"🔧 代码修正完成，已存储到 codebook")
                
                # 显示发现的问题
                if review_result.get('issues'):
                    print(f"❌ 发现的问题:")
                    for issue in review_result['issues']:
                        print(f"   - {issue}")
                
                # 显示修改建议
                if review_result.get('suggestions'):
                    print(f"💡 修改建议:")
                    for suggestion in review_result['suggestions']:
                        print(f"   - {suggestion}")
                
                # 保存并执行修正后的代码
                output_file = "corrected_optimization.py"
                print(f"\n💾 保存修正后的代码到: {output_file}")
                
                if self.code_executor.code_template.save_complete_code(corrected_code, output_file):
                    print(f"✅ 修正代码保存成功")
                    
                    # 执行修正后的代码
                    print(f"\n🚀 执行修正后的代码...")
                    execution_result = self.code_executor.execute_file(output_file)
                    
                    if execution_result['success']:
                        print(f"✅ 修正代码执行成功!")
                        return {
                            'success': True,
                            'review_result': review_result,
                            'corrected_complete_code': corrected_code,
                            'execution_result': execution_result,
                            'corrected': True
                        }
                    else:
                        print(f"❌ 修正代码执行失败: {execution_result.get('error', 'Unknown error')}")
                        return {
                            'success': False,
                            'error': f"修正代码执行失败: {execution_result.get('error', 'Unknown error')}",
                            'review_result': review_result,
                            'corrected_complete_code': corrected_code,
                            'execution_result': execution_result,
                            'corrected': True
                        }
                else:
                    return {
                        'success': False,
                        'error': "修正代码保存失败"
                    }
                    
            elif review_result['status'] == 'PASS':
                print(f"✅ 代码审查通过，无需修正")
                
                # 重新执行原代码以确认
                output_file = "reconfirmed_optimization.py"
                if self.code_executor.code_template.save_complete_code(complete_code_to_correct, output_file):
                    execution_result = self.code_executor.execute_file(output_file)
                    
                    return {
                        'success': execution_result['success'],
                        'review_result': review_result,
                        'corrected_complete_code': complete_code_to_correct,
                        'execution_result': execution_result,
                        'corrected': False
                    }
                else:
                    return {
                        'success': False,
                        'error': "重新确认代码保存失败"
                    }
            else:
                return {
                    'success': False,
                    'error': f"修正流程失败: {review_result.get('status', 'Unknown status')}",
                    'review_result': review_result
                }
                
        except Exception as e:
            print(f"❌ 修正流程出现异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"修正流程异常: {e}"
            }
    
    def _regenerate_solver_code(self, manager_decision):
        """
        重新生成求解器代码
        
        Args:
            manager_decision (dict): Manager的决策结果
            
        Returns:
            dict: 执行结果
        """
        print(f"\n🔄 重新生成求解器代码...")
        
        # 获取Manager的反馈建议
        feedback = manager_decision.get('feedback', '')
        print(f"📝 Manager反馈: {feedback}")
        
        # 获取用户原始需求
        user_requirements = self.workflow_state.get('user_requirements', '')
        
        try:
            # 准备Solver上下文，包含历史代码信息
            solver_context = {
                'user_requirements': user_requirements,
                'manager_feedback': feedback,
                'regeneration': True,
                'iteration': self.workflow_state['current_iteration'] + 1
            }
            
            # 提供历史优化算法代码作为参考
            if self.codebook['optimization_algorithms']:
                solver_context['previous_algorithms'] = self.codebook['optimization_algorithms']
                print(f"📚 提供 {len(self.codebook['optimization_algorithms'])} 个历史优化算法作为参考")
            
            # 提供当前的目标函数代码
            if self.codebook['current']['objective_function']:
                solver_context['current_objective_function'] = self.codebook['current']['objective_function']
                print(f"📋 提供当前目标函数代码作为参考")
            
            # 提供历史完整代码作为参考
            if self.codebook['complete_codes']:
                solver_context['previous_complete_codes'] = self.codebook['complete_codes']
                print(f"📚 提供 {len(self.codebook['complete_codes'])} 个历史完整代码作为参考")
            
            # 构建包含目标函数的Designer结果（模拟）
            designer_result = {
                'success': True,
                'code_snippet': self.codebook['current']['objective_function'],
                'analysis': 'Using current objective function for solver regeneration'
            }
            
            # 重新生成Solver代码
            print(f"\n🔧 Solver重新设计优化算法...")
            solver_result = self.solver.generate_optimization_algorithm(
                designer_result,
                context=solver_context
            )
            
            if not solver_result['success']:
                return {
                    'success': False,
                    'error': f"Solver重新生成失败: {solver_result['error']}"
                }
            
            # 存储新的优化算法代码到 codebook
            new_optimization_algorithm = solver_result['code_snippet']
            self.codebook['current']['optimization_algorithm'] = new_optimization_algorithm
            self.codebook['optimization_algorithms'].append({
                'iteration': self.workflow_state['current_iteration'] + 1,
                'code': new_optimization_algorithm,
                'timestamp': time.time(),
                'regenerated': True,
                'manager_feedback': feedback
            })
            
            print(f"✅ 新的优化算法生成成功，已存储到 codebook")
            
            # 拼接新的完整代码
            print(f"\n🔗 拼接新的完整代码...")
            code_snippets = {
                'OBJECTIVE_FUNCTION': self.codebook['current']['objective_function'],
                'OPTIMIZATION_ALGORITHM': new_optimization_algorithm
            }
            
            new_complete_code = self.code_executor.code_template.insert_code_snippets_robust(code_snippets)
            
            # 存储新的完整代码到 codebook
            self.codebook['current']['complete_code'] = new_complete_code
            self.codebook['complete_codes'].append({
                'iteration': self.workflow_state['current_iteration'] + 1,
                'code': new_complete_code,
                'timestamp': time.time(),
                'regenerated': True,
                'manager_feedback': feedback
            })
            
            print(f"✅ 新的完整代码拼接成功，已存储到 codebook")
            
            # 保存并执行新代码
            output_file = "regenerated_optimization.py"
            print(f"\n💾 保存新代码到: {output_file}")
            
            if self.code_executor.code_template.save_complete_code(new_complete_code, output_file):
                print(f"✅ 新代码保存成功")
                
                # 执行新代码
                print(f"\n🚀 执行新的优化代码...")
                execution_result = self.code_executor.execute_file(output_file)
                
                if execution_result['success']:
                    print(f"✅ 新代码执行成功!")
                    return {
                        'success': True,
                        'solver_result': solver_result,
                        'complete_code': new_complete_code,
                        'execution_result': execution_result,
                        'regenerated': True
                    }
                else:
                    print(f"❌ 新代码执行失败: {execution_result.get('error', 'Unknown error')}")
                    return {
                        'success': False,
                        'error': f"新代码执行失败: {execution_result.get('error', 'Unknown error')}",
                        'solver_result': solver_result,
                        'complete_code': new_complete_code,
                        'execution_result': execution_result,
                        'regenerated': True
                    }
            else:
                return {
                    'success': False,
                    'error': "新代码保存失败"
                }
                
        except Exception as e:
            print(f"❌ 重新生成求解器代码出现异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"重新生成异常: {e}"
            }
    
    def _prepare_error_log(self, manager_decision, iteration_result):
        """准备错误日志"""
        execution_result = iteration_result.get('execution_result', {})
        return f"""
Manager反馈: {manager_decision.get('feedback', '')}
执行输出: {execution_result.get('output', '')}
执行错误: {execution_result.get('error', '')}
        """.strip()
    
    def _create_error_result(self, error_message):
        """创建错误结果"""
        return {
            'success': False,
            'error': error_message,
            'workflow_state': self.workflow_state
        }
    
    def _execute_collaboration_round(self):
        """执行单轮协作 - 包含代码生成、审查、拼接和执行"""
        iteration = self.workflow_state['current_iteration'] + 1
        print(f"   第 {iteration} 轮协作...")
        
        round_result = {
            'iteration': iteration,
            'designer_result': None,
            'solver_result': None,
            'review_result': None,
            'execution_result': None,
            'multi_algorithm_results': {},
            'success': False
        }
        
        try:
            # 1. Designer生成目标函数
            print(f"   👨‍🎨 Designer设计目标函数...")
            designer_result = self.designer.generate_objective_function(
                self.workflow_state['user_requirements'],
                context={
                    'iteration': iteration,
                    'target_method': 'network.targetfunction'
                }
            )
            round_result['designer_result'] = designer_result
            
            if not designer_result['success']:
                round_result['error'] = f"Designer失败: {designer_result['error']}"
                return round_result
            
            # 2. Solver生成多种优化算法
            print(f"   🔧 Solver设计多种优化算法...")
            solver_result = self.solver.generate_optimization_algorithm(
                designer_result,
                context={
                    'user_requirements': self.workflow_state['user_requirements'],
                }
            )
            round_result['solver_result'] = solver_result
            
            if not solver_result['success']:
                round_result['error'] = f"Solver失败: {solver_result['error']}"
                return round_result
            
            # 3. 准备代码片段
            code_snippets = {
                'OBJECTIVE_FUNCTION': designer_result['code_snippet'],
                'OPTIMIZATION_ALGORITHM': solver_result['code_snippet']
            }
            
            # 4. Reviewer代码审查
            print(f"   🕵️ Reviewer审查代码...")
            review_result = self.reviewer.review_code_snippets(
                code_snippets,
                context={
                    'user_requirements': self.workflow_state['user_requirements']
                }
            )
            round_result['review_result'] = review_result
            
            # 5. 应用审查建议（如果有）
            if review_result['status'] == 'NEEDS_MODIFICATION' and review_result.get('corrected_code'):
                print(f"   🔨 应用审查建议...")
                corrected_code = review_result['corrected_code']
                
                # 应用修正后的代码片段
                for snippet_type, corrected_snippet in corrected_code.items():
                    if snippet_type in code_snippets and corrected_snippet:
                        # 检查代码是否真的被修改了
                        original_snippet = code_snippets[snippet_type]
                        if corrected_snippet != original_snippet:
                            code_snippets[snippet_type] = corrected_snippet
                            print(f"     已修复: {snippet_type}")
                        else:
                            print(f"     无需修改: {snippet_type}")
                    elif snippet_type in code_snippets:
                        print(f"     跳过空修正: {snippet_type}")
            
            # 6. 使用重构后的鲁棒方法拼接代码
            print(f"   🔗 使用鲁棒方法拼接代码...")
            try:
                complete_code = self.code_executor.code_template.insert_code_snippets_robust(code_snippets)
                print(f"   ✅ 代码拼接成功")
            except Exception as e:
                print(f"   ❌ 代码拼接失败: {e}")
                round_result['error'] = f"代码拼接失败: {e}"
                return round_result
            
            # 7. 保存并执行代码
            output_file = f"generated_optimization_{iteration}.py"
            if self.code_executor.code_template.save_complete_code(complete_code, output_file):
                print(f"   💾 代码已保存到: {output_file}")
                
                # 执行代码
                print(f"   🚀 执行优化代码...")
                execution_result = self.code_executor.execute_code(complete_code)
                round_result['execution_result'] = execution_result
                
                if execution_result['success']:
                    print(f"   ✅ 代码执行成功!")
                    
                    # 解析多算法结果
                    if execution_result.get('output'):
                        multi_algorithm_results = self._parse_multi_algorithm_results(execution_result['output'])
                        round_result['multi_algorithm_results'] = multi_algorithm_results
                        print(f"   📊 解析到 {len(multi_algorithm_results)} 个算法结果")
                    
                    # 记录到工作流历史
                    self.workflow_state['execution_history'].append(execution_result)
                    self.workflow_state['review_history'].append(review_result)
                    
                    round_result['success'] = True
                    return round_result
                else:
                    print(f"   ❌ 代码执行失败: {execution_result.get('error', 'Unknown error')}")
                    round_result['error'] = f"代码执行失败: {execution_result.get('error', 'Unknown error')}"
                    return round_result
            else:
                print(f"   ❌ 代码保存失败")
                round_result['error'] = "代码保存失败"
                return round_result
                
        except Exception as e:
            print(f"   ❌ 协作轮次出现异常: {e}")
            import traceback
            traceback.print_exc()
            round_result['error'] = f"协作轮次异常: {e}"
            return round_result
    
    def _parse_multi_algorithm_results(self, output_text):
        """解析多种算法的执行结果"""
        results = {
            'algorithms': {},
            'best_algorithm': None,
            'best_objective': float('inf'),
            'successful_count': 0,
            'total_count': 0
        }
        
        try:
            lines = output_text.split('\n')
            current_algorithm = None
            
            for line in lines:
                line = line.strip()
                
                # 检测算法开始
                if '开始' in line and any(alg in line for alg in ['PSO', 'DE', 'GA', 'SA', 'ACO']):
                    for alg in ['PSO', 'DE', 'GA', 'SA', 'ACO']:
                        if alg in line:
                            current_algorithm = alg
                            results['algorithms'][alg] = {'status': 'running'}
                            results['total_count'] += 1
                            break
                
                # 检测算法完成
                elif current_algorithm and '完成' in line and current_algorithm in line:
                    if '最终最优值' in line:
                        try:
                            # 提取目标函数值
                            import re
                            match = re.search(r'最终最优值:\s*([\d.-]+)', line)
                            if match:
                                objective_value = float(match.group(1))
                                results['algorithms'][current_algorithm] = {
                                    'status': 'success',
                                    'objective_value': objective_value
                                }
                                results['successful_count'] += 1
                                
                                # 更新最优算法
                                if objective_value < results['best_objective']:
                                    results['best_objective'] = objective_value
                                    results['best_algorithm'] = current_algorithm
                        except:
                            results['algorithms'][current_algorithm] = {'status': 'failed', 'error': '解析失败'}
                
                # 检测算法失败
                elif current_algorithm and '执行失败' in line:
                    results['algorithms'][current_algorithm] = {'status': 'failed', 'error': line}
            
            # 如果没有解析到结果，使用默认值
            if results['total_count'] == 0:
                results['algorithms'] = {'default': {'status': 'success', 'objective_value': 0.0}}
                results['best_algorithm'] = 'default'
                results['best_objective'] = 0.0
                results['successful_count'] = 1
                results['total_count'] = 1
            
        except Exception as e:
            print(f"⚠️ 解析多算法结果失败: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_multi_algorithm_results(self):
        """分析多种算法的结果"""
        if not self.workflow_state['multi_algorithm_results']:
            return {}
        
        # 合并所有迭代的算法结果
        all_algorithms = {}
        best_overall_algorithm = None
        best_overall_objective = float('inf')
        total_successful = 0
        total_attempts = 0
        
        for iteration, results in self.workflow_state['multi_algorithm_results'].items():
            for alg_name, alg_result in results.get('algorithms', {}).items():
                if alg_name not in all_algorithms:
                    all_algorithms[alg_name] = {
                        'success_count': 0,
                        'total_count': 0,
                        'best_objective': float('inf'),
                        'iterations': []
                    }
                
                all_algorithms[alg_name]['total_count'] += 1
                total_attempts += 1
                
                if alg_result.get('status') == 'success':
                    all_algorithms[alg_name]['success_count'] += 1
                    total_successful += 1
                    objective_value = alg_result.get('objective_value', float('inf'))
                    all_algorithms[alg_name]['iterations'].append({
                        'iteration': iteration,
                        'objective_value': objective_value
                    })
                    
                    # 更新该算法的最优结果
                    if objective_value < all_algorithms[alg_name]['best_objective']:
                        all_algorithms[alg_name]['best_objective'] = objective_value
                    
                    # 更新全局最优算法
                    if objective_value < best_overall_objective:
                        best_overall_objective = objective_value
                        best_overall_algorithm = alg_name
        
        return {
            'algorithms': all_algorithms,
            'best_algorithm': best_overall_algorithm,
            'best_objective': best_overall_objective if best_overall_objective != float('inf') else None,
            'successful_count': total_successful,
            'total_count': total_attempts,
            'success_rate': total_successful / total_attempts if total_attempts > 0 else 0
        }
    
    def _get_workflow_summary(self):
        """获取工作流摘要"""
        summary = {
            'total_iterations': self.workflow_state['current_iteration'] + 1,
            'max_iterations': self.workflow_state['max_iterations'],
            'successful_executions': len([
                exec_result for exec_result in self.workflow_state['execution_history']
                if exec_result.get('success', False)
            ]),
            'total_reviews': len(self.workflow_state['review_history']),
            'issues_found': sum(len(review.get('issues', [])) for review in self.workflow_state['review_history']),
            'improvements_made': sum(1 for review in self.workflow_state['review_history'] 
                                   if review.get('status') == 'NEEDS_MODIFICATION' and review.get('corrected_code'))
        }
        
        return summary
    
    def get_agent_status(self):
        """获取所有智能体的状态"""
        return {
            'designer': self.designer is not None,
            'solver': self.solver is not None,
            'reviewer': self.reviewer is not None,
            'reviewer_full': self.reviewer_full is not None,
            'manager': self.manager is not None,
            'code_executor': self.code_executor is not None
        }
    
    def get_codebook_summary(self):
        """获取codebook的摘要信息"""
        summary = {
            'objective_functions_count': len(self.codebook['objective_functions']),
            'optimization_algorithms_count': len(self.codebook['optimization_algorithms']),
            'complete_codes_count': len(self.codebook['complete_codes']),
            'corrected_codes_count': len(self.codebook['corrected_codes']),
            'current_codes': {
                'has_objective_function': self.codebook['current']['objective_function'] is not None,
                'has_optimization_algorithm': self.codebook['current']['optimization_algorithm'] is not None,
                'has_complete_code': self.codebook['current']['complete_code'] is not None,
                'has_corrected_code': self.codebook['current']['corrected_code'] is not None
            }
        }
        return summary
    
    def print_codebook_status(self):
        """打印codebook状态信息"""
        summary = self.get_codebook_summary()
        print(f"\n📚 Codebook 状态:")
        print(f"   目标函数历史: {summary['objective_functions_count']} 个")
        print(f"   优化算法历史: {summary['optimization_algorithms_count']} 个")
        print(f"   完整代码历史: {summary['complete_codes_count']} 个")
        print(f"   修正代码历史: {summary['corrected_codes_count']} 个")
        print(f"   当前代码状态:")
        print(f"     目标函数: {'✅' if summary['current_codes']['has_objective_function'] else '❌'}")
        print(f"     优化算法: {'✅' if summary['current_codes']['has_optimization_algorithm'] else '❌'}")
        print(f"     完整代码: {'✅' if summary['current_codes']['has_complete_code'] else '❌'}")
        print(f"     修正代码: {'✅' if summary['current_codes']['has_corrected_code'] else '❌'}")
    
    def export_codebook(self, filename=None):
        """导出codebook到文件"""
        if not filename:
            import time
            timestamp = int(time.time())
            filename = f"codebook_export_{timestamp}.json"
        
        try:
            import json
            
            # 准备导出数据（不包含代码内容，只包含元数据）
            export_data = {
                'summary': self.get_codebook_summary(),
                'objective_functions': [
                    {
                        'iteration': item['iteration'],
                        'timestamp': item['timestamp'],
                        'code_length': len(item['code']),
                        'regenerated': item.get('regenerated', False)
                    }
                    for item in self.codebook['objective_functions']
                ],
                'optimization_algorithms': [
                    {
                        'iteration': item['iteration'],
                        'timestamp': item['timestamp'],
                        'code_length': len(item['code']),
                        'regenerated': item.get('regenerated', False),
                        'manager_feedback': item.get('manager_feedback', '')
                    }
                    for item in self.codebook['optimization_algorithms']
                ],
                'complete_codes': [
                    {
                        'iteration': item['iteration'],
                        'timestamp': item['timestamp'],
                        'code_length': len(item['code']),
                        'regenerated': item.get('regenerated', False),
                        'manager_feedback': item.get('manager_feedback', '')
                    }
                    for item in self.codebook['complete_codes']
                ],
                'corrected_codes': [
                    {
                        'iteration': item['iteration'],
                        'timestamp': item['timestamp'],
                        'code_length': len(item['code']),
                        'manager_feedback': item.get('manager_feedback', ''),
                        'correction_type': item.get('correction_type', 'unknown')
                    }
                    for item in self.codebook['corrected_codes']
                ],
                'export_timestamp': time.time()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"📄 Codebook已导出: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 导出Codebook失败: {e}")
            return None
    
    def clear_codebook_history(self, keep_current=True):
        """清理codebook历史记录"""
        if keep_current:
            # 只清理历史记录，保留当前代码
            self.codebook['objective_functions'] = []
            self.codebook['optimization_algorithms'] = []
            self.codebook['complete_codes'] = []
            self.codebook['corrected_codes'] = []
            print(f"🧹 Codebook历史记录已清理，保留当前代码")
        else:
            # 清理所有记录
            self.codebook = {
                'objective_functions': [],
                'optimization_algorithms': [],
                'complete_codes': [],
                'corrected_codes': [],
                'current': {
                    'objective_function': None,
                    'optimization_algorithm': None,
                    'complete_code': None,
                    'corrected_code': None
                }
            }
            print(f"🧹 Codebook已完全清理")
    
    def get_latest_codes(self):
        """获取最新的代码"""
        return {
            'objective_function': self.codebook['current']['objective_function'],
            'optimization_algorithm': self.codebook['current']['optimization_algorithm'],
            'complete_code': self.codebook['current']['complete_code'],
            'corrected_code': self.codebook['current']['corrected_code']
        }
    
    def cleanup(self):
        """清理系统资源"""
        print("\n🧹 清理多智能体系统...")
        
        try:
            # 清理代码执行器的临时文件
            self.code_executor.cleanup_temp_files()
            
            # 重置工作流状态
            self.workflow_state = {
                'current_iteration': 0,
                'max_iterations': 3,
                'user_requirements': '',
                'code_snippets': {},
                'review_history': [],
                'execution_history': [],
                'correction_history': [],  # 添加修正历史记录
                'final_result': None,
                'multi_algorithm_results': {},
                'termination_reason': None,
                'final_iteration_result': None
            }
            
            print("✅ 系统清理完成")
            
        except Exception as e:
            print(f"⚠️ 清理过程出现问题: {e}")
    
    def set_max_iterations(self, max_iterations):
        """设置最大迭代次数"""
        self.workflow_state['max_iterations'] = max_iterations
        print(f"📝 最大迭代次数设置为: {max_iterations}")
        
    
    
    def execute_single_round_with_full_reviewer(self, user_requirements):
        """
        使用ReviewerFullAgent执行单轮协作
        
        流程:
        1. Designer生成目标函数
        2. Solver生成优化算法
        3. 代码拼接成完整代码
        4. ReviewerFullAgent审查完整代码并返回修正后的完整代码
        5. 执行代码并返回结果（由外层Manager进行下一步判断）
        
        Args:
            user_requirements (str): 用户需求描述
            
        Returns:
            dict: 执行结果，包含success字段和详细信息
        """
        print(f"\n🚀 使用ReviewerFullAgent执行单轮协作")
        print(f"用户需求: {user_requirements}")
        
        result = {
            'success': False,
            'designer_result': None,
            'solver_result': None,
            'initial_complete_code': None,
            'review_result': None,
            'corrected_complete_code': None,
            'execution_result': None,
            'error': None
        }
        
        try:
            # 设置基础代码模板
            self.code_executor.set_base_code_template()
            print(f"✅ 已设置基础代码模板: Network_code.py")
            
            # 1. Designer生成目标函数
            print(f"\n👨‍🎨 Designer设计目标函数...")
            designer_context = {
                'iteration': self.workflow_state['current_iteration'] + 1,
                'target_method': 'network.targetfunction'
            }
            
            # 提供历史目标函数代码作为参考
            if self.codebook['objective_functions']:
                designer_context['previous_objective_functions'] = self.codebook['objective_functions']
                print(f"📚 提供 {len(self.codebook['objective_functions'])} 个历史目标函数作为参考")
            
            designer_result = self.designer.generate_objective_function(
                user_requirements,
                context=designer_context
            )
            result['designer_result'] = designer_result
            
            if not designer_result['success']:
                result['error'] = f"Designer失败: {designer_result['error']}"
                return result
            
            # 存储目标函数代码到 codebook
            objective_function_code = designer_result['code_snippet']
            self.codebook['current']['objective_function'] = objective_function_code
            self.codebook['objective_functions'].append({
                'iteration': self.workflow_state['current_iteration'] + 1,
                'code': objective_function_code,
                'timestamp': time.time()
            })
            
            print(f"✅ 目标函数生成成功，已存储到 codebook")
            
            # 2. Solver生成优化算法
            print(f"\n🔧 Solver设计优化算法...")
            solver_context = {
                'user_requirements': user_requirements,
            }
            
            # 提供历史优化算法代码作为参考
            if self.codebook['optimization_algorithms']:
                solver_context['previous_algorithms'] = self.codebook['optimization_algorithms']
                print(f"📚 提供 {len(self.codebook['optimization_algorithms'])} 个历史优化算法作为参考")
            
            solver_result = self.solver.generate_optimization_algorithm(
                designer_result,
                context=solver_context
            )
            result['solver_result'] = solver_result
            
            if not solver_result['success']:
                result['error'] = f"Solver失败: {solver_result['error']}"
                return result
            
            # 存储优化算法代码到 codebook
            optimization_algorithm_code = solver_result['code_snippet']
            self.codebook['current']['optimization_algorithm'] = optimization_algorithm_code
            self.codebook['optimization_algorithms'].append({
                'iteration': self.workflow_state['current_iteration'] + 1,
                'code': optimization_algorithm_code,
                'timestamp': time.time()
            })
            
            print(f"✅ 优化算法生成成功，已存储到 codebook")
            
            # 3. 拼接代码片段生成完整代码
            print(f"\n🔗 拼接代码片段...")
            code_snippets = {
                'OBJECTIVE_FUNCTION': objective_function_code,
                'OPTIMIZATION_ALGORITHM': optimization_algorithm_code
            }
            
            try:
                initial_complete_code = self.code_executor.code_template.insert_code_snippets_robust(code_snippets)
                result['initial_complete_code'] = initial_complete_code
                
                # 存储完整代码到 codebook
                self.codebook['current']['complete_code'] = initial_complete_code
                self.codebook['complete_codes'].append({
                    'iteration': self.workflow_state['current_iteration'] + 1,
                    'code': initial_complete_code,
                    'timestamp': time.time()
                })
                
                print(f"✅ 初始完整代码拼接成功，已存储到 codebook")
            except Exception as e:
                result['error'] = f"代码拼接失败: {e}"
                return result
            
            # 4. 使用ReviewerFullAgent审查完整代码
            print(f"\n🕵️ ReviewerFullAgent审查完整代码...")
            review_result = self.reviewer_full.review_complete_code(
                complete_code=initial_complete_code,
                user_instruction=user_requirements,
                error_log=None
            )
            result['review_result'] = review_result
            
            print(f"📊 审查状态: {review_result['status']}")
            if review_result.get('analysis'):
                print(f"📝 分析结果: {review_result['analysis']}")
            
            # 5. 决定使用哪个代码版本执行
            if review_result['status'] == 'NEEDS_MODIFICATION' and review_result.get('corrected_complete_code'):
                # 使用修正后的完整代码
                final_code = review_result['corrected_complete_code']
                result['corrected_complete_code'] = final_code
                
                # 存储修正后的代码到 codebook
                self.codebook['current']['corrected_code'] = final_code
                self.codebook['corrected_codes'].append({
                    'iteration': self.workflow_state['current_iteration'] + 1,
                    'code': final_code,
                    'timestamp': time.time()
                })
                
                print(f"🔧 使用ReviewerFullAgent修正后的完整代码，已存储到 codebook")
                
                # 显示发现的问题
                if review_result.get('issues'):
                    print(f"❌ 发现的问题:")
                    for issue in review_result['issues']:
                        print(f"   - {issue}")
                
                # 显示修改建议
                if review_result.get('suggestions'):
                    print(f"💡 修改建议:")
                    for suggestion in review_result['suggestions']:
                        print(f"   - {suggestion}")
                        
            elif review_result['status'] == 'PASS':
                # 使用原始代码
                final_code = initial_complete_code
                result['corrected_complete_code'] = final_code
                print(f"✅ 代码审查通过，使用原始代码")
            else:
                # 审查失败，使用原始代码但记录警告
                final_code = initial_complete_code
                result['corrected_complete_code'] = final_code
                print(f"⚠️ 审查未完成，使用原始代码")
            
            # 6. 保存并执行最终代码
            output_file = "generated_optimization_full_review.py"
            print(f"\n💾 保存最终代码到: {output_file}")
            
            if self.code_executor.code_template.save_complete_code(final_code, output_file):
                print(f"✅ 代码保存成功")
                
                # 执行保存的代码文件
                print(f"\n🚀 执行优化代码文件...")
                execution_result = self.code_executor.execute_file(output_file)
                result['execution_result'] = execution_result
                
                if execution_result['success']:
                    print(f"✅ 代码执行成功!")
                    if execution_result.get('output'):
                        print(f"📊 执行输出:")
                        print(execution_result['output'][:500] + "..." if len(execution_result['output']) > 500 else execution_result['output'])
                    
                    result['success'] = True
                    return result
                else:
                    print(f"❌ 代码执行失败: {execution_result.get('error', 'Unknown error')}")
                    result['error'] = f"代码执行失败: {execution_result.get('error', 'Unknown error')}"
                    return result
            else:
                result['error'] = "代码保存失败"
                return result
                
        except Exception as e:
            print(f"❌ 单轮协作出现异常: {e}")
            import traceback
            traceback.print_exc()
            result['error'] = f"单轮协作异常: {e}"
            return result
        
        return result
    
    def get_full_reviewer_status(self):
        """获取ReviewerFullAgent状态"""
        return {
            'reviewer_full': {
                'available': hasattr(self, 'reviewer_full') and self.reviewer_full is not None,
                'llm_client': self.reviewer_full.llm_client is not None if hasattr(self, 'reviewer_full') else False,
                'description': 'ReviewerFullAgent - 审查并返回修正后的完整代码'
            }
        }
    
    # generate_and_execute_code方法已删除，功能整合到_execute_collaboration_round中 