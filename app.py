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

        # 床面積と天井高さを入力し、容積を自動計算
        floor_area = st.number_input(
            f"[{name}] 延床面積 (m²)", 0.0, 9999.0, 90.0, step=0.1, key=f"floor_area_{idx}"
        )
        ceiling_height = st.number_input(
            f"[{name}] 天井高さ (m)", 0.0, 10.0, 2.5, step=0.1, key=f"ceiling_{idx}"
        )
        volume = floor_area * ceiling_height  # 容積 (m³)

        Ua = st.number_input(
            f"[{name}] Ua値 (W/m²K)", 0.0, 10.0, (0.19 if idx == 0 else 0.87),
            step=0.01, key=f"Ua_{idx}"
        )
        ventilation_type = st.selectbox(
            f"[{name}] 換気方式", ["第一種", "第三種"], key=f"vent_type_{idx}"
        )
        heat_recovery_rate = st.slider(
            f"[{name}] 熱交換率（第一種換気）", 0.0, 1.0, 0.75, key=f"heat_rec_{idx}"
        )
        C = st.number_input(
            f"[{name}] C値 (cm²/m²)", 0.0, 100.0, (0.5 if idx == 0 else 2.0),
            step=0.1, key=f"C_{idx}"
        )
        wind_speed = st.number_input(
            f"[{name}] 平均風速 (m/s)", 0.0, 20.0, 2.0, step=0.1, key=f"wind_{idx}"
        )
        dense_area = (
            st.selectbox(f"[{name}] 住宅密集地", ["はい", "いいえ"], key=f"dense_{idx}") == "はい"
        )
        deltaT_winter = st.number_input(
            f"[{name}] 冬の温度差 (°C)", 0.0, 50.0, 20.0, step=0.5, key=f"dt_win_{idx}"
        )
        deltaT_summer = st.number_input(
            f"[{name}] 夏の温度差 (°C)", 0.0, 50.0, 5.0, step=0.5, key=f"dt_sum_{idx}"
        )
        days_heating = st.number_input(
            f"[{name}] 暖房日数", 0, 365, 120, step=1, key=f"days_heat_{idx}"
        )
        days_cooling = st.number_input(
            f"[{name}] 冷房日数", 0, 365, 90, step=1, key=f"days_cool_{idx}"
        )
        electric_rate = st.number_input(
            f"[{name}] 電気料金（円/kWh)", 0.0, 100.0, 27.0, step=0.1, key=f"elec_{idx}"
        )

        solar_capacity = st.number_input(
            f"[{name}] 太陽光容量 (kW)", 0.0, 100.0, 0.0, step=0.1, key=f"solar_{idx}"
        )
        battery_capacity = st.number_input(
            f"[{name}] 蓄電池容量 (kWh)", 0.0, 1000.0, 0.0, step=0.1, key=f"batcap_{idx}"
        )
        battery_eff = st.slider(
            f"[{name}] 蓄電池効率 (%)", 0, 100, 90, key=f"bateff_{idx}"
        ) / 100.0

        # 定数
        hours_per_day = 24.0
        ventilation_rate = 0.5
        air_density = 1.2
        specific_heat_air = 0.33
        gen_hours = 3.5  # 日射可能時間（h/日）

        # 熱損失計算
        Q_skin_w = Ua * floor_area * deltaT_winter * hours_per_day * days_heating / 1000
        Q_skin_s = Ua * floor_area * deltaT_summer * hours_per_day * days_cooling / 1000
        heat_loss_rate = (1 - heat_recovery_rate) if ventilation_type == "第一種" else 1.0
        Q_vent_w = ventilation_rate * volume * air_density * specific_heat_air * deltaT_winter * heat_loss_rate * hours_per_day * days_heating / 1000
        Q_vent_s = ventilation_rate * volume * air_density * specific_heat_air * deltaT_summer * heat_loss_rate * hours_per_day * days_cooling / 1000
        leak_factor = 0.5 if dense_area else 1.0
        leak_vol = C * floor_area * wind_speed * leak_factor / 100
        Q_leak_w = leak_vol * air_density * specific_heat_air * deltaT_winter * hours_per_day * days_heating / 1000
        Q_leak_s = leak_vol * air_density * specific_heat_air * deltaT_summer * hours_per_day * days_cooling / 1000
        Q_total = Q_skin_w + Q_skin_s + Q_vent_w + Q_vent_s + Q_leak_w + Q_leak_s

        # 2) 発電と自家消費→蓄電→夜間放電
        solar_gen = solar_capacity * gen_hours * 365  # 年間発電量[kWh]
        Q_day = Q_total * (gen_hours / 24.0)         # 日中消費量
        Q_night = Q_total - Q_day                   # 夜間消費量

        # 日中：発電で消費を賄い、残りは蓄電
        use_from_solar = min(solar_gen, Q_day)
        surplus_solar = max(solar_gen - use_from_solar, 0.0)
        # 蓄電池にためられる量
        battery_store = min(surplus_solar, battery_capacity * battery_eff * 365)
        # 夜間：蓄電池から放電して消費を賄う
        use_from_battery = min(battery_store, Q_night)
        # 売電量：日中余剰で蓄電庫オーバー分
        sell_back = surplus_solar - battery_store
        # 買電量：日中不足分＋夜間不足分
        day_purchase = max(Q_day - use_from_solar, 0.0)
        night_purchase = max(Q_night - use_from_battery, 0.0)
        grid_purchase = day_purchase + night_purchase

        # 3) 光熱費計算
        cost_total = grid_purchase * electric_rate
        revenue = sell_back * electric_rate * 0.8
        net_cost = cost_total - revenue

        house_params[name] = {
            "年間消費[kWh]": Q_total,
            "年間発電量[kWh]": solar_gen,
            "日中消費[kWh]": Q_day,
            "夜間消費[kWh]": Q_night,
            "日中自家消費[kWh]": use_from_solar,
            "蓄電量[kWh]": battery_store,
            "夜間放電量[kWh]": use_from_battery,
            "買電量[kWh]": grid_purchase,
            "売電量[kWh]": sell_back,
            "年間光熱費(円)": int(net_cost)
        }
        costs[name] = net_cost

# 表示
st.subheader("📊 年間熱損失＋電力収支比較")
df = pd.DataFrame(house_params).T.round(1)
df["年間光熱費(円)"] = df["年間光熱費(円)"].apply(lambda x: f"{x:,} 円")
st.dataframe(df, use_container_width=True)

# 差額表示
names = list(costs.keys())
if len(names) == 2:
    diff = costs[names[1]] - costs[names[0]]
    if diff > 0:
        st.success(f"💡 {names[0]} が {int(diff):,} 円/年 お得です！")
    elif diff < 0:
        st.success(f"💡 {names[1]} が {int(-diff):,} 円/年 お得です！")
    else:
        st.info("💡 両者同額です。")

