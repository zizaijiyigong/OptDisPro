#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码执行器
负责执行已合并的代码
"""

import sys
import os
import time
import traceback
from pathlib import Path
from io import StringIO
import runpy
from .code_template import CodeTemplate

class CodeExecutor:
    """代码执行器 - 专注于代码执行功能"""
    
    def __init__(self):
        """初始化代码执行器"""
        self.code_template = None
        # 确保code_temp文件夹存在
        self.temp_dir = Path('code_temp')
        self.temp_dir.mkdir(exist_ok=True)
    
    def set_base_code_template(self, base_code_file=None):
        """设置基础代码模板"""
        self.code_template = CodeTemplate(base_code_file)
        print(f"📝 代码模板已设置: {'自定义模板' if base_code_file else '默认模板'}")
    
    def _execute_file(self, file_path):
        """
        执行Python文件
        使用runpy模块在当前Python环境中执行文件，可以捕获详细的错误信息
        
        Args:
            file_path (str): 要执行的Python文件路径
            
        Returns:
            dict: 执行结果，包含success, output, error和execution_time
        """
        result = {'success': False, 'output': '', 'error': '', 'execution_time': 0}
        
        # 保存当前工作目录
        original_cwd = os.getcwd()
        # 保存当前的sys.path
        original_syspath = sys.path.copy()
        # 保存当前的标准输出和标准错误
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            # 切换到文件所在目录
            file_dir = os.path.dirname(os.path.abspath(file_path))
            os.chdir(file_dir)
            
            # 将文件目录添加到sys.path
            if file_dir not in sys.path:
                sys.path.insert(0, file_dir)
            
            # 创建StringIO对象来捕获输出
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            # 重定向标准输出和标准错误
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 使用runpy执行文件
                runpy.run_path(
                    file_path,
                    run_name='__main__'
                )
                
                # 记录结束时间
                end_time = time.time()
                result['execution_time'] = end_time - start_time
                result['success'] = True
                
            except Exception as e:
                # 获取完整的错误堆栈
                error_tb = traceback.format_exc()
                result['error'] = f"执行错误:\n{error_tb}"
                result['success'] = False
            
            finally:
                # 获取输出
                result['output'] = stdout_capture.getvalue()
                if stderr_capture.getvalue():
                    result['error'] = f"{result['error']}\n标准错误输出:\n{stderr_capture.getvalue()}"
                
        finally:
            # 恢复标准输出和标准错误
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # 恢复工作目录
            os.chdir(original_cwd)
            
            # 恢复sys.path
            sys.path = original_syspath
            
            # 清理已导入的模块（如果有）
            module_name = Path(file_path).stem
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        return result
    
    def execute_code(self, complete_code):
        """
        执行已合并的完整代码
        
        Args:
            complete_code (str): 完整的代码字符串
            
        Returns:
            dict: 执行结果
        """
        result = {
            'success': False,
            'output': '',
            'error': '',
            'execution_time': 0
        }
        
        try:
            print(f"🚀 开始执行代码...")
            start_time = time.time()
            
            # 在code_temp文件夹中创建临时文件
            temp_file = self.temp_dir / f"temp_code_{int(time.time())}_{os.getpid()}.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(complete_code)
            
            # 执行代码
            execution_result = self._execute_file(str(temp_file))
            end_time = time.time()
            
            result.update(execution_result)
            result['execution_time'] = end_time - start_time
            
            if result['success']:
                print(f"✅ 代码执行成功，耗时 {result['execution_time']:.2f} 秒")
            else:
                print(f"❌ 代码执行失败: {result['error']}")
            
            # 清理临时文件
            try:
                temp_file.unlink()
                print(f"🗑️ 已删除临时文件: {temp_file}")
            except:
                pass
            
        except Exception as e:
            result['error'] = f"代码执行器异常: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ 代码执行器异常: {e}")
        
        return result
    
    def execute_file(self, file_path):
        """
        执行指定的Python文件
        
        Args:
            file_path (str): Python文件路径
            
        Returns:
            dict: 执行结果
        """
        result = {
            'success': False,
            'output': '',
            'error': '',
            'execution_time': 0
        }
        
        try:
            print(f"🚀 开始执行文件: {file_path}")
            start_time = time.time()
            
            # 执行文件
            execution_result = self._execute_file(file_path)
            end_time = time.time()
            
            result.update(execution_result)
            result['execution_time'] = end_time - start_time
            
            if result['success']:
                print(f"✅ 文件执行成功，耗时 {result['execution_time']:.2f} 秒")
            else:
                print(f"❌ 文件执行失败: {result['error']}")
            
        except Exception as e:
            result['error'] = f"文件执行器异常: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ 文件执行器异常: {e}")
        
        return result
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 删除code_temp文件夹中的所有临时文件
            for file in self.temp_dir.glob('temp_code_*.py'):
                if file.is_file():
                    file.unlink()
                    print(f"🗑️ 已删除临时文件: {file}")
            
            # 删除生成的优化文件
            for file in Path('.').glob('generated_optimization_*.py'):
                if file.is_file():
                    file.unlink()
                    print(f"🗑️ 已删除临时文件: {file}")
        except Exception as e:
            print(f"⚠️ 清理临时文件失败: {e}") 