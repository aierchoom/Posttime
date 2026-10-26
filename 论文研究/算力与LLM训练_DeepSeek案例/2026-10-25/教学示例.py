"""CPU-only arithmetic illustrations. No model training benchmark or DeepSeek reproduction."""
import math


def gradient_demo():
    print('单参数二分类：目标=1，学习率=0.1；不是LLM实验')
    w = 0.0
    for step in range(6):
        p = 1 / (1 + math.exp(-w))
        loss = -math.log(p)
        grad = p - 1
        print(f'step={step} w={w:.6f} p={p:.6f} loss={loss:.6f} gradient={grad:.6f}')
        w -= 0.1 * grad


def resource_demo():
    print('\n假设情景：仅6*N_active*D主项，BF16权重；不含注意力、KV、状态或通信')
    scenarios = [('A', 1e12, 50e9, 1e12), ('B', 2e12, 50e9, 1e12),
                 ('C', 2e12, 100e9, 1e12), ('D', 2e12, 100e9, 2e12)]
    baseline = 6 * scenarios[0][2] * scenarios[0][3]
    for name, total, active, tokens in scenarios:
        flops = 6 * active * tokens
        print(f'{name}: FLOP={flops:.3e} ratio={flops/baseline:.1f}, '
              f'weights_decimal_TB={total*2/1e12:.1f}')
    print('\n固定batch=4096 token，top-k=2：假设路由完全均衡')
    for experts in (8, 16, 32):
        print(f'experts={experts}, assignments_per_expert={4096*2/experts:.0f}')


if __name__ == '__main__':
    gradient_demo()
    resource_demo()
