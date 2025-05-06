import streamlit as st
import pandas as pd

st.set_page_config(page_title="熱損失シミュレーター", layout="wide")
st.title("🏠 熱損失シミュレーター（2軒比較＋太陽光＆蓄電池）")

col1, col2 = st.columns(2)
house_params = {}
costs = {}

for idx, col in enumerate([col1, col2]):
    with col:
        name = "一条工務店" if idx == 0 else "その他の家"
        st.header(f"🏡 {name}")
        # 基本入力
        floor_area = st.number_input(f"[{name}] 延床面積 (m²)", 90.0, key=f"floor_area_{idx}")
        Ua = st.number_input(f"[{name}] Ua値 (W/m²K)", 0.19 if idx == 0 else 0.87, key=f"Ua_{idx}")
        volume = st.number_input(f"[{name}] 容積 (m³)", 288.0, key=f"volume_{idx}")
        ventilation_type = st.selectbox(f"[{name}] 換気方式", ["第一種", "第三種"], key=f"vent_type_{idx}")
        heat_recovery_rate = st.slider(f"[{name}] 熱交換率（第一種）", 0.0, 1.0, 0.75, key=f"heat_rec_{idx}")
        C = st.number_input(f"[{name}] C値 (cm²/m²)", 0.5 if idx == 0 else 2.0, key=f"C_{idx}")
        wind_speed = st.number_input(f"[{name}] 平均風速 (m/s)", 2.0, key=f"wind_{idx}")
        dense_area = st.selectbox(f"[{name}] 住宅密集地", ["はい", "いいえ"], key=f"dense_{idx}") == "はい"
        deltaT_winter = st.number_input(f"[{name}] 冬の温度差 (°C)", 20.0, key=f"dt_win_{idx}")
        deltaT_summer = st.number_input(f"[{name}] 夏の温度差 (°C)", 5.0, key=f"dt_sum_{idx}")
        days_heating = st.number_input(f"[{name}] 暖房日数", 120, key=f"days_heat_{idx}")
        days_cooling = st.number_input(f"[{name}] 冷房日数", 90, key=f"days_cool_{idx}")
        electric_rate = st.number_input(f"[{name}] 電気料金（円/kWh）", 27.0, key=f"elec_{idx}")
        # 追加入力：太陽光・蓄電池
        solar_capacity = st.number_input(f"[{name}] 太陽光容量 (kW)", 0.0, key=f"solar_cap_{idx}")
        battery_capacity = st.number_input(f"[{name}] 蓄電池容量 (kWh)", 0.0, key=f"bat_cap_{idx}")
        battery_eff = st.slider(f"[{name}] 蓄電池効率 (%)", 0, 100, 90, key=f"bat_eff_{idx}") / 100.0

        # 計算定数
        hours_per_day = 24.0
        ventilation_rate = 0.5
        air_density = 1.2
        specific_heat_air = 0.33

        # 1) 熱損失計算
        Q_skin_winter = Ua * floor_area * deltaT_winter * hours_per_day * days_heating / 1000
        Q_skin_summer = Ua * floor_area * deltaT_summer * hours_per_day * days_cooling / 1000
        heat_loss_rate = (1 - heat_recovery_rate) if ventilation_type == "第一種" else 1.0
        Q_vent_winter = ventilation_rate * volume * air_density * specific_heat_air * deltaT_winter * heat_loss_rate * hours_per_day * days_heating / 1000
        Q_vent_summer = ventilation_rate * volume * air_density * specific_heat_air * deltaT_summer * heat_loss_rate * hours_per_day * days_cooling / 1000
        leak_factor = 0.5 if dense_area else 1.0
        leakage_volume = C * floor_area * wind_speed * leak_factor / 100.0
        Q_leak_winter = leakage_volume * air_density * specific_heat_air * deltaT_winter * hours_per_day * days_heating / 1000
        Q_leak_summer = leakage_volume * air_density * specific_heat_air * deltaT_summer * hours_per_day * days_cooling / 1000
        Q_total = Q_skin_winter + Q_skin_summer + Q_vent_winter + Q_vent_summer + Q_leak_winter + Q_leak_summer

        # 2) 発電と蓄電計算
        solar_gen = solar_capacity * 3.5 * 365.0              # 年間発電量[kWh]
        battery_use = min(battery_capacity * battery_eff * 365.0, Q_total)   # 蓄電池からの年間供給量
        net_load = Q_total - solar_gen
        if net_load >= 0:
            grid_purchase = max(net_load - battery_use, 0.0)
            sell_back = 0.0
        else:
            sell_back = abs(net_load)
            grid_purchase = 0.0

        # 3) 費用計算
        cost_total = grid_purchase * electric_rate
        revenue = sell_back * electric_rate * 0.8  # 売電単価を電力単価の80%と仮定
        net_cost = cost_total - revenue

        # 結果格納
        house_params[name] = {
            "外皮損失 (冬)[kWh]": Q_skin_winter,
            "換気損失 (冬)[kWh]": Q_vent_winter,
            "漏気損失 (冬)[kWh]": Q_leak_winter,
            "外皮損失 (夏)[kWh]": Q_skin_summer,
            "換気損失 (夏)[kWh]": Q_vent_summer,
            "漏気損失 (夏)[kWh]": Q_leak_summer,
            "年間消費電力[kWh]": Q_total,
            "年間発電量[kWh]": solar_gen,
            "蓄電池使用量[kWh]": battery_use,
            "買電量[kWh]": grid_purchase,
            "売電量[kWh]": sell_back,
            "年間光熱費（円）": int(net_cost)
        }
        costs[name] = net_cost

# 表示
st.subheader("📊 年間熱損失＋電力収支比較")
df = pd.DataFrame(house_params).T.round(1)
df["年間光熱費（円）"] = df["年間光熱費（円）"].apply(lambda x: f"{x:,} 円")
st.dataframe(df, use_container_width=True)

# 差額表示
names = list(costs.keys())
if len(names) == 2:
    diff = costs[names[1]] - costs[names[0]]
    if diff > 0:
        st.success(f"💡 **{names[0]}** の方が **{int(diff):,} 円**／年 お得です！")
    elif diff < 0:
        st.success(f"💡 **{names[1]}** の方が **{int(-diff):,} 円**／年 お得です！")
    else:
        st.info("💡 両者の年間光熱費は同じです。")
