#!/usr/bin/env python3
"""
简化的embedding性能测试
"""

import time
import asyncio
from rag_modules.embedding import (
    get_batch_embeddings,
    get_batch_embeddings_optimized,
    get_batch_embeddings_large_scale
)

def quick_test():
    """快速测试不同方法的性能"""
    
    # 测试不同规模的数据集
    test_cases = [
        {"size": 20, "desc": "小规模"},
        {"size": 100, "desc": "中规模"}, 
        {"size": 300, "desc": "大规模"}
    ]
    
    base_texts = [
        "人工智能技术发展迅速",
        "机器学习改变世界", 
        "深度学习神经网络",
        "自然语言处理应用",
        "计算机视觉识别",
        "数据科学分析方法",
        "云计算服务平台",
        "分布式系统架构",
        "软件工程最佳实践",
        "算法优化与性能调优"
    ]
    
    for test_case in test_cases:
        size = test_case["size"]
        desc = test_case["desc"]
        
        # 生成测试数据
        texts = (base_texts * (size // len(base_texts) + 1))[:size]
        
        print(f"\n{'='*50}")
        print(f"📊 {desc}测试 - {len(texts)}个文本")
        print(f"{'='*50}")
        
        # 1. 原始方法
        print("🔄 原始串行方法...", end="", flush=True)
        start = time.time()
        try:
            original_result = get_batch_embeddings(texts)
            original_time = time.time() - start
            print(f" ✅ {original_time:.2f}秒")
        except Exception as e:
            print(f" ❌ 失败: {e}")
            continue
        
        # 2. 优化并发方法  
        print("⚡ 优化并发方法...", end="", flush=True)
        start = time.time()
        try:
            optimized_result = get_batch_embeddings_optimized(texts)
            optimized_time = time.time() - start
            speedup_opt = original_time / optimized_time
            print(f" ✅ {optimized_time:.2f}秒 (提升 {speedup_opt:.2f}x)")
        except Exception as e:
            print(f" ❌ 失败: {e}")
            continue
            
        # 3. 大规模并发方法
        print("🚀 大规模并发方法...", end="", flush=True)
        start = time.time()
        try:
            large_scale_result = get_batch_embeddings_large_scale(
                texts, 
                max_workers=3,
                texts_per_worker=max(50, len(texts)//4)
            )
            large_scale_time = time.time() - start
            speedup_large = original_time / large_scale_time
            print(f" ✅ {large_scale_time:.2f}秒 (提升 {speedup_large:.2f}x)")
        except Exception as e:
            print(f" ❌ 失败: {e}")
            continue
        
        # 结果验证
        if (len(original_result) == len(optimized_result) == len(large_scale_result) and
            len(original_result[0]) == len(optimized_result[0]) == len(large_scale_result[0])):
            print("✅ 结果一致性验证通过")
        else:
            print("⚠️  结果不一致")
        
        # 性能总结
        print(f"\n📈 性能总结:")
        print(f"   原始方法: {original_time:.2f}秒 (基准)")
        print(f"   优化并发: {optimized_time:.2f}秒 ({speedup_opt:.2f}x)")
        print(f"   大规模并发: {large_scale_time:.2f}秒 ({speedup_large:.2f}x)")
        
        best_method = "原始方法"
        best_time = original_time
        if optimized_time < best_time:
            best_method = "优化并发"
            best_time = optimized_time
        if large_scale_time < best_time:
            best_method = "大规模并发"
            best_time = large_scale_time
            
        print(f"   🏆 最佳方法: {best_method} ({best_time:.2f}秒)")

def test_threshold_effect():
    """测试不同阈值设置的效果"""
    print(f"\n{'='*60}")
    print("🔬 阈值设置影响测试")
    print(f"{'='*60}")
    
    texts = ["测试文本 " + str(i) for i in range(150)]
    thresholds = [50, 100, 200, 300]
    
    print(f"测试数据: {len(texts)}个文本")
    
    for threshold in thresholds:
        print(f"\n📏 阈值设置: {threshold}")
        start = time.time()
        try:
            result = get_batch_embeddings_large_scale(
                texts,
                max_workers=3,
                texts_per_worker=threshold
            )
            elapsed = time.time() - start
            
            if len(texts) <= threshold:
                method_used = "串行 (低于阈值)"
            else:
                chunks = len(texts) // threshold + (1 if len(texts) % threshold else 0)
                method_used = f"并发 ({chunks}个块)"
                
            print(f"   方法: {method_used}")
            print(f"   耗时: {elapsed:.2f}秒")
            print(f"   效率: {len(texts)/elapsed:.1f}个文本/秒")
            
        except Exception as e:
            print(f"   失败: {e}")

if __name__ == "__main__":
    print("🚀 开始embedding性能优化测试")
    print("确保已设置 siliconflow_api_key 环境变量")
    
    try:
        quick_test()
        test_threshold_effect()
        
        print(f"\n{'='*60}")
        print("💡 优化建议:")
        print("• 50个以下文本: 使用原始方法")
        print("• 50-200个文本: 使用优化并发方法")  
        print("• 200个以上文本: 使用大规模并发方法")
        print("• 根据网络速度和API限制调整并发数")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
    
    print("\n✅ 测试完成")
