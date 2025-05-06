import streamlit as st
import pandas as pd

st.set_page_config(page_title="熱損失シミュレーター", layout="centered")
st.title("🏠 熱損失シミュレーター（1軒分）")

# 入力フォーム
with st.sidebar:
    st.header("📌 入力パラメータ")
    floor_area = st.number_input("延床面積 (m²)", value=120)
    Ua = st.number_input("Ua値 (W/m²K)", value=0.19)
    volume = st.number_input("容積 (m³)", value=288)
    ventilation_type = st.selectbox("換気方式", ["第一種", "第三種"])
    heat_recovery_rate = st.slider("熱交換率（第一種換気）", 0.0, 1.0, 0.75)
    C = st.number_input("C値 (cm²/m²)", value=0.5)
    wind_speed = st.number_input("平均風速 (m/s)", value=2.0)
    dense_area = st.selectbox("住宅密集地", ["はい", "いいえ"]) == "はい"
    deltaT_winter = st.number_input("冬の温度差 (°C)", value=20)
    deltaT_summer = st.number_input("夏の温度差 (°C)", value=5)
    days_heating = st.number_input("暖房日数", value=120)
    days_cooling = st.number_input("冷房日数", value=90)
    electric_rate = st.number_input("電気料金（円/kWh）", value=27.0)
    hours_per_day = 24

# 計算
Q_skin_winter = Ua * floor_area * deltaT_winter * hours_per_day * days_heating / 1000
Q_skin_summer = Ua * floor_area * deltaT_summer * hours_per_day * days_cooling / 1000

ventilation_rate = 0.5  # 回/h
air_density = 1.2  # kg/m³
specific_heat_air = 0.33  # Wh/kgK
heat_loss_rate = 1 - heat_recovery_rate if ventilation_type == "第一種" else 1.0

Q_vent_winter = ventilation_rate * volume * air_density * specific_heat_air * deltaT_winter * heat_loss_rate * hours_per_day * days_heating / 1000
Q_vent_summer = ventilation_rate * volume * air_density * specific_heat_air * deltaT_summer * heat_loss_rate * hours_per_day * days_cooling / 1000

leak_factor = 0.5 if dense_area else 1.0
leakage_volume = C * floor_area * wind_speed * leak_factor / 100  # m³/h
Q_leak_winter = leakage_volume * air_density * specific_heat_air * deltaT_winter * hours_per_day * days_heating / 1000
Q_leak_summer = leakage_volume * air_density * specific_heat_air * deltaT_summer * hours_per_day * days_cooling / 1000

Q_total_winter = Q_skin_winter + Q_vent_winter + Q_leak_winter
Q_total_summer = Q_skin_summer + Q_vent_summer + Q_leak_summer
Q_total = Q_total_winter + Q_total_summer
cost_total = Q_total * electric_rate  # 円換算

# 結果表
df = pd.DataFrame({
    "項目": [
        "外皮損失 (冬)", "換気損失 (冬)", "漏気損失 (冬)",
        "外皮損失 (夏)", "換気損失 (夏)", "漏気損失 (夏)",
        "合計 (年間)", "年間光熱費（円）"
    ],
    "値": [
        round(Q_skin_winter), round(Q_vent_winter), round(Q_leak_winter),
        round(Q_skin_summer), round(Q_vent_summer), round(Q_leak_summer),
        round(Q_total), f"{int(cost_total):,}"
    ]
})

st.subheader("📊 年間の熱損失エネルギーと光熱費")
st.dataframe(df, use_container_width=True)
