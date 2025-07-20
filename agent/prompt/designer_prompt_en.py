Designer_role = """
# Role
You are a professional power equipment calculation expert who can accurately set up objective functions for power equipment intraday scheduling based on users' specific requirements.

## Expert Knowledge
### Knowledge 1: Foundation of Power Equipment Objective Function Construction
1. The objective function of power equipment is constructed based on equipment parameter combinations, with each parameter measured every 15 minutes, totaling 96 measurement points in 24 hours.

### Knowledge 2: Objective Function Generation Process
    - Initialize data structure: Create a data structure (usually a dictionary) to store results.
    - Create monitors: Create monitors for power grid components that need monitoring (such as lines, energy storage devices, transformers) to collect data.
    - Solve power system: Call a solve method to simulate power system operation, which may involve specific operation modes (such as 'Daily'), time steps, and other parameters.
    - Data collection: Iterate through monitored components, use monitors to collect relevant data such as voltage, power, etc. For OpenDSS monitor objects, the mode parameter is the monitor mode, default is θ (voltage and current), 0=voltage and current, 1=power (kW+j*kvar).
    - Calculate indicators: Based on collected data, calculate required indicators such as voltage deviation rate, power and revenue of energy storage devices, stability and power of transformers.
    - Store results: Store calculated results in the previously initialized data structure.
    - Output results: May include printing or returning calculated results.

## Constraints:
- Generated code function signature is targetfunction(self)
- Only output the generated code

### Generation Format
```python
  def targetfunction(self):
    # Generated code
    pass
```
"""

Network_code= """
class network:
    # Parameters extracted when generating dss network
    def __init__(self, element, outputfilepath, T_daily):
        # Given network file location
        self.dss_mainfile = f"{outputfilepath + 'main.dss'}"
        # Compile and load DSS file
        DSSText.Command = f"compile '{self.dss_mainfile}'"
        # Add network components to main.dss file
        for attr in element:
            DSSText.Command = f'redirect {attr}.dss'

        # Get the name of each branch
        self.line_names = DSSCircuit.Lines.AllNames
        # Get the name of each downstream node
        self.node_names = []
        for i, name in enumerate(self.line_names):
            # Determine line according to line name
            DSSCircuit.lines.name = name
            # Find downstream node
            self.node_names.append(DSSCircuit.lines.bus2)
        self.node_names = tuple(self.node_names)
        # Get the name of each load
        self.load_names = DSSCircuit.Loads.AllNames
        # Set collection to store line phases
        self.line_phases = []
        # Set collection to store normal operating current of lines
        self.line_NormAmps = []
        # Read the number of phases for each branch
        for i, name in enumerate(self.line_names):
            DSSLines.Name = name
            self.line_phases.append(DSSLines.Phases)
            self.line_NormAmps.append(DSSLines.NormAmps)
        # Get the name of each transformer
        self.transformer_names = DSSCircuit.Transformers.AllNames
        # Get the name of each PV system
        self.pvsystem_names = DSSCircuit.PVSystems.AllNames
        # Get transformer capacity
        self.transformer_kVA = []
        for i, name in enumerate(self.transformer_names):
            DSSTransformers.Name = name
            self.transformer_kVA.append(DSSTransformers.kva)
        # Get the name of each monitor
        self.MonitorsAllName = []
        # Get loadshape names, i.e., load curve names
        self.loadshape_names = DSSLoadShapes.AllNames
        # Get transformer rated current
        self.transformer_ratecurrent = {}
        # Get transformer rated power
        self.tranformer_kva = {}
        # Get transformer rated voltage
        self.tranformer_kV = {}
        # Get basic information of energy storage
        DSSCircuit.SetActiveClass('Storage')
        # Get the name of each energy storage
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
        # Get the number of time series for solving
        DSSCircuit.SetActiveClass('loadshape')
        DSSCircuit.SetActiveElement(f'{DSSCircuit.ActiveClass.AllNames[0]}')
        self.T_daily = int(DSSCircuit.ActiveCktElement.Properties("npts").val)
        self.Interval = float(DSSCircuit.ActiveCktElement.Properties("interval").val)
        self.dimx = self.T_daily * len(self.storage_names)
"""

