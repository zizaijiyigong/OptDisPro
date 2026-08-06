

# OptDisPro

Este repositorio contiene la implementación del código para el artículo **"OptDisPro: LLM-based Multi-agent Framework for Flexibly Adapting Heuristic Optimal DisFlow"**.

## Descripción general

Este proyecto tiene como objetivo lograr la generación, solución y ejecución automáticas del código de flujo de potencia óptimo para redes de distribución mediante sistemas multiagente basados en modelos de lenguaje grandes (LLM). El marco de trabajo aprovecha múltiples agentes inteligentes para manejar colaborativamente la compleja tarea de optimización del flujo de potencia en sistemas de distribución.

## Estado actual

**Nota**: Este artículo ha sido aceptado para su publicación en IEEE Transactions on Smart Grid. La base de código completa está ahora disponible, incluyendo:

- Plantillas de prompts para agentes (disponibles en versión china e inglesa)
- Implementación completa del sistema multiagente
- Código base de la red (Network_code.py)
- Código de prueba del flujo de trabajo principal (test_core_workflow.py)
- Muestras de código generado para diferentes objetivos de optimización
- Conjuntos de datos de prueba

## Prompts de los Agentes

Los prompts de los agentes se proporcionan en dos versiones:
- **Versión china**: Prompts originales escritos en chino
- **Versión inglesa**: Prompts traducidos al inglés

Los prompts originales se desarrollaron en chino y luego se tradujeron al inglés para una mayor accesibilidad.

## Ejemplos de generación de código

A continuación se muestran tres funciones objetivo de ejemplo generadas por el marco de trabajo para diferentes objetivos de optimización:

### 1. Maximizar la generación de energía fotovoltaica (PV)
**optimization_example_pv.py**  
Esta función objetivo tiene como objetivo maximizar la potencia total de salida de todos los sistemas fotovoltaicos en la red.
```python
def targetfunction(self):
    """
    Objective: Maximize total PV generation.
    """
    self.pv_generation = {}
    for i, name in enumerate(self.pvsystem_names):
        DSSText.command = f'New Monitor.pvmonitor{i} element=PVSystem.{name} terminal=1 mode=1'
    self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
    for i, name in enumerate(self.pvsystem_names):
        DSSMonitors.Name = f'pvmonitor{i}'
        pv_power = np.array(DSSMonitors.Channel(1))
        self.pv_generation[name] = np.sum(pv_power)
    self.total_pv_generation = sum(self.pv_generation.values())
    print('Total PV generation:', self.total_pv_generation)
```

### 2. Minimizar la tasa de sobrecarga del transformador
**optimization_example_trans.py**  
Esta función objetivo calcula y minimiza la tasa de sobrecarga de todos los transformadores en la red.
```python
def targetfunction(self):
    """
    Objective: Minimize transformer overload rate.
    """
    self.transformer_overload = {}
    for i, name in enumerate(self.transformer_names):
        DSSText.command = f'New Monitor.transmonitor{i} element=Transformer.{name} terminal=1 mode=1'
    self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
    for i, name in enumerate(self.transformer_names):
        DSSMonitors.Name = f'transmonitor{i}'
        transformer_power = np.array(DSSMonitors.Channel(1))
        DSSTransformers.Name = name
        rated_power = DSSTransformers.kva
        overload_rate = np.max(transformer_power) / rated_power
        self.transformer_overload[name] = overload_rate
    self.max_overload_rate = max(self.transformer_overload.values())
    print('Max transformer overload rate:', self.max_overload_rate)
```

### 3. Minimizar la desviación del voltaje del nodo (V)
**optimization_example_volt.py**  
Esta función objetivo calcula y minimiza la desviación del voltaje en todos los nodos de la red.
```python
def targetfunction(self):
    """
    Objective: Minimize node voltage deviation.
    """
    self.voltage_deviation = {}
    for i, name in enumerate(self.line_names):
        DSSText.command = f'New Monitor.linemonitor{i} element=line.{name} 1 mode=0'
    self.solve('Daily', 50, '[10, 0.4]', self.T_daily)
    for i, name in enumerate(self.line_names):
        DSSCircuit.lines.name = name
        line_bus2 = DSSCircuit.lines.bus2
        DSSCircuit.SetActiveBus(line_bus2)
        kVBase = DSSCircuit.ActiveBus.kVBase
        DSSMonitors.Name = f'linemonitor{i}'
        for j in range(1, self.line_phases[i]+1):
            voltage_pu = np.array(DSSMonitors.Channel(j*2-1)) / (1000 * kVBase)
            voltage_deviation = np.sum(abs(voltage_pu - 1)) / voltage_pu.shape[0]
            self.voltage_deviation[f'Node{line_bus2}Phase{j}'] = voltage_deviation
    self.max_voltage_deviation = max(self.voltage_deviation.values())
    print('Max node voltage deviation:', self.max_voltage_deviation)
```

## Resumen del artículo

OptDisPro propone un nuevo marco de trabajo multiagente que utiliza modelos de lenguaje grandes para adaptar y generar de manera flexible soluciones heurísticas óptimas de flujo de distribución. El sistema emplea múltiples agentes especializados que trabajan en coordinación para automatizar el proceso tradicionalmente manual de desarrollo y ejecución de código para la optimización del flujo de potencia.

## Estructura del repositorio

El repositorio contiene:
- `agent/` - Implementación de agentes y plantillas de prompts
  - `prompt/` - Prompts para agentes (versiones en chino e inglés)
  - `multi_agent_system.py` - Implementación completa del sistema multiagente
- `Network_code.py` - Código base de la red para la integración con DSS
- `test_core_workflow.py` - Prueba y validación del flujo de trabajo principal
- `optimization_example_*.py` - Ejemplos de generación de código para diferentes objetivos
- `dssdata/` - Conjuntos de datos de prueba y datos de red
- Documentación (README.md)

## Referencia bibliográfica

Si utiliza este trabajo en su investigación, cite nuestro artículo:

```bibtex
@ARTICLE{11201936,
  author={Li, Zhengbo and Yang, Haolan and Liu, Youbo and Xiang, Yue and Gao, Hongjun and Liu, Jingyao and Liu, Junyong},
  journal={IEEE Transactions on Smart Grid},
  title={OptDisPro: LLM-based Multi-agent Framework for Flexibly Adapting Heuristic Optimal DisFlow},
  year={2025},
  volume={},
  number={},
  pages={1-1},
  keywords={Optimization;Codes;Encoding;Distribution networks;Heuristic algorithms;Adaptation models;Power system stability;Load flow;Complexity theory;Power system reliability;Artificial Intelligence;Large Language Models;Multi-agent Framework;Optimal Power Flow},
  doi={10.1109/TSG.2025.3620496}
}
```

## Contacto

Para preguntas sobre esta implementación, consulte a los autores del artículo o abra un problema (issue) en este repositorio.
