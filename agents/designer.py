#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Designer智能体
负责根据用户需求生成目标函数代码片段
"""

from .prompt.designer_prompt import Designer_role, Designer_instruction, Designer_example, Network_code

class DesignerAgent:
    """Designer智能体 - 目标函数设计者"""
    
    def __init__(self, llm_client=None):
        """
        初始化Designer智能体
        
        Args:
            llm_client: 大语言模型客户端接口
        """
        self.llm_client = llm_client
        self.prompt_template = Designer_role
        self.designer_examples = Designer_example
        self.network_code = Network_code
        
    def generate_objective_function(self, user_requirements, context=None):
        """
        根据用户需求生成目标函数代码片段
        
        Args:
            user_requirements (str): 用户需求描述
            context (dict): 上下文信息
            
        Returns:
            dict: 生成结果
        """
        print(f"🎨 Designer正在生成目标函数...")
        
        # 构建完整prompt
        prompt = self._build_prompt(user_requirements, context)
        
        if self.llm_client:
            # 调用大模型生成目标函数，使用智能体特定配置
            response = self.llm_client.generate(
                prompt=prompt,
                agent_type="designer"
            )
            return self._parse_design_result(response)
        else:
            # 模拟生成（用于测试）
            return self._mock_generate_objective(user_requirements)
    
    def _build_prompt(self, user_requirements, context):
        """构建完整提示词"""
        # 使用prompt文件中的指令模板
        prompt = Designer_instruction.format(
            user_instruction=user_requirements
        )
        
        # 拼接角色定义、网络代码结构和示例
        full_prompt = self.prompt_template + "\n" + self.network_code + "\n" + self.designer_examples + "\n" + prompt
        
        if context:
            full_prompt += f"\n上下文信息：{context}\n"
        
        return full_prompt
    
    def _extract_code_snippet(self, response_content):
        """从LLM响应中提取代码片段，保留完整格式和缩进"""
        lines = response_content.split('\n')
        code_lines = []
        in_code_block = False
        code_block_started = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # 检测代码块开始和结束
            if stripped_line.startswith('```'):
                if not in_code_block:
                    # 代码块开始
                    in_code_block = True
                    code_block_started = True
                else:
                    # 代码块结束
                    in_code_block = False
                continue
            
            # 如果在代码块内，保留原始行（包括缩进）
            if in_code_block:
                code_lines.append(line)
            # 如果不在代码块内，但看起来像代码行，也保留
            elif code_block_started and (stripped_line.startswith('def ') or 
                                       stripped_line.startswith('import ') or
                                       stripped_line.startswith('from ') or
                                       stripped_line.startswith('#') or
                                       stripped_line.startswith('"""') or
                                       stripped_line.startswith("'''") or
                                       line.startswith('    ') or
                                       (stripped_line and '=' in stripped_line) or
                                       (stripped_line and stripped_line.endswith(':'))):
                code_lines.append(line)
        
        # 如果没有找到代码块，尝试提取所有看起来像代码的行
        if not code_lines:
            for line in lines:
                stripped_line = line.strip()
                if (stripped_line.startswith('def ') or 
                    stripped_line.startswith('import ') or
                    stripped_line.startswith('from ') or
                    stripped_line.startswith('#') or
                    stripped_line.startswith('"""') or
                    stripped_line.startswith("'''") or
                    line.startswith('    ') or
                    (stripped_line and '=' in stripped_line) or
                    (stripped_line and stripped_line.endswith(':')) or
                    (stripped_line and stripped_line.startswith('return ')) or
                    (stripped_line and stripped_line.startswith('for ')) or
                    (stripped_line and stripped_line.startswith('if ')) or
                    (stripped_line and stripped_line.startswith('try:')) or
                    (stripped_line and stripped_line.startswith('except')) or
                    (stripped_line and stripped_line.startswith('self.'))):
                    code_lines.append(line)
        
        # 清理代码行：去除首尾空行，但保留内部空行和缩进
        if code_lines:
            # 去除开头的空行
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            
            # 去除结尾的空行
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
        
        extracted_code = '\n'.join(code_lines)
        
        # 调试信息
        print(f"📝 代码提取调试信息:")
        print(f"   - 原始响应行数: {len(lines)}")
        print(f"   - 提取代码行数: {len(code_lines)}")
        print(f"   - 提取代码长度: {len(extracted_code)}字符")
        
        if code_lines:
            print(f"   - 第一行: '{code_lines[0]}'")
            print(f"   - 最后一行: '{code_lines[-1]}'")
            indented_lines = [line for line in code_lines if line.startswith('    ')]
            print(f"   - 有缩进的行数: {len(indented_lines)}")
        
        return extracted_code
    
    def get_design_examples(self):
        """获取设计示例"""
        examples = {
            '系统损耗最小化': {
                'description': '最小化配网系统的有功损耗',
                'code_snippet': '''"""目标函数：最小化系统损耗"""
try:
    # 执行潮流计算
    self.solve('snap', 50, '[0.4]', 1)
    
    # 获取系统损耗
    losses = self.get_system_losses()
    
    if losses == float('inf') or losses > 1000:
        return 1e6  # 异常情况惩罚
    
    return losses

except Exception as e:
    print(f"目标函数计算异常: {e}")
    return 1e6'''
            },
            
            '电压偏差最小化': {
                'description': '最小化母线电压偏差',
                'code_snippet': '''"""目标函数：最小化电压偏差"""
import numpy as np

try:
    # 执行潮流计算
    self.solve('snap', 50, '[0.4]', 1)
    
    # 获取电压信息
    voltages = self.get_bus_voltages()
    
    if len(voltages) == 0:
        return 1e6
    
    # 计算电压偏差（相对于1.0标幺值）
    voltage_deviation = np.sum(np.abs(voltages - 1.0))
    
    # 添加电压越限惩罚
    voltage_penalty = np.sum(np.maximum(0, voltages - 1.05)) * 1000  # 过电压
    voltage_penalty += np.sum(np.maximum(0, 0.95 - voltages)) * 1000  # 欠电压
    
    return voltage_deviation + voltage_penalty

except Exception as e:
    print(f"目标函数计算异常: {e}")
    return 1e6'''
            },
            
            '储能套利收益最大化': {
                'description': '最大化储能峰谷套利收益',
                'code_snippet': '''"""目标函数：最大化储能套利收益"""
import numpy as np

try:
    # 储能时序功率调度（x包含96个时点的功率值）
    peak_price = 0.8  # 峰时电价
    valley_price = 0.3  # 谷时电价
    
    # 简化的峰谷时段（实际应根据电价曲线）
    peak_hours = list(range(8, 12)) + list(range(14, 18)) + list(range(19, 22))  # 峰时段
    valley_hours = list(range(23, 24)) + list(range(0, 7))  # 谷时段
    
    arbitrage_revenue = 0
    
    # 计算套利收益
    for t, power in enumerate(x[:96]):  # 96个时点
        if t in peak_hours and power > 0:  # 峰时放电
            arbitrage_revenue += power * peak_price
        elif t in valley_hours and power < 0:  # 谷时充电
            arbitrage_revenue -= abs(power) * valley_price
    
    # 执行潮流计算验证可行性
    self.solve('daily', 50, '[0.4]', 96)
    
    # 检查电压约束
    voltages = self.get_bus_voltages()
    if len(voltages) > 0:
        voltage_violation = np.sum(np.maximum(0, voltages - 1.05)) + np.sum(np.maximum(0, 0.95 - voltages))
        if voltage_violation > 0:
            return 1e6  # 电压越限惩罚
    
    # 返回负收益用于最小化（最大化收益等价于最小化负收益）
    return -arbitrage_revenue

except Exception as e:
    print(f"目标函数计算异常: {e}")
    return 1e6'''
            }
        }
        
        return examples
    
    def validate_requirements(self, requirements):
        """验证用户需求的完整性"""
        issues = []
        
        if not requirements or len(requirements.strip()) < 10:
            issues.append("需求描述过于简短")
        
        # 检查关键词
        optimization_keywords = ['最小化', '最大化', '优化', '降低', '提高', '减少', '增加']
        has_optimization_goal = any(keyword in requirements for keyword in optimization_keywords)
        
        if not has_optimization_goal:
            issues.append("未明确优化目标")
        
        # 检查是否涉及电力系统
        power_keywords = ['损耗', '电压', '功率', '储能', '负荷', '变压器', '线路']
        has_power_context = any(keyword in requirements for keyword in power_keywords)
        
        if not has_power_context:
            issues.append("缺少电力系统相关内容")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'suggestions': self._get_requirement_suggestions() if issues else []
        }
    
    def _get_requirement_suggestions(self):
        """获取需求改进建议"""
        return [
            "明确优化目标（如：最小化系统损耗、最大化储能收益等）",
            "指定涉及的设备类型（如：储能、负荷、变压器等）",
            "说明约束条件（如：电压限制、功率限制等）",
            "提供具体的量化指标要求"
        ]
    
    def _parse_design_result(self, response_content):
        """
        解析大模型返回的设计结果
        
        Args:
            response_content (str): 大模型返回的内容
            
        Returns:
            dict: 结构化的设计结果
        """
        # 提取代码片段
        code_snippet = self._extract_code_snippet(response_content)
        
        result = {
            'success': True,
            'code_snippet': code_snippet,
            'raw_response': response_content
        }
        
        print(f"✅ Designer生成目标函数成功，代码长度: {len(code_snippet)}字符")
        return result
    
    def _mock_generate_objective(self, user_requirements):
        """
        模拟生成目标函数（用于测试）
        
        Args:
            user_requirements (str): 用户需求
            
        Returns:
            dict: 模拟生成结果
        """
        # 根据用户需求生成模拟代码
        if '储能' in user_requirements or 'storage' in user_requirements.lower():
            mock_code = """# 储能优化目标函数
try:
    # 计算储能充放电功率
    storage_power = sum(x[i] for i in range(len(x)))
    
    # 计算系统损耗
    system_losses = self.get_system_losses()
    
    # 计算电压偏差
    bus_voltages = self.get_bus_voltages()
    voltage_deviation = sum(abs(v - 1.0) for v in bus_voltages)
    
    # 综合目标函数
    objective_value = storage_power + 0.1 * system_losses + 0.5 * voltage_deviation
    
    return objective_value
except Exception as e:
    print(f"目标函数计算出错: {e}")
    return float('inf')"""
        else:
            mock_code = """# 通用优化目标函数
try:
    # 计算目标函数值
    result = sum(x[i]**2 for i in range(len(x)))
    return result
except Exception as e:
    print(f"目标函数计算出错: {e}")
    return float('inf')"""
        
        return {
            'success': True,
            'code_snippet': mock_code,
            'raw_response': f"模拟生成的目标函数代码：\n{mock_code}"
        } 