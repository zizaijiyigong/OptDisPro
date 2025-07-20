import win32com.client
import numpy as np
import pygmo as pg
import csv
import os

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 创建 OpenDSS 引擎对象
DSSObj = win32com.client.Dispatch("OpenDSSEngine.DSS")
# 屏蔽显示opendss进度条的功能， 以防迭代过程中出现地址占用的问题
DSSObj.Allowforms = False
# 设置OpenDSS工作路径为项目根目录
DSSText = DSSObj.Text
DSSText.Command = f"Set DataPath='{PROJECT_ROOT}'"
# 获取 OpenDSS 文本接口对象
DSSText = DSSObj.Text
# 获取激活的电路接口对象
DSSCircuit = DSSObj.ActiveCircuit
# 获取解决方案接口对象
DSSSolution = DSSCircuit.Solution
# 激活监视器对象
DSSMonitors = DSSCircuit.Monitors
# 激活测量器对象
DSSEnergyMeters = DSSCircuit.Meters
# 激活loadshape对象
DSSLoadShapes = DSSCircuit.LoadShapes
# 激活网络线路接口
DSSLines = DSSCircuit.Lines
# 激活网络变压器接口
DSSTransformers = DSSCircuit.Transformers


class userproblem:

    def __init__(self, dim, network):
        self.dim = dim
        self.network = network

    def get_bounds(self):
        return ([-1] * self.dim, [1] * self.dim)

    def fitness(self, x):
        self.network.clear()
        self.network.gridinitialisation()
        DSSCircuit.SetActiveClass('Storage')
        storage_names = DSSCircuit.ActiveClass.AllNames
        storage_shapes = []
        for i, name in enumerate(storage_names):
            DSSCircuit.SetActiveElement(f'Storage.{name}')
            storage_shapes.append(DSSCircuit.ActiveCktElement.Properties('daily').val)
        for i, name in enumerate(storage_shapes):
            values = [round(float(j), 5) for j in x[i * 96:(i + 1) * 96]]
            DSSText.Command = f'New LoadShape.{name} npts=96 interval={self.network.Interval} mult={values}'
        max_overload = self.network.targetfunction()
        return [max_overload]

