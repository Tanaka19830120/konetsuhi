import streamlit as st
import pandas as pd

st.set_page_config(page_title="熱損失シミュレーター", layout="wide")
st.title("🏠 熱損失シミュレーター（2軒比較＋太陽光＆蓄電池＋時間帯別料金）")

# 全体設定：昼・夜の単価と売電単価
st.sidebar.header("🔌 電気料金設定")
day_rate   = st.sidebar.number_input("昼間電気料金（円/kWh）", min_value=0.0, value=28.87, step=0.01)
night_rate = st.sidebar.number_input("夜間電気料金（円/kWh）", min_value=0.0, value=15.37, step=0.01)
sell_rate  = st.sidebar.number_input("売電単価（円/kWh）",   min_value=0.0, value=16.00, step=0.01)

col1, col2 = st.columns(2)
house_params = {}
costs = {}

for idx, col in enumerate([col1, col2]):
    with col:
        name = "一条工務店" if idx == 0 else "他の家"
        st.header(f"🏡 {name}")

        # 床面積と天井高さ
        floor_area = st.number_input(
            f"[{name}] 延床面積 (m²)", min_value=0.0, value=90.0, step=0.1, key=f"floor_{idx}"
        )
        ceiling_h = st.number_input(
            f"[{name}] 天井高さ (m)", min_value=0.0, value=2.5, step=0.1, key=f"ceil_{idx}"
        )
        volume = floor_area * ceiling_h

        # 熱損失関連
        Ua        = st.number_input(
            f"[{name}] Ua値 (W/m²K)", 0.0, 10.0, (0.19 if idx == 0 else 0.87),
            step=0.01, key=f"Ua_{idx}"
        )
        vent_type = st.selectbox(
            f"[{name}] 換気方式", ["第一種", "第三種"], key=f"vent_{idx}"
        )
        rec_rate  = st.slider(
            f"[{name}] 熱交換率（第一種換気）", 0.0, 1.0, 0.75, key=f"rec_{idx}"
        )
        Cval      = st.number_input(
            f"[{name}] C値 (cm²/m²)", 0.0, 100.0, (0.5 if idx == 0 else 2.0),
            step=0.1, key=f"C_{idx}"
        )
        wind_spd  = st.number_input(
            f"[{name}] 平均風速 (m/s)", 0.0, 20.0, 2.0, step=0.1, key=f"wind_{idx}"
        )
        dense     = st.selectbox(
            f"[{name}] 住宅密集地", ["はい", "いいえ"], key=f"dense_{idx}"
        ) == "はい"
        dTw       = st.number_input(
            f"[{name}] 冬の温度差 (°C)", 0.0, 50.0, 20.0, step=0.5, key=f"dTw_{idx}"
        )
        dTs       = st.number_input(
            f"[{name}] 夏の温度差 (°C)", 0.0, 50.0, 5.0, step=0.5, key=f"dTs_{idx}"
        )
        days_h    = st.number_input(
            f"[{name}] 暖房日数", 0, 365, 120, step=1, key=f"dh_{idx}"
        )
        days_c    = st.number_input(
            f"[{name}] 冷房日数", 0, 365, 90, step=1, key=f"dc_{idx}"
        )

        # 太陽光・蓄電池（初期値を一条側13.47kW/7.04kWh、他の家0に設定）
        sol_cap = st.number_input(
            f"[{name}] 太陽光容量 (kW)",
            min_value=0.0, max_value=100.0,
            value=(13.47 if idx == 0 else 0.0),
            step=0.01, key=f"sol_{idx}"
        )
        bat_cap = st.number_input(
            f"[{name}] 蓄電池容量 (kWh)",
            min_value=0.0, max_value=1000.0,
            value=(7.04 if idx == 0 else 0.0),
            step=0.01, key=f"bat_{idx}"
        )
        bat_eff = st.slider(
            f"[{name}] 蓄電池効率 (%)", 0, 100, 90, key=f"beff_{idx}"
        ) / 100.0

        # 定数
        hrs       = 24.0
        vent_rate = 0.5
        rho       = 1.2
        c_air     = 0.33
        gen_h     = 3.5

        # 熱損失計算
        Qsw = Ua * floor_area * dTw * hrs * days_h / 1000
        Qss = Ua * floor_area * dTs * hrs * days_c / 1000
        hlr = (1 - rec_rate) if vent_type == "第一種" else 1.0
        Qvw = vent_rate * volume * rho * c_air * dTw * hlr * hrs * days_h / 1000
        Qvs = vent_rate * volume * rho * c_air * dTs * hlr * hrs * days_c / 1000
        lf  = 0.5 if dense else 1.0
        leakv = Cval * floor_area * wind_spd * lf / 100
        Qlw  = leakv * rho * c_air * dTw * hrs * days_h / 1000
        Qls  = leakv * rho * c_air * dTs * hrs * days_c / 1000
        Qtot = Qsw + Qss + Qvw + Qvs + Qlw + Qls

        # 昼夜消費
        Qday   = Qtot * (gen_h / 24)
        Qnight = Qtot - Qday

        # 発電→自家消費→蓄電→夜間放電（年間蓄電容量を365倍で計算）
        gen      = sol_cap * gen_h * 365
        use_s    = min(gen, Qday)
        surplus  = gen - use_s
        store    = min(surplus, bat_cap * bat_eff * 365)
        use_b    = min(store, Qnight)
        sell     = surplus - store
        buy_day  = max(Qday - use_s, 0.0)
        buy_night= max(Qnight - use_b, 0.0)

        # 費用計算
        cost_day   = buy_day   * day_rate
        cost_night = buy_night * night_rate
        revenue    = sell      * sell_rate
        net_cost   = cost_day + cost_night - revenue

        house_params[name] = {
            "年間消費[kWh]": Qtot,
            "年間発電量[kWh]": gen,
            "日中自家消費": use_s,
            "年間蓄電量": store,
            "夜間放電": use_b,
            "買電 (昼)": buy_day,
            "買電 (夜)": buy_night,
            "売電量": sell,
            "年間光熱費(円)": int(net_cost)
        }
        costs[name] = net_cost

# 結果表示
st.subheader("📊 年間電力収支比較")
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
