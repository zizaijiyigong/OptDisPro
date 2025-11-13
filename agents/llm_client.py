#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大语言模型客户端
基于OpenAI SDK实现，支持多智能体调用
"""

import json
from typing import Optional, Dict, Any

class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, 
                 temperature: float = None, max_tokens: int = None, 
                 top_p: float = None, frequency_penalty: float = None,
                 presence_penalty: float = None):
        """
        初始化LLM客户端
        
        Args:
            api_key (str): API密钥
            base_url (str): API基础URL
            model (str): 模型名称
            temperature (float): 温度参数，控制随机性 (0.0-2.0)
            max_tokens (int): 最大生成token数
            top_p (float): 核采样参数 (0.0-1.0)
            frequency_penalty (float): 频率惩罚 (-2.0-2.0)
            presence_penalty (float): 存在惩罚 (-2.0-2.0)
        """
        # 尝试从配置文件加载
        try:
            from config import LLM_CONFIG
            default_config = LLM_CONFIG
        except ImportError:
            default_config = {
                "api_key": "sk-darst55vahzc2jx5",
                "base_url": "https://cloud.infini-ai.com/maas/v1",
                "model": "qwen2.5-72b-instruct",
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        
        # 配置参数（命令行参数优先级最高）
        self.api_key = api_key or default_config["api_key"]
        self.base_url = base_url or default_config["base_url"]  
        self.model = model or default_config["model"]
        self.temperature = temperature if temperature is not None else default_config.get("temperature", 0.7)
        self.max_tokens = max_tokens if max_tokens is not None else default_config.get("max_tokens", 2000)
        self.top_p = top_p if top_p is not None else default_config.get("top_p", 0.9)
        self.frequency_penalty = frequency_penalty if frequency_penalty is not None else default_config.get("frequency_penalty", 0.0)
        self.presence_penalty = presence_penalty if presence_penalty is not None else default_config.get("presence_penalty", 0.0)
        
        # 智能体特定配置
        self.agent_configs = {
            "designer": {
                "temperature": 0.4,  # 设计器需要更多创造
                "system_prompt": "你是一个专业的电力系统优化目标函数设计专家"
            },
            "solver": {
                "temperature": 0.2
            },
            "reviewer": {
                "temperature": 0.2,  # 审查器需要更严谨
                "system_prompt": "你是一个专业的代码审查专家"
            },
            "manager": {
                "temperature": 0.3,  # 管理者需要平衡创造性和稳定性
                "system_prompt": "你是一个专业的项目管理和决策专家"
            }
        }
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            print(f"✅ LLM客户端初始化成功")
            print(f"   模型: {self.model}")
            print(f"   温度: {self.temperature}")
            print(f"   最大Token: {self.max_tokens}")
            
        except ImportError:
            print("❌ 未安装openai库，请运行: pip install openai")
            self.client = None
        except Exception as e:
            print(f"❌ LLM客户端初始化失败: {e}")
            self.client = None
    
    def generate(self, prompt: str, knowledge: str = None, response_format: str = "text", 
                 agent_type: str = None, custom_config: Dict[str, Any] = None) -> str:
        """
        调用大模型生成内容
        
        Args:
            prompt (str): 输入提示词
            knowledge (str): 额外知识/上下文
            response_format (str): 响应格式 ("text" 或 "json")
            agent_type (str): 智能体类型 ("designer", "solver", "reviewer", "manager")
            custom_config (dict): 自定义配置参数
            
        Returns:
            str: 生成的内容
        """
        if not self.client:
            print("⚠️ LLM客户端未初始化，使用模拟响应")
            return self._mock_response(prompt, agent_type)
        
        # 获取配置参数
        config = self._get_config_for_agent(agent_type, custom_config)
        
        # 构建完整提示词
        full_prompt = prompt
        if knowledge:
            full_prompt += "\n\n# 参考信息：\n" + knowledge
        
        try:
            # 准备请求参数
            messages = []
            
            # 添加系统提示词（如果有）
            if config.get("system_prompt"):
                messages.append({
                    "role": "system",
                    "content": config["system_prompt"]
                })
            
            messages.append({
                "role": "user", 
                "content": full_prompt
            })
            
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"],
                "top_p": config.get("top_p", self.top_p),
                "frequency_penalty": config.get("frequency_penalty", self.frequency_penalty),
                "presence_penalty": config.get("presence_penalty", self.presence_penalty)
            }
            
            # 如果需要JSON格式输出
            if response_format == "json":
                request_params["response_format"] = {"type": "json_object"}
                # 在提示词中添加JSON格式要求
                if "json" not in full_prompt.lower():
                    full_prompt += "\n\n请以JSON格式返回结果。"
                    messages[-1]["content"] = full_prompt
            
            # 调用API
            print(f"🤖 正在调用大模型 ({agent_type or 'default'})...")
            response = self.client.chat.completions.create(**request_params)
            
            # 提取响应内容
            content = response.choices[0].message.content
            
            # 如果是JSON格式，清理和验证
            if response_format == "json":
                content = self._clean_json_response(content)
            
            print("✅ 大模型响应成功")
            return content
            
        except Exception as e:
            print(f"❌ 大模型调用失败: {e}")
            return self._mock_response(prompt, agent_type)
    
    def _get_config_for_agent(self, agent_type: str = None, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取智能体特定的配置参数
        
        Args:
            agent_type (str): 智能体类型
            custom_config (dict): 自定义配置
            
        Returns:
            dict: 配置参数
        """
        # 基础配置
        base_config = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty
        }
        
        # 如果有智能体特定配置，合并
        if agent_type and agent_type in self.agent_configs:
            agent_config = self.agent_configs[agent_type]
            base_config.update(agent_config)
        
        # 如果有自定义配置，覆盖
        if custom_config:
            base_config.update(custom_config)
        
        return base_config
    
    def _clean_json_response(self, content: str) -> str:
        """清理JSON响应格式"""
        try:
            # 移除可能的代码块标记
            content = content.replace("```json", "").replace("```", "")
            content = content.strip()
            
            # 验证JSON格式
            json.loads(content)
            return content
            
        except json.JSONDecodeError:
            print("⚠️ 响应不是有效的JSON格式，返回原始内容")
            return content
    
    def _mock_response(self, prompt: str, agent_type: str = None) -> str:
        """生成模拟响应（用于测试）"""
        prompt_lower = prompt.lower()
        
        # 根据智能体类型和提示词内容返回不同的模拟响应
        if agent_type == "designer" or "目标函数" in prompt or "objective_function" in prompt_lower:
            return """
def objective_function(dss_engine, variables):
    '''最小化网损目标函数'''
    import numpy as np
    
    try:
        # 设置优化变量（储能功率）
        for i, power in enumerate(variables):
            dss_engine.set_storage_power(f'storage{i+1}', power)
        
        # 执行潮流计算
        if not dss_engine.solve_power_flow():
            return float('inf')  # 不收敛时返回极大值
        
        # 计算总网损
        total_losses = dss_engine.get_total_losses()
        
        return total_losses
        
    except Exception as e:
        print(f"目标函数计算出错: {e}")
        return float('inf')
"""
        
        elif agent_type == "solver" or "求解算法" in prompt or "solve_optimization" in prompt_lower:
            return """
def solve_optimization(dss_engine, objective_function, bounds):
    '''多算法优化求解'''
    import numpy as np
    
    print("🚀 开始多算法优化...")
    
    # 算法1: 差分进化
    print("🧬 算法1: 差分进化")
    try:
        from scipy.optimize import differential_evolution
        
        def wrapper_function(variables):
            try:
                obj_value = objective_function(dss_engine, variables)
                if np.isnan(obj_value) or np.isinf(obj_value):
                    return 1e10
                return obj_value
            except Exception as e:
                print(f"  ⚠️ 目标函数评估失败: {e}")
                return 1e10
        
        result_de = differential_evolution(
            wrapper_function,
            bounds,
            maxiter=30,
            popsize=8,
            seed=42,
            disp=False
        )
        
        print(f"  ✅ DE完成: 目标值 = {result_de.fun:.6f}")
        
    except ImportError:
        print("  ❌ DE算法不可用")
        result_de = None
    
    # 算法2: 粒子群优化
    print("🐝 算法2: 粒子群优化")
    try:
        result_pso = _pso_algorithm(dss_engine, objective_function, bounds)
        print(f"  ✅ PSO完成: 目标值 = {result_pso[1]:.6f}")
    except Exception as e:
        print(f"  ❌ PSO算法失败: {e}")
        result_pso = None
    
    # 算法3: 遗传算法
    print("🧬 算法3: 遗传算法")
    try:
        result_ga = _ga_algorithm(dss_engine, objective_function, bounds)
        print(f"  ✅ GA完成: 目标值 = {result_ga[1]:.6f}")
    except Exception as e:
        print(f"  ❌ GA算法失败: {e}")
        result_ga = None
    
    # 选择最优结果
    results = [r for r in [result_de, result_pso, result_ga] if r is not None]
    
    if not results:
        print("❌ 所有算法都失败，使用随机搜索")
        return _random_search_fallback(dss_engine, objective_function, bounds)
    
    # 找到最优结果
    best_result = min(results, key=lambda x: x[1])
    
    optimization_info = {
        'algorithm': 'multi_algorithm',
        'success': True,
        'total_algorithms': len(results),
        'best_algorithm': 'unknown'
    }
    
    print(f"🎉 多算法优化完成: 最优目标值 = {best_result[1]:.6f}")
    
    return best_result[0], best_result[1], optimization_info

def _pso_algorithm(dss_engine, objective_function, bounds):
    '''粒子群优化算法'''
    import numpy as np
    import random
    
    n_particles = 20
    n_iterations = 50
    n_variables = len(bounds)
    
    # 初始化粒子
    particles = np.random.uniform(
        [b[0] for b in bounds], 
        [b[1] for b in bounds], 
        (n_particles, n_variables)
    )
    velocities = np.random.uniform(-0.1, 0.1, (n_particles, n_variables))
    
    # 个体最优和全局最优
    pbest = particles.copy()
    pbest_fitness = np.array([float('inf')] * n_particles)
    gbest = particles[0].copy()
    gbest_fitness = float('inf')
    
    # 迭代优化
    for iteration in range(n_iterations):
        for i in range(n_particles):
            try:
                fitness = objective_function(dss_engine, particles[i])
                if fitness < pbest_fitness[i]:
                    pbest[i] = particles[i].copy()
                    pbest_fitness[i] = fitness
                    
                    if fitness < gbest_fitness:
                        gbest = particles[i].copy()
                        gbest_fitness = fitness
            except:
                continue
        
        # 更新速度和位置
        w = 0.7  # 惯性权重
        c1 = 1.5  # 个体学习因子
        c2 = 1.5  # 社会学习因子
        
        for i in range(n_particles):
            velocities[i] = (w * velocities[i] + 
                           c1 * random.random() * (pbest[i] - particles[i]) +
                           c2 * random.random() * (gbest - particles[i]))
            
            particles[i] += velocities[i]
            
            # 边界约束
            particles[i] = np.clip(particles[i], 
                                 [b[0] for b in bounds], 
                                 [b[1] for b in bounds])
    
    return gbest.tolist(), gbest_fitness, {'algorithm': 'PSO'}

def _ga_algorithm(dss_engine, objective_function, bounds):
    '''遗传算法'''
    import numpy as np
    import random
    
    pop_size = 30
    n_generations = 40
    n_variables = len(bounds)
    
    # 初始化种群
    population = np.random.uniform(
        [b[0] for b in bounds], 
        [b[1] for b in bounds], 
        (pop_size, n_variables)
    )
    
    best_individual = None
    best_fitness = float('inf')
    
    for generation in range(n_generations):
        # 评估适应度
        fitness = []
        for individual in population:
            try:
                fit = objective_function(dss_engine, individual)
                fitness.append(fit)
                if fit < best_fitness:
                    best_fitness = fit
                    best_individual = individual.copy()
            except:
                fitness.append(float('inf'))
        
        # 选择
        fitness = np.array(fitness)
        fitness = 1 / (1 + fitness)  # 转换为最大化问题
        probs = fitness / fitness.sum()
        
        new_population = []
        for _ in range(pop_size):
            parent1 = population[np.random.choice(pop_size, p=probs)]
            parent2 = population[np.random.choice(pop_size, p=probs)]
            
            # 交叉
            if random.random() < 0.8:
                crossover_point = random.randint(1, n_variables-1)
                child = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
            else:
                child = parent1.copy()
            
            # 变异
            if random.random() < 0.1:
                mutation_point = random.randint(0, n_variables-1)
                child[mutation_point] = random.uniform(bounds[mutation_point][0], bounds[mutation_point][1])
            
            # 边界约束
            child = np.clip(child, [b[0] for b in bounds], [b[1] for b in bounds])
            new_population.append(child)
        
        population = np.array(new_population)
    
    return best_individual.tolist(), best_fitness, {'algorithm': 'GA'}

def _random_search_fallback(dss_engine, objective_function, bounds):
    '''随机搜索备用算法'''
    import random
    
    print("🎲 使用随机搜索算法...")
    
    best_variables = None
    best_objective = float('inf')
    n_evaluations = 50
    
    for i in range(n_evaluations):
        variables = [random.uniform(bound[0], bound[1]) for bound in bounds]
        
        try:
            obj_value = objective_function(dss_engine, variables)
            if obj_value < best_objective:
                best_objective = obj_value
                best_variables = variables.copy()
                print(f"  🎯 迭代 {i+1}: 目标值 = {best_objective:.6f}")
        except:
            continue
    
    optimization_info = {
        'algorithm': 'random_search',
        'total_evaluations': n_evaluations,
        'success': best_variables is not None
    }
    
    return best_variables, best_objective, optimization_info
"""
        
        elif agent_type == "reviewer" or "代码审查" in prompt or "review" in prompt_lower:
            return """
REVIEW_RESULT: PASS
COMMENTS: 代码检查通过，语法正确，逻辑合理，符合用户需求。
ISSUES: []
SUGGESTED_FIXES: {}
"""
        
        elif agent_type == "manager" or "decision" in prompt_lower or "决策" in prompt:
            return """
DECISION: TERMINATE_SUCCESS
REASON: 优化算法收敛，得到有效的最优解，目标函数值合理
NEXT_ACTION: 输出最终结果给用户
FEEDBACK: 优化成功完成！找到了最优运行策略。
"""
        
        else:
            return "模拟响应：功能正常运行中。"
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            if not self.client:
                return False
            
            response = self.generate("测试连接，请回复'连接成功'")
            return "成功" in response or "success" in response.lower()
            
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "client_initialized": self.client is not None,
            "agent_configs": list(self.agent_configs.keys())
        }
    
    def update_agent_config(self, agent_type: str, config: Dict[str, Any]):
        """
        更新智能体特定配置
        
        Args:
            agent_type (str): 智能体类型
            config (dict): 新的配置参数
        """
        if agent_type in self.agent_configs:
            self.agent_configs[agent_type].update(config)
            print(f"✅ 已更新 {agent_type} 的配置")
        else:
            print(f"⚠️ 未知的智能体类型: {agent_type}")
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """
        获取智能体特定配置
        
        Args:
            agent_type (str): 智能体类型
            
        Returns:
            dict: 配置参数
        """
        return self.agent_configs.get(agent_type, {}) 