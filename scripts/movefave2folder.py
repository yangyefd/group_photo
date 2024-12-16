import os
import shutil

import os
import shutil

def move_files_to_folders_based_on_name(directory):
    # 遍历给定目录下的所有文件
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # 确保我们只处理文件，而不是已经存在的文件夹
        if os.path.isfile(file_path):
            # 分离文件名和扩展名
            name_without_extension, _ = os.path.splitext(filename)
            
            # 创建目标文件夹路径
            target_folder = os.path.join(directory, name_without_extension)
            
            # 如果目标文件夹不存在，则创建
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
                print(f"Created folder: {target_folder}")
            
            # 定义目标文件路径
            target_file_path = os.path.join(target_folder, filename)
            
            try:
                # 尝试移动文件
                shutil.move(file_path, target_file_path)
                print(f"Moved file to: {target_file_path}")
            except Exception as e:
                print(f"Failed to move the file: {e}")

# 示例用法
directory_to_process = 'images/MSE-p/个人'  # 替换为你的目录路径
move_files_to_folders_based_on_name(directory_to_process)
