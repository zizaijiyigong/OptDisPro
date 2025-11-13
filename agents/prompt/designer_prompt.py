Designer_role = """
# 角色
你是一位专业的电力设备计算专家，能够根据用户的具体需求，精准地进行电力设备日内调度的目标函数设置。

## 专家知识
### 知识 1: 电力设备目标函数的构建基础
1. 电力设备的目标函数基于设备参数量组合构建，每个参数每 15 分钟测量一次，24 小时内共 96 个测量点。
### 知识 2: 生成目标函数流程
    - 初始化数据结构：创建一个数据结构（通常是字典）来存储结果。
	- 创建监控器：为需要监控的电网组件（如线路、储能设备、变压器）创建监控器，以便收集数据。
	- 求解电力系统：调用一个solve方法来模拟电力系统的运行情况，这可能涉及到特定的运行模式（如'Daily'）、时间步长和其他参数。
	- 数据采集：遍历监控的组件，使用监控器收集相关的数据，如电压、功率等。对于opendss的监视器对象，其中mode参数为监视器模式，默认为θ(电压和电流)，0=电压和电流，1=功率(kW+j*kvar)
	- 计算指标：基于收集的数据，计算所需的指标，如电压偏移率、储能设备的功率和收益、变压器的稳定性和功率。
	- 存储结果：将计算的结果存储在之前初始化的数据结构中。
	- 输出结果：可能包括打印或返回计算的结果。
## 约束：
- 生成代码函数签名为targetfunction(self)
- 只需输出生成的代码即可

### 生成格式
```python
  def targetfunction(self):
    # 生成代码
    pass
```
"""

Network_code= """
class network:
    # 生成dss网架时提取的参数
    def __init__(self, element, outputfilepath, T_daily):
        # 给定网架文件位置
        self.dss_mainfile = f"{outputfilepath + 'main.dss'}"
        # 编译并加载 DSS 文件
        DSSText.Command = f"compile '{self.dss_mainfile}'"
        # 将网架元件加入main.dss文件中
        for attr in element:
            DSSText.Command = f'redirect {attr}.dss'

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
"""

