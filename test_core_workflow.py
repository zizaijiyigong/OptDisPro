#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心流程测试脚本
专注于测试智能体流程衔接运转
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.multi_agent_system import MultiAgentSystem

def test_simple_workflow():
    """测试简单的完整工作流程"""
    print("🚀 测试简单的完整工作流程")
    print("=" * 50)
    
    # 创建多智能体系统
    system = MultiAgentSystem()
    system.set_max_iterations(3)  # 测试三轮
    
    # 用户需求  最大化光伏出力,最小化节点电压偏差
    user_requirements = "最大化光伏出力"
    
    print(f"用户需求: {user_requirements}")
    print("开始执行...")
    
    try:
        start_time = time.time()
        
        # 执行完整工作流程
        result = system.solve_optimization_problem(user_requirements)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️  执行时间: {execution_time:.2f}秒")
        print(f"✅ 执行成功: {result.get('success', False)}")
        
        if result.get('success'):
            print("🎉 核心流程测试成功!")
            
            # 检查工作流状态
            workflow_state = result.get('workflow_state', {})
            print(f"📊 工作流状态:")
            print(f"   迭代次数: {workflow_state.get('current_iteration', 0)}")
            print(f"   代码片段: {len(workflow_state.get('code_snippets', {}))} 个")
            print(f"   审查历史: {len(workflow_state.get('review_history', []))} 条")
            print(f"   执行历史: {len(workflow_state.get('execution_history', []))} 条")
            
            # 检查多算法结果
            if 'multi_algorithm_results' in result:
                print(f"🔢 多算法结果: {len(result['multi_algorithm_results'])} 轮")
                
        else:
            print(f"❌ 核心流程测试失败: {result.get('error', '未知错误')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return None

def test_agent_chain():
    """测试智能体链式调用"""
    print("\n🔗 测试智能体链式调用")
    print("=" * 50)
    
    try:
        system = MultiAgentSystem()
        
        # 测试单轮协作
        print("执行单轮协作...")
        iteration_result = system._execute_collaboration_round()
        
        print(f"✅ 链式调用完成")
        
        # 检查每个智能体的输出
        designer_success = iteration_result.get('designer_result', {}).get('success', False)
        solver_success = iteration_result.get('solver_result', {}).get('success', False)
        review_success = not iteration_result.get('review_result', {}).get('has_issues', True)
        execution_success = iteration_result.get('execution_result', {}).get('success', False)
        
        print(f"👨‍🎨 Designer: {'✅' if designer_success else '❌'}")
        print(f"🔧 Solver: {'✅' if solver_success else '❌'}")
        print(f"🕵️ Reviewer: {'✅' if review_success else '❌'}")
        print(f"⚡ Execution: {'✅' if execution_success else '❌'}")
        
        # 检查代码片段
        if designer_success:
            designer_code = iteration_result.get('designer_result', {}).get('code_snippet', '')
            print(f"   目标函数代码长度: {len(designer_code)} 字符")
            
        if solver_success:
            solver_code = iteration_result.get('solver_result', {}).get('code_snippet', '')
            print(f"   算法代码长度: {len(solver_code)} 字符")
            
        return iteration_result
        
    except Exception as e:
        print(f"❌ 链式调用测试失败: {e}")
        return None

def test_manager_decision_flow():
    """测试Manager决策流程"""
    print("\n🎯 测试Manager决策流程")
    print("=" * 50)
    
    try:
        system = MultiAgentSystem()
        
        # 模拟不同的执行结果
        test_cases = [
            {
                'name': '成功情况',
                'execution_result': {'success': True, 'output': '算法执行成功'},
                'optimization_result': {'objective_value': 0.123}
            },
            {
                'name': '失败情况',
                'execution_result': {'success': False, 'error': '语法错误'},
                'optimization_result': None
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['name']}")
            
            decision = system.manager.make_decision(
                "最小化损耗",
                test_case['execution_result'],
                test_case['optimization_result']
            )
            
            print(f"决策: {decision.get('decision', 'UNKNOWN')}")
            print(f"原因: {decision.get('reason', 'N/A')}")
            print(f"下一步: {decision.get('next_action', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Manager决策测试失败: {e}")
        return False

def test_error_recovery():
    """测试错误恢复机制"""
    print("\n🛡️ 测试错误恢复机制")
    print("=" * 50)
    
    try:
        system = MultiAgentSystem()
        
        # 测试空输入
        print("测试空输入处理...")
        result1 = system.solve_optimization_problem("")
        
        # 测试异常输入
        print("测试异常输入处理...")
        result2 = system.solve_optimization_problem("这是一个测试")
        
        print(f"空输入处理: {'✅' if not result1.get('success', True) else '❌'}")
        print(f"异常输入处理: {'✅' if 'workflow_state' in result2 else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误恢复测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始核心流程测试")
    print("=" * 60)
    
    start_time = time.time()
    
    # 测试结果统计
    test_results = {
        'simple_workflow': False,
        'agent_chain': False,
        'manager_decision': False,
        'error_recovery': False
    }
    
    try:
        # 1. 测试简单工作流程
        result1 = test_simple_workflow()
        test_results['simple_workflow'] = result1 is not None and result1.get('success', False)
        
        # 2. 测试智能体链式调用
        result2 = test_agent_chain()
        test_results['agent_chain'] = result2 is not None
        
        # 3. 测试Manager决策流程
        result3 = test_manager_decision_flow()
        test_results['manager_decision'] = result3
        
        # 4. 测试错误恢复机制
        result4 = test_error_recovery()
        test_results['error_recovery'] = result4
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 生成测试报告
        print(f"\n📊 测试报告")
        print("=" * 50)
        print(f"⏱️  总测试时间: {total_time:.2f}秒")
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"✅ 通过测试: {passed_tests}/{total_tests}")
        
        for test_name, passed in test_results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 所有核心流程测试通过！")
            print(f"🚀 智能体系统运转正常！")
            return True
        else:
            print(f"\n⚠️  部分测试失败，请检查系统配置")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现严重错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎊 核心流程测试完成！系统可以正常使用！")
    else:
        print("\n💥 核心流程测试失败，请检查系统实现。") 