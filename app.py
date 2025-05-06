# 必要なライブラリ
import pandas as pd

# --- 入力パラメータ ---
floor_area = 120           # 延床面積 m^2
Ua = 0.19                  # 外皮平均熱貫流率 W/m^2K
volume = 288               # 容積 m^3（例: 天井高2.4m）
ventilation_type = "第一種"  # 換気方式 ("第一種" または "第三種")
heat_recovery_rate = 0.75  # 熱交換率（第一種のみ有効）
C = 0.5                    # C値 cm^2/m^2
wind_speed = 2             # 平均風速 m/s
dense_area = True          # 住宅密集地かどうか
deltaT_winter = 20         # 冬の温度差 °C
deltaT_summer = 5          # 夏の温度差 °C
days_heating = 120         # 暖房日数
days_cooling = 90          # 冷房日数
hours_per_day = 24         # 冷暖房使用時間（時間/日）
electric_rate = 27         # 電気単価（円/kWh）

# --- 固定定数 ---
ventilation_rate = 0.5        # 回/h
air_density = 1.2             # kg/m^3
specific_heat_air = 0.33      # Wh/kgK

# --- 外皮からの熱損失（冬・夏）---
Q_skin_winter = Ua * floor_area * deltaT_winter * hours_per_day * days_heating / 1000  # kWh
Q_skin_summer = Ua * floor_area * deltaT_summer * hours_per_day * days_cooling / 1000

# --- 換気による熱損失 ---
heat_loss_rate = 1 - heat_recovery_rate if ventilation_type == "第一種" else 1.0
Q_vent_winter = ventilation_rate * volume * air_density * specific_heat_air * deltaT_winter * heat_loss_rate * hours_per_day * days_heating / 1000
Q_vent_summer = ventilation_rate * volume * air_density * specific_heat_air * deltaT_summer * heat_loss_rate * hours_per_day * days_cooling / 1000

# --- 漏気による熱損失 ---
leak_factor = 0.5 if dense_area else 1.0
leakage_volume = C * floor_area * wind_speed * leak_factor / 100  # m³/h
Q_leak_winter = leakage_volume * air_density * specific_heat_air * deltaT_winter * hours_per_day * days_heating / 1000
Q_leak_summer = leakage_volume * air_density * specific_heat_air * deltaT_summer * hours_per_day * days_cooling / 1000

# --- 合計 ---
Q_total_winter = Q_skin_winter + Q_vent_winter + Q_leak_winter
Q_total_summer = Q_skin_summer + Q_vent_summer + Q_leak_summer
Q_total = Q_total_winter + Q_total_summer
total_cost = Q_total * electric_rate  # 円

# --- 結果出力 ---
df = pd.DataFrame({
    "項目": ["外皮損失 (冬)", "換気損失 (冬)", "漏気損失 (冬)",
           "外皮損失 (夏)", "換気損失 (夏)", "漏気損失 (夏)",
           "合計 (年間)", "年間光熱費（円）"],
    "エネルギー[kWh]・金額[円]": [
        round(Q_skin_winter), round(Q_vent_winter), round(Q_leak_winter),
        round(Q_skin_summer), round(Q_vent_summer), round(Q_leak_summer),
        round(Q_total), round(total_cost)
    ]
})

print(df)
