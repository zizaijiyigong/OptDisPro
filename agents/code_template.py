import os
import ast
import textwrap
import sys
from typing import Dict, List, Tuple, Optional


class CodeTemplate:
    """简化的代码模板类，专注于鲁棒的代码拼接"""
    
    def __init__(self, base_code_file=None):
        """初始化代码模板"""
        self.base_code_file = "Network_code.py"
        self.base_code = self._load_base_code()
        self.insertion_points = {
            'OBJECTIVE_FUNCTION': '# {{INSERT_OBJECTIVE_FUNCTION}}',
            'OPTIMIZATION_ALGORITHM': '# {{INSERT_OPTIMIZATION_ALGORITHM}}'
        }
        self.has_ast_unparse = hasattr(ast, 'unparse') and sys.version_info >= (3, 9)
    
    def _load_base_code(self):
        """加载基础代码模板"""
        try:
            with open(self.base_code_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"⚠️ 基础代码文件 {self.base_code_file} 未找到，使用默认模板")
            return self._get_default_template()
        except Exception as e:
            print(f"⚠️ 加载基础代码失败: {e}")
            return self._get_default_template()
    
    def _get_default_template(self):
        """获取默认代码模板"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的优化代码
"""

import numpy as np
import pygmo as pg
from opendssdirect import *

class OptimizationSystem:
    def __init__(self):
        self.network = None
        self.optimization_results = {}
    
    # {{INSERT_OBJECTIVE_FUNCTION}}
    
    # {{INSERT_OPTIMIZATION_ALGORITHM}}

if __name__ == "__main__":
    system = OptimizationSystem()
    print("优化系统已初始化")
