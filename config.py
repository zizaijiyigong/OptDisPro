#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置文件
包含LLM、OpenDSS等相关配置
"""

# LLM配置
LLM_CONFIG = {
    "api_key": "",
    "base_url": "", 
    "model": "deepseek-v3",
    "temperature": 0.1,
    "max_tokens": 8096
}

# 系统配置
# SYSTEM_CONFIG = {
#     "max_iterations": 5,  # 最大迭代次数
#     "verbose": True,      # 详细输出
#     "save_logs": True,    # 保存日志
#     "demo_mode": True     # 演示模式（无OpenDSS时使用模拟）
# }

# # 优化配置
# OPTIMIZATION_CONFIG = {
#     "default_bounds": [(-50, 50), (-50, 50)],  # 默认变量边界
#     "algorithm_timeout": 300,  # 算法超时时间（秒）
#     "convergence_tolerance": 1e-6  # 收敛容差
# }

# # 日志配置
# LOG_CONFIG = {
#     "log_dir": "results/logs",
#     "log_level": "INFO",
#     "max_log_files": 10
# } 