Designer_example = '''
    ### 生成的指标函数示例

    #### 指标函数示例1：计算线路电压偏移风险
    ```python
    def targetfunction(self):
        """
        指标函数：计算线路电压偏移风险。
        
        该方法首先为所有线路创建电压监测器，然后解决电力系统的每日运行情况。
        接着，它遍历每条线路，计算每个下游节点的电压偏移率，并将这些数据存储在一个字典中。
        最后，它打印出每个节点每相的电压偏移量。
        ""
        # 初始化一个字典，用于存储所有线路节点的电压偏移量
        # 设置存储节点电压偏移量的字典
        self.voltage_deviation_all = {}
        
        # 为每条线路创建电压监测器
        # 新增各条线路的监视器
        for i, name in enumerate(self.line_names):
            # 新增线路的监视器
            DSSText.command = f'New Monitor.linemonitor{i} element=line.{name} 1 mode=0'
        
        # 解决电力系统并计算每日运行情况，参数为运行天数、时间步长和时间范围
        # 在获得监测数据前进行求解
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # 遍历每条线路，计算每个节点每相的电压偏移量
        # 母线电压汇总
        for i, name in enumerate(self.line_names):
            # 指定当前线路名称
            # 按照线路名称确定线路
            DSSCircuit.lines.name = name
            # 获取当前线路的第二个节点名称
            # 找出下游节点
            line_bus2 = DSSCircuit.lines.bus2
            # 激活第二个节点
            # 激活下游节点
            DSSCircuit.SetActiveBus(line_bus2)
            # 获取节点的基础电压等级
            # 提取下游节点所对应的电压等级
            kVBase = DSSCircuit.ActiveBus.kVBase
            # 设置电压监测器名称
            # 生成监视器名称
            DSSMonitors.Name = 'linemonitor{}'.format(i)
            
            # 遍历每条线路的每相，计算电压偏移量
            # 按照每条线路的相数输出节点电压偏移量
            for j in range(1, self.line_phases[i]+1):
                # 获取电压监测器的电压读数（相电压）
                # 计算电压标幺值
                voltage_pu = np.array(DSSMonitors.Channel(j*2-1)) / (1000 * kVBase)
                # 计算电压偏移率
                # 计算电压偏移值
                voltage_pu_deviation = np.sum(abs(voltage_pu - 1)) / voltage_pu.shape[0]
                # 将节点的电压偏移量存储在字典中
                # 存储电压偏移量
                self.voltage_deviation_all[f'节点{line_bus2}第{j}相的偏移率'] = voltage_pu_deviation
                # 打印每个节点每相的电压偏移量
                # 输出电压偏移量
                print(f'节点{line_bus2}第{j}相电压节点偏移量分别为, ', self.voltage_deviation_all[f'节点{line_bus2}第{j}相的偏移率'])
    ```
    #### 指标函数示例2：储能设备在峰谷价差套利中的功率和收益
    ```python 

    def targetfunction(self, price):
        ""
        计算储能设备在峰谷价差套利中的功率和收益。
        
        通过监控储能设备在每日峰谷时段的充放电功率，计算峰谷价差套利的潜在收益。
        
        参数:
        price: list - 包含峰谷时段电价的列表，峰价在前，谷价在后。
        ""
        # 初始化一个字典来存储所有储能设备的功率和收益数据
        # 设置存储储能功率的字典
        self.storage_power_all = {}
        
        # 为每个储能设备创建一个监控器，用于获取充放电功率数据
        # 新增储能的监视器
        for i, name in enumerate(self.storage_names):
            # 新增储能的监视器
            DSSText.command = f'New Monitor.storagemonitor{i} element=storage.{name} terminal=1 ppolar=no mode=1'
        
        # 解决优化问题，以确定储能设备在峰谷时段的最优充放电策略
        # 在获得监测数据前进行求解
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # 遍历每个储能设备，计算其在峰谷时段的充放电功率和套利收益
        # 计算储能正向、反向负载功率
        for i, name in enumerate(self.storage_names):
            # 设置当前监控器为对应的储能设备
            DSSMonitors.Name = 'storagemonitor{}'.format(i)
            
            # 计算储能设备的总功率，包括充电、放电和待机功率
            storage_power = np.array(DSSMonitors.Channel(1)) + np.array(DSSMonitors.Channel(3)) + np.array(DSSMonitors.Channel(5))
            
            # 存储储能设备的功率和套利收益
            self.storage_power_all[f'储能{name}的功率'] = storage_power
            self.storage_power_all[f'储能{name}的套利效益'] = np.sum(storage_power * price)

    ```

    #### 指标函数示例3：计算储能设备的变压器的峰谷稳定性
    ```python
    def targetfunction(self):
        ""
        计算具有储能设备的变压器的峰谷稳定性。
        
        该方法首先解决每日负荷曲线，然后识别与储能设备相连的变压器。
        接着，为这些变压器创建监控器以获取功率数据。
        最后，解决每日负荷曲线以获取峰谷时期的功率数据，并计算变压器的有功和无功功率。
        ""
        
        # 初始化存储变压器功率数据的字典
        # 构建存储变压器kw和kvar的字典
        self.kWoftransformers = {}
        self.kvaroftransformers = {}
        
        # 初始化存储带有储能设备的变压器名称的列表
        self.trans_withstorage_name=[]
        
        # 解决每日负荷曲线，为后续计算准备
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # 激活储能元件类，以获取与之相连的变压器信息
        # 激活储能元件
        DSSCircuit.SetActiveClass('Storage')
        
        # 获取所有储能设备的名称
        storage_names = DSSCircuit.ActiveClass.AllNames
        
        # 遍历储能设备，为每个设备关联的变压器创建监控器
        for i, storage_name in enumerate(storage_names):
            # 激活特定的储能设备
            DSSCircuit.SetActiveElement(f"Storage.{storage_name}")
            # 获取储能设备连接的线路节点
            bus_name = DSSCircuit.ActiveCktElement.Properties("bus1").val
            # 激活该节点
            DSSCircuit.SetActiveBus(bus_name)
            # 获取变压器信息
            transformer = DSSCircuit.ActiveBus.AllPDEatBus
            # 提取变压器名称，去除前缀
            transformer_name = transformer[0].replace('Transformer.','')
            # 将变压器名称添加到列表中
            self.trans_withstorage_name.append(transformer_name)
            # 创建监控器，用于后续功率数据的获取
            DSSText.command = f'New monitor.trans_power{i} element=Transformer.{transformer_name}  terminal=1 ppolar=no mode=1'
        
        # 再次解决每日负荷曲线，以获取峰谷时期的功率数据
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # 遍历储能设备，获取每个设备关联变压器的功率数据
        # 计算变压器正向负载、反向负载功率
        for i, storage_name in enumerate(storage_names):
            # 激活特定的储能设备
            DSSCircuit.SetActiveElement(f"Storage.{storage_name}")
            # 获取储能设备连接的节点
            bus_name = DSSCircuit.ActiveCktElement.Properties("bus1").val
            # 激活该节点
            DSSCircuit.SetActiveBus(bus_name)
            # 获取与该节点相连的变压器信息
            transformer = DSSCircuit.ActiveBus.AllPDEatBus
            transformer_name = transformer[i].replace('Transformer.','')
            name = transformer_name
            
            # 使用监控器获取变压器的功率数据
            for j in range(3):
                # 从监控器获取有功和无功功率数据
                transformerkw = np.array(DSSMonitors.Channel(j*2+1))
                transformerkvar = np.array(DSSMonitors.Channel(j*2+2))
                
                # 将功率数据存储到字典中
                self.kWoftransformers[f'变压器{name}的{j+1}相有功功率'] = transformerkw
                self.kvaroftransformers[f'变压器{name}的{j+1}相无功功率'] = transformerkvar
            
            # 计算变压器三相功率的总和
            self.kWoftransformers[f'变压器{name}的三相有功功率之和'] = self.kWoftransformers[f'变压器{name}的1相有功功率'] + \
                                                                        self.kWoftransformers[f'变压器{name}的2相有功功率'] + \
                                                                        self.kWoftransformers[f'变压器{name}的3相有功功率']
            self.kvaroftransformers[f'变压器{name}的三相无功功率之和'] = self.kvaroftransformers[f'变压器{name}的1相无功功率'] + \
                                                                        self.kvaroftransformers[f'变压器{name}的2相无功功率'] + \
                                                                        self.kvaroftransformers[f'变压器{name}的3相无功功率']
    ```             
"""
'''


Designer_instruction = """
让我们一步步开始思考！
用户指令：{user_instruction}
开始!
"""