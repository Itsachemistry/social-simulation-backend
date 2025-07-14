#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数对比实验脚本（复用 test_with_config.py 流程和数据加载）
"""
import sys
import os
from io import StringIO
from contextlib import redirect_stdout
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

import test_with_config

# 参数组合
w_pop_values = [0.3, 0.5, 0.7, 0.8]
k_values = [1, 2, 3]

results_dir = "experiment_results"
os.makedirs(results_dir, exist_ok=True)

def run_single_experiment(w_pop, k, output_file):
    # 重定向stdout到StringIO
    output_buffer = StringIO()
    try:
        with redirect_stdout(output_buffer):
            # 运行主流程，传递参数
            test_with_config.main(
                w_pop=w_pop,
                k=k,
                save_log=False  # 控制主流程不重复保存日志
            )
    except Exception as e:
        print(f"实验运行出错: {e}")
        import traceback
        traceback.print_exc()
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"=== 参数对比实验 ===\n")
        f.write(f"实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参数配置: w_pop={w_pop}, k={k}\n")
        f.write(f"{'='*50}\n\n")
        f.write(output_buffer.getvalue())
    output_buffer.close()
    print(f"实验结果已保存到: {output_file}")

def run_all_experiments():
    total = len(w_pop_values) * len(k_values)
    idx = 0
    for w_pop in w_pop_values:
        for k in k_values:
            idx += 1
            filename = f"result_wpop{w_pop}_k{k}.txt"
            output_path = os.path.join(results_dir, filename)
            print(f"[{idx}/{total}] 运行参数: w_pop={w_pop}, k={k}")
            run_single_experiment(w_pop, k, output_path)
    print(f"\n所有实验完成！结果保存在 {os.path.abspath(results_dir)}")

if __name__ == "__main__":
    run_all_experiments() 