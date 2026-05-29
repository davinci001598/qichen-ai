"""
连续记忆流 vs 离散存储 — 零依赖版
只用 numpy + matplotlib，手写 Euler 法求解 ODE，无需 torch/torchdiffeq
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

# 参数
MEMORY_DIM = 10
TIME_POINTS = 100
DECAY_RATE = 0.1
EXTERNAL_STRENGTH = 0.05
SEED = 42

np.random.seed(SEED)

OUT_DIR = "continuous_memory_output"
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================
# 1. 连续记忆流 — 手写 Euler 法求解 ODE
# ============================================

t = np.linspace(0, 10, TIME_POINTS)
dt = t[1] - t[0]

# 内部关联矩阵（记忆之间的相互影响）
connection = np.random.randn(MEMORY_DIM, MEMORY_DIM) * 0.1

# 外部输入模式
external_pattern = np.random.randn(MEMORY_DIM) * 0.05

# 初始记忆
continuous = np.zeros((TIME_POINTS, MEMORY_DIM))
continuous[0] = np.random.randn(MEMORY_DIM) * 0.5

for i in range(1, TIME_POINTS):
    m = continuous[i-1]
    ti = t[i-1]
    
    # ODE: dm/dt = -decay*m + connection*m + external_input(t)
    decay = -DECAY_RATE * m
    interaction = connection @ m
    external = EXTERNAL_STRENGTH * external_pattern * (0.5 + 0.5 * np.sin(ti * 2 * np.pi / 20))
    
    dm_dt = decay + interaction + external
    continuous[i] = m + dm_dt * dt

# ============================================
# 2. 离散存储 — 向量数据库式
# ============================================

discrete = np.zeros((TIME_POINTS, MEMORY_DIM))
discrete[0] = continuous[0].copy()

storage_points = list(range(0, TIME_POINTS, 5))
current = discrete[0].copy()

for i in range(TIME_POINTS):
    if i in storage_points:
        current = current * 0.8 + np.random.randn(MEMORY_DIM) * 0.2
    discrete[i] = current.copy()

# ============================================
# 3. 可视化
# ============================================

# 3.1 三合一对比图
fig, axes = plt.subplots(3, 1, figsize=(12, 15))

ax = axes[0]
for d in range(MEMORY_DIM):
    ax.plot(t, continuous[:, d], alpha=0.6, lw=1.2)
ax.set_title('连续记忆流（神经ODE — Euler法）', fontsize=14, fontweight='bold')
ax.set_xlabel('时间 t'); ax.set_ylabel('记忆强度')
ax.grid(True, alpha=0.3)
ax.text(0.02, 0.98, '平滑流动 · 持续存在 · 相互影响',
        transform=ax.transAxes, va='top', fontsize=10,
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

ax = axes[1]
for d in range(MEMORY_DIM):
    ax.plot(t, discrete[:, d], alpha=0.6, lw=1.2, drawstyle='steps-post')
ax.set_title('离散存储（向量数据库式）', fontsize=14, fontweight='bold')
ax.set_xlabel('时间 t'); ax.set_ylabel('记忆强度')
ax.grid(True, alpha=0.3)
ax.text(0.02, 0.98, '阶梯状 · 只在存储点变化 · 其余时间静止',
        transform=ax.transAxes, va='top', fontsize=10,
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

ax = axes[2]
ax.plot(t, continuous[:, 0], 'b-', lw=2.5, alpha=0.8, label='连续记忆流')
ax.plot(t, discrete[:, 0], 'r--', lw=2, alpha=0.8, label='离散存储')
ax.set_title('对比：连续流 vs 离散（第一维度）', fontsize=14, fontweight='bold')
ax.set_xlabel('时间 t'); ax.set_ylabel('记忆强度')
ax.legend(fontsize=12); ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'memory_flow_comparison.png'), dpi=200)

# 3.2 连续流单独
fig, ax = plt.subplots(figsize=(10, 6))
for d in range(MEMORY_DIM):
    ax.plot(t, continuous[:, d], alpha=0.5, lw=1.5)
ax.set_title('连续记忆流 — 全部 10 个维度', fontsize=14, fontweight='bold')
ax.set_xlabel('时间 t'); ax.set_ylabel('记忆强度')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'continuous_memory_flow.png'), dpi=200)
plt.close()

# 3.3 离散单独
fig, ax = plt.subplots(figsize=(10, 6))
for d in range(MEMORY_DIM):
    ax.plot(t, discrete[:, d], alpha=0.5, lw=1.5, drawstyle='steps-post')
ax.set_title('离散存储 — 全部 10 个维度', fontsize=14, fontweight='bold')
ax.set_xlabel('时间 t'); ax.set_ylabel('记忆强度')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'discrete_memory_storage.png'), dpi=200)
plt.close()

# ============================================
# 4. 量化对比
# ============================================
d_cont = np.diff(continuous, axis=0)
d_disc = np.diff(discrete, axis=0)

metrics = {
    "平均变化幅度": (float(np.mean(np.abs(d_cont))), float(np.mean(np.abs(d_disc)))),
    "变化连续性（自相关）": (
        float(np.corrcoef(d_cont[:-1, 0], d_cont[1:, 0])[0, 1]),
        float(np.corrcoef(d_disc[:-1, 0], d_disc[1:, 0])[0, 1]),
    ),
    "记忆持久性（滞后自相关）": (
        float(np.corrcoef(continuous[:-1, 0], continuous[1:, 0])[0, 1]),
        float(np.corrcoef(discrete[:-1, 0], discrete[1:, 0])[0, 1]),
    ),
    "总路径长度": (
        float(np.sum(np.sqrt(np.sum(d_cont**2, axis=1)))),
        float(np.sum(np.sqrt(np.sum(d_disc**2, axis=1)))),
    ),
}

print("=" * 60)
print("连续记忆流 vs 离散存储 — 量化对比")
print("=" * 60)
for name, (c, d) in metrics.items():
    diff = (c - d) / abs(d) * 100 if d != 0 else float('inf')
    print(f"\n{name}:")
    print(f"  连续: {c:.4f}  离散: {d:.4f}  差异: {diff:+.1f}%")

print(f"\n图片已保存: {OUT_DIR}/")
print("  continuous_memory_flow.png")
print("  discrete_memory_storage.png")
print("  memory_flow_comparison.png")

# 保存数据
with open(os.path.join(OUT_DIR, 'experiment_data.json'), 'w') as f:
    json.dump({
        "params": {"dim": MEMORY_DIM, "points": TIME_POINTS, "decay": DECAY_RATE},
        "continuous": continuous.tolist(),
        "discrete": discrete.tolist(),
        "time": t.tolist(),
        "metrics": {k: {"连续": v[0], "离散": v[1]} for k, v in metrics.items()}
    }, f, indent=2, ensure_ascii=False)

print("\ndone.")