class network:
    # 生成dss网架时提取的参数
    def __init__(self, dss_mainfile):
        self.dss_mainfile = os.path.join(PROJECT_ROOT, dss_mainfile)  # 使用绝对路径
        # 编译并加载 DSS 主文件
        DSSText.Command = f"compile '{self.dss_mainfile}'"

        # 获取每条支路的名字
        self.line_names = DSSCircuit.Lines.AllNames
        # 获取每个线路下游节点的名字
        self.node_names = []
        for i, name in enumerate(self.line_names):
            # 按照线路名称确定线路
            DSSCircuit.lines.name = name
            # 找出下游节点
            self.node_names.append(DSSCircuit.lines.bus2)
        self.node_names = tuple(self.node_names)
        # 获取每个负荷的名字
        self.load_names = DSSCircuit.Loads.AllNames
        # 设置存储线路相数的集合
        self.line_phases = []
        # 设置存储线路正常运行电流大小的集合
        self.line_NormAmps = []
        # 读取每条支路的相数
        for i, name in enumerate(self.line_names):
            DSSLines.Name = name
            self.line_phases.append(DSSLines.Phases)
            self.line_NormAmps.append(DSSLines.NormAmps)
        # 获取每个变压器的名字
        self.transformer_names = DSSCircuit.Transformers.AllNames
        # 获取每个光伏的名字
        self.pvsystem_names = DSSCircuit.PVSystems.AllNames
        # 获取变压器容量
        self.transformer_kVA = []
        for i, name in enumerate(self.transformer_names):
            DSSTransformers.Name = name
            self.transformer_kVA.append(DSSTransformers.kva)
        # 获取每个监视器的姓名
        self.MonitorsAllName = []
        # 获取loadshape的名称，即负荷曲线名
        self.loadshape_names = DSSLoadShapes.AllNames
        # 获取变压器额定电流
        self.transformer_ratecurrent = {}
        # 获取变压器的额定功率
        self.tranformer_kva = {}
        # 获取变压器的额定电压
        self.tranformer_kV = {}
        # 获取储能的基础信息
        DSSCircuit.SetActiveClass('Storage')
        # 获取每个储能的名字
        self.storage_names = DSSCircuit.ActiveClass.AllNames
        self.storageloadshape_names = []
        self.storageloadshape_mult = {}
        for i, name in enumerate(self.storage_names):
            DSSCircuit.SetActiveElement(name)
            storageloadshapename = DSSCircuit.ActiveCktElement.Properties("daily").val
            self.storageloadshape_names.append(storageloadshapename)
            DSSCircuit.LoadShapes.name = storageloadshapename
            self.storageloadshape_mult[storageloadshapename] = DSSCircuit.LoadShapes.Pmult
        self.storageloadshape_names = tuple(self.storageloadshape_names)
        #获取求解的时序数
        DSSCircuit.SetActiveClass('loadshape')
        DSSCircuit.SetActiveElement(f'{DSSCircuit.ActiveClass.AllNames[0]}')
        self.T_daily = int(DSSCircuit.ActiveCktElement.Properties("npts").val)
        self.Interval = float(DSSCircuit.ActiveCktElement.Properties("interval").val)
        self.dimx = self.T_daily * len(self.storage_names)
        self.storage_shapes = []

    # 进行网架初始化操作
    def gridinitialisation(self):
        DSSText.Command = f"compile '{self.dss_mainfile}'"
        
    # 清空当前网架内容
    def clear(self):
        DSSText.Command = 'clear'

    # 获取解决方案
    def solve(self, mode, freq, vol, number):
        # 设置电压等级并进行计算
        DSSText.Command = f'Set Voltagebases={vol}'         # 用来设置电压等级
        DSSText.Command = f'calcv'                          # 用来计算电压
        # 设置计算的默认频率
        DSSText.Command = f'Set DefaultBaseFrequency={freq}'
        # 设置求解的模式snap是断面求解、Daily是日时序求解、Yearly是年时序
        DSSText.Command = f'set mode = {mode}'
        # 设置求解的点数
        DSSText.Command = f'set number = {number}'
        # 设置求解次数
        DSSText.Command = f'Set maxcontroliter = 500'
        DSSSolution.Solve()
        # 检查结果是否收敛
        if DSSSolution.Converged != 1:
            Converge = -1
            print('结果不收敛')
        else:
            Converge = 1
            # print('结果收敛')
    

    def get_system_losses(self):
        """获取系统损耗"""
        try:
            losses = DSSCircuit.Losses
            total_losses_kw = losses[0] / 1000.0
            return total_losses_kw
        except Exception as e:
            print(f"获取损耗失败: {e}")
            return float('inf')
    
    def get_bus_voltages(self):
        """获取母线电压"""
        try:
            voltages = np.array(DSSCircuit.AllBusVmagPu)
            return voltages
        except Exception as e:
            print(f"获取电压失败: {e}")
            return np.array([])

    def get_all_node_names(self):
        """获取所有节点名称"""
        return DSSCircuit.AllNodeNames

    def get_all_bus_vmag(self):
        """获取所有母线电压幅值"""
        return DSSCircuit.AllBusVmag

    def targetfunction(self):
        """
        指标函数：计算变压器过载率，以有功功率与总容量的比值表示。
        
        该方法首先为所有变压器创建功率监测器，然后解决电力系统的每日运行情况。
        接着，它遍历每个变压器，计算每个时间点的有功功率与容量的比值，
        并找出最大过载率作为目标函数值。
        """
        self.transformer_overload = {}
        for i, name in enumerate(self.transformer_names):
            DSSText.Command = f'New Monitor.transmonitor{i} element=transformer.{name} terminal=1 mode=1'
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        max_overload = 0
        for i, name in enumerate(self.transformer_names):
            DSSMonitors.Name = f'transmonitor{i}'
            kw_phase1 = np.array(DSSMonitors.Channel(1))
            kw_phase2 = np.array(DSSMonitors.Channel(3))
            kw_phase3 = np.array(DSSMonitors.Channel(5))
            total_kw = kw_phase1 + kw_phase2 + kw_phase3
            overload_ratio = total_kw / (self.transformer_kVA[i])
            max_ratio = np.max(overload_ratio)
            self.transformer_overload[f'变压器{name}的最大过载率'] = max_ratio
            if max_ratio > max_overload:
                max_overload = max_ratio
        return max_overload

    def solve_optimization(self):
        """
        变压器过载率优化函数。
        
        该函数通过多种优化算法寻找最优的储能系统充放电策略，
        以最小化变压器的最大过载率。
        """
        self.transformer_overload_results = {}
        prob = pg.problem(userproblem(dim=self.dimx, network=self))
        algo_settings = {'PSO': {'algo': pg.pso(gen=500, omega=0.7, eta1=1.5, eta2=1.5), 'pop_size': 30, 'num_runs': 5}, 'DE': {'algo': pg.de(gen=600, F=0.9, CR=0.8), 'pop_size': 40, 'num_runs': 5}, 'SGA': {'algo': pg.sga(gen=400, cr=0.8, eta_c=1.2, m=0.03, param_m=1.2, param_s=3, crossover='exponential', mutation='polynomial', selection='tournament'), 'pop_size': 50, 'num_runs': 5}}
        for algo_name in algo_settings.keys():
            self.transformer_overload_results[f'{algo_name}_results'] = []
        for algo_name, setting in algo_settings.items():
            print(f'=== 执行{algo_name}算法 ===')
            optimizer = pg.algorithm(setting['algo'])
            optimizer.set_verbosity(50)
            for run in range(setting['num_runs']):
                seed = np.random.randint(0, 10000)
                pop_size = setting['pop_size'] + np.random.randint(-5, 6)
                pop_size = max(10, pop_size)
                pop = pg.population(prob, size=pop_size, seed=seed)
                pop = optimizer.evolve(pop)
                result = {'run_id': run + 1, 'best_fitness': pop.champion_f[0], 'best_solution': pop.champion_x.copy(), 'seed': seed, 'pop_size': pop_size}
                self.transformer_overload_results[f'{algo_name}_results'].append(result)
                print(f"  {algo_name} 循环{run + 1}: 最优适应度={result['best_fitness']:.4f}")
        print('\n=== 优化结果汇总 ===')
        for algo_name in algo_settings.keys():
            results = self.transformer_overload_results[f'{algo_name}_results']
            best_result = min(results, key=lambda x: x['best_fitness'])
            print(f"{algo_name}算法最佳结果: 适应度={best_result['best_fitness']:.4f} (循环{best_result['run_id']})")

def run_optimization():
    """执行优化求解的主函数"""
    print("🚀 开始多算法最优潮流优化求解...")
    
    try:
        dssfile_path = 'dssdata/Grid_C/main.dss'   # 使用相对路径，相对于项目根目录

        global network1
        network1 = network(dssfile_path)
        
        network1.clear()
        network1.gridinitialisation()

        # 调用多算法优化
        optimization_results = network1.solve_optimization()
        print(f"多算法优化完成!: {optimization_results}")


        # 返回所有算法的结果
        return {
            'success': True,
            'all_algorithm_results': optimization_results
        }
        
    except Exception as e:
        print(f"❌ 优化过程出错: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__=="__main__":
    result = run_optimization()