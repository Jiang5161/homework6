import numpy as np
import matplotlib.pyplot as plt
import math

# --- 1. 参数定义 ---
BUILDING_LEN = 100.0  # 长 (X轴)
BUILDING_WID = 80.0   # 宽 (Y轴)
CORRIDOR_Y = 40.0     # 走廊中心Y坐标
CORRIDOR_W = 2.0      # 走廊宽度

# 墙体参数
ATTEN承重 = 12   # dB
ATTEN_PARTITION = 6  # dB
ATTEN_GLASS = 7    # dB

# AP 参数
TX_POWER = 20.0      # 发射功率 20dBm (100mW)
TARGET_RSSI = -65    # 目标边缘场强
FREQ_MHZ = 5000      # 5GHz

# --- 2. 传播模型 ---
def calculate_rssi(distance, wall_loss):
    """
    计算 RSSI
    """
    if distance < 0.1:
        distance = 0.1  # 防止除以0或log(0)

    # 自由空间路径损耗公式: PL(dB) = 32.4 + 20log10(f) + 20log10(d)
    pl_fs = 32.4 + 20 * math.log10(FREQ_MHZ) + 20 * math.log10(distance / 1000.0)

    # 总损耗 = 路径损耗 + 墙体损耗
    total_loss = pl_fs + wall_loss

    rssi = TX_POWER - total_loss
    return rssi

# --- 3. 墙体检测逻辑 (优化版) ---
def check_walls(ap_x, ap_y, target_x, target_y):
    """
    简化版射线检测：计算从 AP 到目标点穿过了多少堵墙
    """
    wall_loss = 0.0

    # 1. 检查是否穿过走廊墙壁 (进入教室)
    # 走廊范围: 39 ~ 41
    # 如果 AP 在走廊，目标在教室，必须穿过 y=39 或 y=41
    in_corridor_ap = (39 <= ap_y <= 41)
    in_corridor_target = (39 <= target_y <= 41)

    if in_corridor_ap and not in_corridor_target:
        # 简单模型：只要进出走廊，算穿过 1 堵普通隔断
        wall_loss += ATTEN_PARTITION

    # 2. 检查承重墙 (X轴方向每15米一堵)
    # 计算 AP 和 目标点 之间跨越了多少个 15m 的边界
    x_step = 15.0
    # 找到 AP 和目标点所在的区间索引
    idx_ap = int(ap_x // x_step)
    idx_target = int(target_x // x_step)

    # 跨越的墙数量 = 索引差的绝对值
    # 注意：如果正好在边界上，逻辑需要微调，这里简化处理
    walls_crossed = abs(idx_ap - idx_target)
    wall_loss += walls_crossed * ATTEN承重

    # 3. 玻璃幕墙 (外围) - 这里简化处理，仅当点在边缘时增加损耗
    # 实际部署中，边缘点通常不计算额外的“穿透”损耗，除非是从外向内
    # 此处暂忽略外围玻璃对内部覆盖的影响，或者视为安全余量

    return wall_loss

# --- 4. 部署规划 ---
def plan_ap_deployment():
    # 根据题目：5GHz 穿透1堵承重墙(12dB) 半径 58m
    # 走廊直线覆盖距离应该远大于此。
    # 100m 长度，部署 2 个 AP 比较稳妥，分别位于 1/3 和 2/3 处。
    ap_positions = [
        (33.0, CORRIDOR_Y),
        (66.0, CORRIDOR_Y)
    ]
    return ap_positions

# --- 5. 热力图生成 ---
def generate_heatmap(aps):
    resolution = 1.0
    x = np.arange(0, BUILDING_LEN + resolution, resolution)
    y = np.arange(0, BUILDING_WID + resolution, resolution)
    X, Y = np.meshgrid(x, y)

    # 初始化为很低的信号值，而不是 0
    # 这样如果计算出的信号是 -80，它也能更新上去
    Z = np.full_like(X, -100.0, dtype=float)

    print(f"{'AP_ID':<5} {'X(m)':<8} {'Y(m)':<8} {'Ch_2.4G':<8} {'Ch_5G':<8}")
    for i, (ap_x, ap_y) in enumerate(aps):
        ch_24 = [1, 6, 11][i % 3]
        ch_5 = [36, 149, 161][i % 3]
        print(f"{i+1:<5} {ap_x:<8.1f} {ap_y:<8.1f} {ch_24:<8} {ch_5:<8}")

        # 遍历网格计算信号 (为了演示清晰使用循环，实际可用向量化加速)
        for xi in range(len(x)):
            for yi in range(len(y)):
                tx = X[yi, xi]
                ty = Y[yi, xi]

                dist = math.sqrt((tx - ap_x)**2 + (ty - ap_y)**2)
                walls = check_walls(ap_x, ap_y, tx, ty)
                rssi = calculate_rssi(dist, walls)

                # 取所有 AP 中的最强信号
                if rssi > Z[yi, xi]:
                    Z[yi, xi] = rssi

    # --- 绘图 ---
    plt.figure(figsize=(12, 8))

    # 设置颜色条范围，-90 到 -30 是典型的 Wi-Fi 信号范围
    # 如果数据全是 NaN 或 0，这里会显示空白，所以前面的初始化很重要
    levels = np.linspace(-90, -30, 20)
    cp = plt.contourf(X, Y, Z, levels=levels, cmap='jet', extend='both')
    plt.colorbar(cp, label='Signal Strength (dBm)')

    # 绘制建筑结构
    # 走廊
    plt.axhspan(39, 41, color='white', alpha=0.3, label='Corridor')
    # 教室网格
    for x_wall in np.arange(0, 101, 15):
        plt.axvline(x_wall, color='gray', linestyle='--', alpha=0.4, linewidth=1)
    for y_wall in np.arange(0, 81, 10):
        if abs(y_wall - 40) > 1:
            plt.axhline(y_wall, color='gray', linestyle='--', alpha=0.4, linewidth=1)

    # 绘制 AP
    for ap_x, ap_y in aps:
        plt.plot(ap_x, ap_y, 'k+', markersize=15, markeredgewidth=3, label='AP Location')

    plt.title(f'Wi-Fi Signal Heatmap (5GHz)\n{len(aps)} APs Deployed', fontsize=16)
    plt.xlabel('Length (m)', fontsize=12)
    plt.ylabel('Width (m)', fontsize=12)
    plt.xlim(0, 100)
    plt.ylim(0, 80)
    plt.legend(loc='upper right')
    plt.grid(False) # 关闭默认网格，使用绘制的建筑线
    plt.tight_layout()
    plt.show()

# --- 主程序 ---
if __name__ == "__main__":
    print("--- AP 部署方案 ---")
    aps = plan_ap_deployment()
    print("------------------")
    generate_heatmap(aps)