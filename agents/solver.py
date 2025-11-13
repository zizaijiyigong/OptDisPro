#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求解器智能体
负责根据目标函数生成优化算法代码片段
"""

from .llm_client import LLMClient
from .prompt.solver_prompt import Solver_fitness, Solver_output_instruction, Solver_role, Solver_example, Solver_instruction

class SolverAgent:
    """求解器智能体"""
    
    def __init__(self, llm_client=None):
        """
        初始化求解器智能体
        
        Args:
            llm_client: LLM客户端实例，如果为None则创建新的实例
        """
        self.role = "Solver"
        self.llm_client = llm_client or LLMClient()
        
        # 从prompt文件引用系统提示词
        self.system_prompt = Solver_role
        
        # 从prompt文件引用例子代码
        self.solver_examples = Solver_example

    def generate_optimization_algorithm(self, objective_function_info, context=None):
        """
        根据目标函数生成优化算法代码片段
        
        Args:
            objective_function_info (dict): 目标函数信息
            context (dict): 上下文信息（可选）
            
        Returns:
            dict: 生成结果
        """
        print(f"🔧 Solver正在设计优化算法...")
        
        try:
            # 构建提示词
            prompt = self._build_prompt(objective_function_info, context)
            
            # 调用LLM生成代码，使用智能体特定配置
            response = self.llm_client.generate(
                prompt=prompt,
                agent_type="solver"
            )
            
            if not response:
                return {
                    'success': False,
                    'error': "LLM调用失败",
                    'code_snippet': ''
                }
            
            # 提取代码片段
            code_snippet = self._extract_code_snippet(response)
            
            result = {
                'success': True,
                'code_snippet': code_snippet,
                'objective_info': objective_function_info,
                'context': context,
                'raw_response': response
            }
            
            print(f"✅ Solver生成优化算法成功，代码长度: {len(code_snippet)}字符")
            return result
            
        except Exception as e:
            print(f"❌ Solver生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'code_snippet': ''
            }
    
    def _build_prompt(self, objective_function_info, context):
        """构建完整提示词"""
        # 提取用户指令和目标函数
        user_instruction = ""
        objective_function = ""
        
        if isinstance(objective_function_info, dict):
            if 'code_snippet' in objective_function_info:
                objective_function = objective_function_info['code_snippet']
        user_instruction = context['user_requirements']

        # 使用prompt文件中的指令模板
        prompt = Solver_instruction.format(
            user_instruction=user_instruction,
            objective_function=objective_function,
            code_solver=context['code_solver'] if 'code_solver' in context else '',
            update_info=context['update_info'] if 'update_info' in context else ''
        )
        
        prompt = Solver_role +"\n"+f"\n参考算法示例：\n{self.solver_examples}"+ "\n"+Solver_fitness+"\n"+ Solver_output_instruction + "\n" +prompt

       
        
        return prompt
    
    def _extract_code_snippet(self, response_content):
        """从LLM响应中提取代码片段"""
        # 去除markdown代码块标记
        lines = response_content.strip().split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            elif in_code_block or line.strip():
                code_lines.append(line)
        
        # 如果没有找到代码块，直接使用全部内容
        if not code_lines:
            code_lines = lines
        
        # 移除def语句（如果存在）
        # filtered_lines = []
        # for line in code_lines:
        #     if not line.strip().startswith('def '):
        #         filtered_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def get_algorithm_examples(self):
        """获取算法示例"""
        examples = {
            '粒子群优化(PSO)': {
                'description': '适用于连续变量优化，收敛稳定',
                'code_snippet': '''"""粒子群优化算法"""
import random
import numpy as np

# PSO参数
num_particles = 30
max_iterations = 100
w = 0.7  # 惯性权重
c1 = 1.5  # 个体学习因子
c2 = 1.5  # 社会学习因子

print(f"🔍 开始PSO优化，粒子数: {num_particles}, 最大迭代: {max_iterations}")

# 初始化粒子群
particles = []
velocities = []
best_positions = []
best_values = []

for i in range(num_particles):
    # 随机初始化位置
    position = [random.uniform(bounds[j][0], bounds[j][1]) for j in range(len(bounds))]
    velocity = [0.0] * len(bounds)
    
    particles.append(position)
    velocities.append(velocity)
    
    # 计算初始适应度
    value = self.objective_function(position)
    best_positions.append(position[:])
    best_values.append(value)

# 全局最优
global_best_idx = best_values.index(min(best_values))
global_best_position = best_positions[global_best_idx][:]
global_best_value = best_values[global_best_idx]

print(f"   初始最优值: {global_best_value:.6f}")

# 迭代优化
for iteration in range(max_iterations):
    for i in range(num_particles):
        # 更新速度
        for j in range(len(bounds)):
            r1, r2 = random.random(), random.random()
            velocities[i][j] = (w * velocities[i][j] + 
                              c1 * r1 * (best_positions[i][j] - particles[i][j]) +
                              c2 * r2 * (global_best_position[j] - particles[i][j]))
        
        # 更新位置
        for j in range(len(bounds)):
            particles[i][j] += velocities[i][j]
            # 边界约束
            particles[i][j] = max(bounds[j][0], min(bounds[j][1], particles[i][j]))
        
        # 评估新位置
        value = self.objective_function(particles[i])
        
        # 更新个体最优
        if value < best_values[i]:
            best_positions[i] = particles[i][:]
            best_values[i] = value
            
            # 更新全局最优
            if value < global_best_value:
                global_best_position = particles[i][:]
                global_best_value = value
    
    if iteration % 20 == 0:
        print(f"   迭代 {iteration}: 当前最优值 = {global_best_value:.6f}")

print(f"✅ PSO优化完成，最终最优值: {global_best_value:.6f}")

return global_best_position, global_best_value, {
    'iterations': max_iterations,
    'particles': num_particles,
    'algorithm': 'PSO',
    'final_iteration': iteration + 1
}'''
            },
            
            '差分进化(DE)': {
                'description': '适用于全局优化，鲁棒性强',
                'code_snippet': '''"""差分进化算法"""
import random
import numpy as np

# DE参数
population_size = 40
max_generations = 80
F = 0.5  # 变异因子
CR = 0.7  # 交叉概率

print(f"🔍 开始DE优化，种群大小: {population_size}, 最大代数: {max_generations}")

# 初始化种群
population = []
fitness_values = []

for i in range(population_size):
    individual = [random.uniform(bounds[j][0], bounds[j][1]) for j in range(len(bounds))]
    population.append(individual)
    fitness_values.append(self.objective_function(individual))

# 找到初始最优
best_idx = fitness_values.index(min(fitness_values))
best_individual = population[best_idx][:]
best_fitness = fitness_values[best_idx]

print(f"   初始最优值: {best_fitness:.6f}")

# 进化过程
for generation in range(max_generations):
    new_population = []
    
    for i in range(population_size):
        # 变异操作
        # 随机选择三个不同个体
        candidates = list(range(population_size))
        candidates.remove(i)
        a, b, c = random.sample(candidates, 3)
        
        # 变异向量
        mutant = []
        for j in range(len(bounds)):
            mutant_value = population[a][j] + F * (population[b][j] - population[c][j])
            # 边界处理
            mutant_value = max(bounds[j][0], min(bounds[j][1], mutant_value))
            mutant.append(mutant_value)
        
        # 交叉操作
        trial = []
        for j in range(len(bounds)):
            if random.random() < CR or j == random.randint(0, len(bounds)-1):
                trial.append(mutant[j])
            else:
                trial.append(population[i][j])
        
        # 选择操作
        trial_fitness = self.objective_function(trial)
        if trial_fitness < fitness_values[i]:
            new_population.append(trial)
            fitness_values[i] = trial_fitness
            
            # 更新全局最优
            if trial_fitness < best_fitness:
                best_individual = trial[:]
                best_fitness = trial_fitness
        else:
            new_population.append(population[i])
    
    population = new_population
    
    if generation % 20 == 0:
        print(f"   代数 {generation}: 当前最优值 = {best_fitness:.6f}")

print(f"✅ DE优化完成，最终最优值: {best_fitness:.6f}")

return best_individual, best_fitness, {
    'generations': max_generations,
    'population_size': population_size,
    'algorithm': 'DE',
    'final_generation': generation + 1
}'''
            },
            
            'scipy优化': {
                'description': '适用于光滑函数，收敛快速',
                'code_snippet': '''"""scipy优化算法"""
try:
    from scipy.optimize import minimize, differential_evolution
    scipy_available = True
except ImportError:
    scipy_available = False

if scipy_available:
    print("🔍 使用scipy差分进化算法")
    
    # 定义目标函数包装器
    def objective_wrapper(variables):
        return self.objective_function(variables)
    
    # 执行优化
    result = differential_evolution(
        objective_wrapper,
        bounds,
        seed=42,
        maxiter=100,
        popsize=15,
        tol=1e-6,
        disp=True
    )
    
    best_variables = result.x.tolist()
    best_objective = result.fun
    optimization_info = {
        'algorithm': 'scipy_DE',
        'success': result.success,
        'iterations': result.nit,
        'function_evaluations': result.nfev,
        'message': result.message
    }
    
    print(f"✅ scipy优化完成，成功: {result.success}")
    print(f"   最优值: {best_objective:.6f}")
    print(f"   函数评估次数: {result.nfev}")
    
    return best_variables, best_objective, optimization_info

else:
    print("⚠️ scipy未安装，使用简单网格搜索")
    
    # 简单网格搜索作为后备
    best_variables = None
    best_objective = float('inf')
    
    n_points = 20
    for i in range(n_points):
        variables = []
        for bound in bounds:
            value = bound[0] + (bound[1] - bound[0]) * i / (n_points - 1)
            variables.append(value)
        
        objective_value = self.objective_function(variables)
        if objective_value < best_objective:
            best_objective = objective_value
            best_variables = variables
    
    optimization_info = {
        'algorithm': 'grid_search',
        'grid_points': n_points,
        'success': best_variables is not None
    }
    
    print(f"✅ 网格搜索完成，最优值: {best_objective:.6f}")
    
    return best_variables, best_objective, optimization_info'''
            }
        }
        
        return examples
    