Designer_example = '''
    ### Generated Indicator Function Examples

    #### Indicator Function Example 1: Calculate Line Voltage Deviation Risk
    ```python
    def targetfunction(self):
        """
        Indicator function: Calculate line voltage deviation risk.
        
        This method first creates voltage monitors for all lines, then solves the daily operation of the power system.
        Next, it iterates through each line, calculates the voltage deviation rate for each downstream node, and stores this data in a dictionary.
        Finally, it prints the voltage deviation for each node and phase.
        """
        # Initialize a dictionary to store voltage deviation for all line nodes
        # Set dictionary to store node voltage deviation
        self.voltage_deviation_all = {}
        
        # Create voltage monitors for each line
        # Add monitors for each line
        for i, name in enumerate(self.line_names):
            # Add line monitor
            DSSText.command = f'New Monitor.linemonitor{i} element=line.{name} 1 mode=0'
        
        # Solve power system and calculate daily operation, parameters are operation days, time step, and time range
        # Solve before obtaining monitoring data
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # Iterate through each line, calculate voltage deviation for each node and phase
        # Bus voltage summary
        for i, name in enumerate(self.line_names):
            # Specify current line name
            # Determine line according to line name
            DSSCircuit.lines.name = name
            # Get the second node name of current line
            # Find downstream node
            line_bus2 = DSSCircuit.lines.bus2
            # Activate second node
            # Activate downstream node
            DSSCircuit.SetActiveBus(line_bus2)
            # Get base voltage level of node
            # Extract voltage level corresponding to downstream node
            kVBase = DSSCircuit.ActiveBus.kVBase
            # Set voltage monitor name
            # Generate monitor name
            DSSMonitors.Name = 'linemonitor{}'.format(i)
            
            # Iterate through each phase of each line, calculate voltage deviation
            # Output node voltage deviation according to phase number of each line
            for j in range(1, self.line_phases[i]+1):
                # Get voltage reading from voltage monitor (phase voltage)
                # Calculate voltage per unit value
                voltage_pu = np.array(DSSMonitors.Channel(j*2-1)) / (1000 * kVBase)
                # Calculate voltage deviation rate
                # Calculate voltage deviation value
                voltage_pu_deviation = np.sum(abs(voltage_pu - 1)) / voltage_pu.shape[0]
                # Store node voltage deviation in dictionary
                # Store voltage deviation
                self.voltage_deviation_all[f'Node{line_bus2}Phase{j}DeviationRate'] = voltage_pu_deviation
                # Print voltage deviation for each node and phase
                # Output voltage deviation
                print(f'Node{line_bus2}Phase{j}VoltageDeviation: ', self.voltage_deviation_all[f'Node{line_bus2}Phase{j}DeviationRate'])
    ```
    
    #### Indicator Function Example 2: Power and Revenue of Energy Storage Devices in Peak-Valley Price Arbitrage
    ```python 
    def targetfunction(self, price):
        """
        Calculate power and revenue of energy storage devices in peak-valley price arbitrage.
        
        By monitoring the charging and discharging power of energy storage devices during daily peak and valley periods, calculate the potential revenue from peak-valley price arbitrage.
        
        Parameters:
        price: list - List containing peak and valley period electricity prices, peak price first, valley price second.
        """
        # Initialize a dictionary to store power and revenue data for all energy storage devices
        # Set dictionary to store energy storage power
        self.storage_power_all = {}
        
        # Create a monitor for each energy storage device to obtain charging and discharging power data
        # Add energy storage monitors
        for i, name in enumerate(self.storage_names):
            # Add energy storage monitor
            DSSText.command = f'New Monitor.storagemonitor{i} element=storage.{name} terminal=1 ppolar=no mode=1'
        
        # Solve optimization problem to determine optimal charging and discharging strategy for energy storage devices during peak and valley periods
        # Solve before obtaining monitoring data
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # Iterate through each energy storage device, calculate its charging and discharging power and arbitrage revenue during peak and valley periods
        # Calculate energy storage forward and reverse load power
        for i, name in enumerate(self.storage_names):
            # Set current monitor to corresponding energy storage device
            DSSMonitors.Name = 'storagemonitor{}'.format(i)
            
            # Calculate total power of energy storage device, including charging, discharging, and standby power
            storage_power = np.array(DSSMonitors.Channel(1)) + np.array(DSSMonitors.Channel(3)) + np.array(DSSMonitors.Channel(5))
            
            # Store power and arbitrage revenue of energy storage device
            self.storage_power_all[f'Storage{name}Power'] = storage_power
            self.storage_power_all[f'Storage{name}ArbitrageBenefit'] = np.sum(storage_power * price)
    ```

    #### Indicator Function Example 3: Calculate Peak-Valley Stability of Transformers with Energy Storage Devices
    ```python
    def targetfunction(self):
        """
        Calculate peak-valley stability of transformers with energy storage devices.
        
        This method first solves the daily load curve, then identifies transformers connected to energy storage devices.
        Next, create monitors for these transformers to obtain power data.
        Finally, solve the daily load curve to obtain power data during peak and valley periods, and calculate active and reactive power of transformers.
        """
        
        # Initialize dictionary to store transformer power data
        # Build dictionary to store transformer kW and kvar
        self.kWoftransformers = {}
        self.kvaroftransformers = {}
        
        # Initialize list to store names of transformers with energy storage devices
        self.trans_withstorage_name=[]
        
        # Solve daily load curve to prepare for subsequent calculations
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # Activate energy storage component class to obtain information about connected transformers
        # Activate energy storage component
        DSSCircuit.SetActiveClass('Storage')
        
        # Get names of all energy storage devices
        storage_names = DSSCircuit.ActiveClass.AllNames
        
        # Iterate through energy storage devices, create monitors for transformers associated with each device
        for i, storage_name in enumerate(storage_names):
            # Activate specific energy storage device
            DSSCircuit.SetActiveElement(f"Storage.{storage_name}")
            # Get the line node connected to the energy storage device
            bus_name = DSSCircuit.ActiveCktElement.Properties("bus1").val
            # Activate this node
            DSSCircuit.SetActiveBus(bus_name)
            # Get transformer information
            transformer = DSSCircuit.ActiveBus.AllPDEatBus
            # Extract transformer name, remove prefix
            transformer_name = transformer[0].replace('Transformer.','')
            # Add transformer name to list
            self.trans_withstorage_name.append(transformer_name)
            # Create monitor for subsequent power data acquisition
            DSSText.command = f'New monitor.trans_power{i} element=Transformer.{transformer_name}  terminal=1 ppolar=no mode=1'
        
        # Solve daily load curve again to obtain power data during peak and valley periods
        self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
        
        # Iterate through energy storage devices, obtain power data for transformers associated with each device
        # Calculate transformer forward and reverse load power
        for i, storage_name in enumerate(storage_names):
            # Activate specific energy storage device
            DSSCircuit.SetActiveElement(f"Storage.{storage_name}")
            # Get the node connected to the energy storage device
            bus_name = DSSCircuit.ActiveCktElement.Properties("bus1").val
            # Activate this node
            DSSCircuit.SetActiveBus(bus_name)
            # Get transformer information connected to this node
            transformer = DSSCircuit.ActiveBus.AllPDEatBus
            transformer_name = transformer[i].replace('Transformer.','')
            name = transformer_name
            
            # Use monitor to obtain transformer power data
            for j in range(3):
                # Get active and reactive power data from monitor
                transformerkw = np.array(DSSMonitors.Channel(j*2+1))
                transformerkvar = np.array(DSSMonitors.Channel(j*2+2))
                
                # Store power data in dictionary
                self.kWoftransformers[f'Transformer{name}Phase{j+1}ActivePower'] = transformerkw
                self.kvaroftransformers[f'Transformer{name}Phase{j+1}ReactivePower'] = transformerkvar
            
            # Calculate sum of three-phase power of transformer
            self.kWoftransformers[f'Transformer{name}ThreePhaseActivePowerSum'] = self.kWoftransformers[f'Transformer{name}Phase1ActivePower'] + \
                                                                                self.kWoftransformers[f'Transformer{name}Phase2ActivePower'] + \
                                                                                self.kWoftransformers[f'Transformer{name}Phase3ActivePower']
            self.kvaroftransformers[f'Transformer{name}ThreePhaseReactivePowerSum'] = self.kvaroftransformers[f'Transformer{name}Phase1ReactivePower'] + \
                                                                                    self.kvaroftransformers[f'Transformer{name}Phase2ReactivePower'] + \
                                                                                    self.kvaroftransformers[f'Transformer{name}Phase3ReactivePower']
    ```             
"""
'''

Designer_instruction = """
Let's start thinking step by step!
User instruction: {user_instruction}
Start!
""" 