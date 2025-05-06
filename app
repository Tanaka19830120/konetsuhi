# 条件に基づき、住宅1軒分の冷暖房に必要なエネルギー量を計算するPythonコード

# 入力パラメータ（仮の数値で定義）
floor_area = 120  # 延床面積 m^2
Ua = 0.19         # 外皮平均熱貫流率 W/m^2K
volume = 288      # 容積 m^3（天井高2.4mを仮定）
ventilation_type = "第一種"  # または "第三種"
heat_recovery_rate = 0.75  # 熱交換率（第一種の場合）
C = 0.5           # C値 cm^2/m^2
wind_speed = 2    # 平均風速 m/s
dense_area = True  # 住宅密集地かどうか
deltaT_winter = 20  # 冬の温度差 °C
deltaT_summer = 5   # 夏の温度差 °C
days_heating = 120  # 暖房日数
days_cooling = 90   # 冷房日数
hours_per_day = 24  # 冷暖房時間 h

# 外皮熱損失の計算
Q_skin_winter = Ua * floor_area * deltaT_winter * hours_per_day * days_heating / 1000  # kWh
Q_skin_summer = Ua * floor_area * deltaT_summer * hours_per_day * days_cooling / 1000

# 換気による熱損失の計算
ventilation_rate = 0.5  # 回/h
air_density = 1.2  # kg/m^3
specific_heat_air = 0.33  # Wh/kgK

# 換気損失（換気による熱交換を考慮）
if ventilation_type == "第一種":
    heat_loss_rate = 1 - heat_recovery_rate
else:
    heat_loss_rate = 1.0

Q_vent_winter = ventilation_rate * volume * air_density * specific_heat_air * deltaT_winter * heat_loss_rate * hours_per_day * days_heating / 1000
Q_vent_summer = ventilation_rate * volume * air_density * specific_heat_air * deltaT_summer * heat_loss_rate * hours_per_day * days_cooling / 1000

# 漏気による熱損失（風速と住宅密集度を考慮）
leak_factor = 0.5 if dense_area else 1.0
leakage_volume = C * floor_area * wind_speed * leak_factor / 100  # m^3/h
Q_leak_winter = leakage_volume * air_density * specific_heat_air * deltaT_winter * hours_per_day * days_heating / 1000
Q_leak_summer = leakage_volume * air_density * specific_heat_air * deltaT_summer * hours_per_day * days_cooling / 1000

# 合計熱負荷
Q_total_winter = Q_skin_winter + Q_vent_winter + Q_leak_winter
Q_total_summer = Q_skin_summer + Q_vent_summer + Q_leak_summer
Q_total = Q_total_winter + Q_total_summer

import pandas as pd
import ace_tools as tools

# 結果を表形式で出力
df = pd.DataFrame({
    "項目": ["外皮損失 (冬)", "換気損失 (冬)", "漏気損失 (冬)", "外皮損失 (夏)", "換気損失 (夏)", "漏気損失 (夏)", "合計 (年間)"],
    "エネルギー[kWh]": [
        round(Q_skin_winter), round(Q_vent_winter), round(Q_leak_winter),
        round(Q_skin_summer), round(Q_vent_summer), round(Q_leak_summer),
        round(Q_total)
    ]
})

tools.display_dataframe_to_user(name="熱損失シミュレーション結果", dataframe=df)