'''
    
    def insert_code_snippets_robust(self, snippets: Dict[str, str]) -> str:
        """
        鲁棒的代码拼接方法 - 外部唯一调用接口
        
        Args:
            snippets: 代码片段字典 {'OBJECTIVE_FUNCTION': code, 'OPTIMIZATION_ALGORITHM': code}
            
        Returns:
            str: 拼接完成的完整代码
        """
        print("🔗 开始鲁棒代码拼接...")
        
        complete_code = self.base_code
        
        # 收集所有类定义
        all_classes = []
        for point_type, placeholder in self.insertion_points.items():
            if placeholder in complete_code and snippets.get(point_type):
                try:
                    processed_code, extracted_classes = self._process_snippet(
                        snippets[point_type], point_type
                    )
                    
                    # 替换插入点
                    complete_code = complete_code.replace(placeholder, processed_code)
                    all_classes.extend(extracted_classes)
                    
                    print(f"✅ {point_type} 处理完成")
                    
                except Exception as e:
                    print(f"⚠️ {point_type} 处理失败，使用原始代码: {e}")
                    # 失败时使用简单的缩进处理
                    simple_code = self._simple_indent_fix(snippets[point_type], point_type)
                    complete_code = complete_code.replace(placeholder, simple_code)
            else:
                # 移除空的插入点
                complete_code = complete_code.replace(placeholder, "")
        
        # 将类定义插入到合适的位置（导入语句之后，函数定义之前）
        if all_classes:
            complete_code = self._insert_classes_at_proper_location(complete_code, all_classes)
            print(f"📝 已添加 {len(all_classes)} 个类定义到合适位置")
        
        print("🎉 代码拼接完成")
        return complete_code
    
    def _process_snippet(self, code_snippet: str, point_type: str) -> Tuple[str, List[str]]:
        """
        处理单个代码片段的核心方法
        
        Returns:
            tuple: (处理后的方法体代码, 提取的类定义列表)
        """
        # 1. 标准化缩进
        normalized_code = self._normalize_code(code_snippet)
        
        # 2. 修复文档字符串缩进
        normalized_code = self._fix_docstring_indentation(normalized_code)
        
        # 3. AST解析和处理
        try:
            tree = ast.parse(normalized_code)
            return self._extract_from_ast(tree, point_type)
        except SyntaxError:
            # AST解析失败，使用文本处理
            print(f"⚠️ {point_type} AST解析失败，使用文本处理")
            return self._extract_from_text(normalized_code, point_type)
    
    def _normalize_code(self, code: str) -> str:
        """标准化代码缩进和格式"""
        if not code.strip():
            return ""
        
        lines = code.strip().split('\n')
        
        # 找到第一个非空行的缩进作为基准
        base_indent = 0
        for line in lines:
            if line.strip():
                base_indent = len(line) - len(line.lstrip())
                break
        
        # 标准化所有行的缩进
        normalized_lines = []
        for line in lines:
            if not line.strip():
                normalized_lines.append("")
            else:
                # 计算相对缩进并标准化为4的倍数
                current_indent = len(line) - len(line.lstrip())
                relative_indent = max(0, current_indent - base_indent)
                standard_indent = (relative_indent // 4) * 4
                
                # 特殊处理文档字符串缩进
                stripped = line.strip()
                if (stripped.startswith('"""') or stripped.startswith("'''")) and relative_indent > 0:
                    # 文档字符串应该与函数体保持一致的缩进
                    standard_indent = 4
                
                normalized_lines.append(" " * standard_indent + line.lstrip())
        
        return '\n'.join(normalized_lines)
    
    def _fix_docstring_indentation(self, code: str) -> str:
        """
        修复文档字符串的缩进问题
        
        Args:
            code: 包含文档字符串的代码
            
        Returns:
            str: 修复后的代码
        """
        lines = code.split('\n')
        fixed_lines = []
        in_docstring = False
        docstring_indent = 0
        function_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测函数定义
            if stripped.startswith('def '):
                function_indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                continue
            
            # 检测文档字符串开始
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_docstring = True
                # 文档字符串应该比函数定义多4个空格缩进
                docstring_indent = function_indent + 4
                quote_type = '"""' if stripped.startswith('"""') else "'''"
                
                # 处理单行文档字符串
                if stripped.count(quote_type) >= 2:
                    fixed_lines.append(" " * docstring_indent + stripped)
                    in_docstring = False
                else:
                    # 多行文档字符串开始
                    fixed_lines.append(" " * docstring_indent + stripped)
                continue
            
            # 在文档字符串内部
            if in_docstring:
                if stripped.endswith('"""') or stripped.endswith("'''"):
                    # 文档字符串结束
                    fixed_lines.append(" " * docstring_indent + stripped)
                    in_docstring = False
                else:
                    # 文档字符串内容，保持相对缩进
                    if stripped:
                        # 对于文档字符串内容，保持与开始行相同的缩进
                        fixed_lines.append(" " * docstring_indent + stripped)
                    else:
                        # 空行保持相同缩进
                        fixed_lines.append(" " * docstring_indent)
                continue
            
            # 普通代码行
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _extract_from_ast(self, tree: ast.AST, point_type: str) -> Tuple[str, List[str]]:
        """从AST中提取函数体和类定义"""
        function_bodies = []
        class_definitions = []
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                # 提取函数体（去掉def行）
                body_code = self._ast_to_code(node.body)
                function_bodies.append(body_code)
            elif isinstance(node, ast.ClassDef):
                # 提取类定义
                class_code = self._ast_to_code([node])
                class_definitions.append(class_code)
        
        # 合并函数体
        method_body = '\n'.join(function_bodies) if function_bodies else ""
        
        # 根据插入点类型调整缩进
        if point_type in ['OBJECTIVE_FUNCTION', 'OPTIMIZATION_ALGORITHM']:
            # 类方法内部需要8个空格缩进
            method_body = self._add_method_indent(method_body)
        
        return method_body, class_definitions
    
    def _extract_from_text(self, code: str, point_type: str) -> Tuple[str, List[str]]:
        """文本方式提取函数体和类定义"""
        lines = code.split('\n')
        method_lines = []
        class_lines = []
        current_class = []
        in_class = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('class '):
                if current_class:
                    class_lines.append('\n'.join(current_class))
                current_class = [line]
                in_class = True
            elif in_class:
                if stripped and not line.startswith(' ') and not line.startswith('\t'):
                    # 类定义结束
                    class_lines.append('\n'.join(current_class))
                    current_class = []
                    in_class = False
                    method_lines.append(line)
                else:
                    current_class.append(line)
            elif not stripped.startswith('def '):
                # 跳过函数定义行，保留函数体
                method_lines.append(line)
        
        # 处理最后一个类
        if current_class:
            class_lines.append('\n'.join(current_class))
        
        method_body = '\n'.join(method_lines).strip()
        
        # 调整缩进
        if point_type in ['OBJECTIVE_FUNCTION', 'OPTIMIZATION_ALGORITHM']:
            method_body = self._add_method_indent(method_body)
        
        return method_body, class_lines
    
    def _ast_to_code(self, nodes: List[ast.AST]) -> str:
        """将AST节点转换为代码字符串"""
        if not nodes:
            return ""
        
        code_parts = []
        for node in nodes:
            if self.has_ast_unparse:
                code_parts.append(ast.unparse(node))
            else:
                # 简单的备用方案
                code_parts.append(f"# AST节点: {type(node).__name__}")
        
        return '\n'.join(code_parts)
    
    def _add_method_indent(self, code: str) -> str:
        """为方法体添加适当的缩进（8个空格）"""
        if not code.strip():
            return ""
        
        lines = code.split('\n')
        indented_lines = []
        
        for line in lines:
            if line.strip():
                indented_lines.append("        " + line)  # 8个空格
            else:
                indented_lines.append("")
        
        return '\n'.join(indented_lines)
    
    def _simple_indent_fix(self, code: str, point_type: str) -> str:
        """简单的缩进修复备用方案"""
        if not code.strip():
            return ""
        
        lines = code.strip().split('\n')
        
        # 移除函数定义行
        filtered_lines = []
        for line in lines:
            if not line.strip().startswith('def ') and not line.strip().startswith('class '):
                filtered_lines.append(line)
        
        # 添加适当缩进
        if point_type in ['OBJECTIVE_FUNCTION', 'OPTIMIZATION_ALGORITHM']:
            indented_lines = []
            for line in filtered_lines:
                if line.strip():
                    indented_lines.append("        " + line.lstrip())
                else:
                    indented_lines.append("")
            return '\n'.join(indented_lines)
        
        return '\n'.join(filtered_lines)
    
    def _insert_classes_at_proper_location(self, complete_code: str, class_definitions: List[str]) -> str:
        """
        将类定义插入到合适的位置（导入语句之后，函数定义之前）
        
        Args:
            complete_code: 完整的代码
            class_definitions: 类定义列表
            
        Returns:
            str: 插入类定义后的代码
        """
        lines = complete_code.split('\n')
        new_lines = []
        classes_inserted = False
        
        for line in lines:
            stripped = line.strip()
            
            # 如果还没有插入类定义，且遇到第一个函数定义或类定义
            if not classes_inserted and (stripped.startswith('def ') or stripped.startswith('class ')):
                # 在函数定义之前插入类定义
                if class_definitions:
                    new_lines.append('')  # 添加空行
                    new_lines.extend(class_definitions)
                    new_lines.append('')  # 添加空行
                classes_inserted = True
            
            new_lines.append(line)
        
        # 如果没有找到函数定义，将类定义插入到文件末尾（在导入语句之后）
        if not classes_inserted:
            # 找到最后一个导入语句的位置
            last_import_index = -1
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    last_import_index = i
            
            # 在最后一个导入语句之后插入类定义
            if last_import_index >= 0:
                new_lines = lines[:last_import_index + 1]
                new_lines.append('')  # 添加空行
                new_lines.extend(class_definitions)
                new_lines.append('')  # 添加空行
                new_lines.extend(lines[last_import_index + 1:])
            else:
                # 如果没有导入语句，在文件开头插入
                new_lines = class_definitions + [''] + lines
        
        return '\n'.join(new_lines)
    
    def save_complete_code(self, complete_code: str, filename: str) -> bool:
        """保存完整代码到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(complete_code)
            print(f"💾 代码已保存到: {filename}")
            return True
        except Exception as e:
            print(f"❌ 保存代码失败: {e}")
            return False 