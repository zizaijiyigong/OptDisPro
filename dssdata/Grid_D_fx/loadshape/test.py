import os
import pandas as pd


def extract_csv_data(folder_path):
    # 获取文件夹内所有文件名
    files = os.listdir(folder_path)
    # 过滤出CSV文件
    csv_files = [file for file in files if file.endswith('.csv')]

    # 创建一个空的DataFrame来存储所有数据
    combined_data = pd.DataFrame()

    # 遍历所有CSV文件并读取数据
    for csv_file in csv_files:
        file_path = os.path.join(folder_path, csv_file)
        data = pd.read_csv(file_path)
        combined_data = pd.concat([combined_data, data], ignore_index=True)

    return combined_data


# 使用示例
folder_path = '你的文件夹路径'
all_data = extract_csv_data(folder_path)
print(all_data)
