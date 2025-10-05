import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, date


# --- 1. Tiền xử lý Dữ liệu POWER ---

def transform_power_data_to_dataframe(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Chuyển đổi Dict thô từ NASA POWER DAILY thành Pandas DataFrame với DateTime Index.
    Phiên bản này có kiểm tra an toàn để tránh KeyError khi thiếu biến số.
    """

    series_list = []

    # Danh sách đầy đủ các cột mà chúng ta cần
    REQUIRED_COLUMNS = ['T2M_MAX', 'T2M_MIN', 'PRECTOT', 'WS10M', 'PS', 'RH2M', 'ALLSKY_SFC_UV_INDEX']

    # 1. Tạo Series chỉ cho dữ liệu tồn tại trong phản hồi của NASA POWER
    for var_name in REQUIRED_COLUMNS:
        if var_name in raw_data:
            data_dict = raw_data[var_name]
            s = pd.Series(data_dict, name=var_name, dtype=float)
            series_list.append(s)
        # Nếu biến số không có, ta sẽ bổ sung nó sau (Bước 3)

    if not series_list:
        return pd.DataFrame()

    df = pd.concat(series_list, axis=1)

    # 2. Chuyển đổi Index (YYYYMMDD) thành DateTime
    df.index = pd.to_datetime(df.index, format='%Y%m%d', errors='coerce')
    df = df[df.index.notna()]

    # 3. THÊM CÁC CỘT BỊ THIẾU VÀO DATAFRAME VỚI GIÁ TRỊ NaN (FIX KEYERROR)
    missing_cols = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
            missing_cols.append(col)

    if missing_cols:
        print(f"Cảnh báo: Các biến số sau bị thiếu trong phản hồi của NASA POWER: {missing_cols}. Đã thay bằng NaN.")

    # 4. Xử lý giá trị bị thiếu của NASA POWER (-999) bằng NaN
    df = df.replace(-999.0, np.nan)

    return df.sort_index()


# --- 2. Công thức Chỉ số Thông minh ---

def calculate_discomfort_index(temp_c: float, rh_percent: float, wind_speed: float) -> float:
    """
    Tính Chỉ số Khó chịu (Discomfort Index) dựa trên T, RH, và Gió (tương tự Heat Index).
    """
    # ... (Công thức đã đề xuất trước đó, ví dụ: Heat Index điều chỉnh)
    T_F = (temp_c * 9 / 5) + 32
    R = rh_percent
    # Công thức NOAA regression (đã giản lược)
    HI_F = (-42.379 + 2.049 * T_F + 10.143 * R - 0.224 * T_F * R + 0.001 * T_F * R ** 2)
    HI_C = (HI_F - 32) * 5 / 9

    wind_factor = max(0, wind_speed - 3) * 0.5
    di = max(temp_c, HI_C - wind_factor)  # DI không thấp hơn T

    return round(di, 1)


# --- 3. Logic Tính Xác suất (Core Logic Mới) ---

def calculate_climatological_metrics(historical_df: pd.DataFrame, target_date: date) -> Dict[str, Any]:
    """
    Tính toán các Trung bình và Xác suất Lịch sử cho ngày/tháng mục tiêu.
    """
    if historical_df.empty:
        return {"error": "Không có dữ liệu lịch sử để tính xác suất."}

    # Lọc Dữ liệu Lịch sử theo Ngày và Tháng (tất cả các năm)
    target_day_month = (target_date.month, target_date.day)

    filtered_history = historical_df[
        (historical_df.index.month == target_day_month[0]) &
        (historical_df.index.day == target_day_month[1])
        ]

    total_days = len(filtered_history)
    if total_days == 0:
        return {"error": "Không có dữ liệu lịch sử cho ngày cụ thể này."}

    # --- A. TÍNH TRUNG BÌNH KHÍ TƯỢNG (CLIMATOLOGICAL MEANS) ---

    # 1. Tính Tmax, Tmin, Gió, Áp suất, Độ ẩm, UV trung bình
    avg_tmax = filtered_history['T2M_MAX'].mean()
    avg_rh = filtered_history['RH2M'].mean()
    avg_ws = filtered_history['WS10M'].mean()
    avg_ps = filtered_history['PS'].mean()
    avg_uv = filtered_history['ALLSKY_SFC_UV_INDEX'].mean()

    # 2. Tính Discomfort Index trung bình
    # Tính DI cho từng ngày lịch sử và lấy trung bình
    discomfort_series = filtered_history.apply(
        lambda row: calculate_discomfort_index(row['T2M_MAX'], row['RH2M'], row['WS10M']),
        axis=1
    )
    avg_di = discomfort_series.mean()

    # --- B. TÍNH XÁC SUẤT (PROBABILITIES) ---

    # 3. P(Mưa): Đếm số ngày mưa (> 0.1 mm)
    rain_days = filtered_history[filtered_history['PRECTOT'] > 0.1].shape[0]
    p_rain = round((rain_days / total_days) * 100, 1)

    # 4. P(Cực đoan/Thiên tai - Ví dụ: Cực nóng)
    # Ngưỡng: 90th Percentile của Tmax trong tất cả 30 năm (để xác định "Cực đoan")
    extreme_tmax_threshold = historical_df['T2M_MAX'].quantile(0.90)
    extreme_heat_days = filtered_history[filtered_history['T2M_MAX'] > extreme_tmax_threshold].shape[0]
    p_extreme_heat = round((extreme_heat_days / total_days) * 100, 1)

    # LƯU Ý: P(Sấm sét, Cháy rừng) đòi hỏi dữ liệu khác (như Flash Density, Fire Index)
    # Ta sử dụng P(Gió mạnh) làm đại diện cho rủi ro bão/giông:
    extreme_wind_threshold = historical_df['WS10M'].quantile(0.90)
    extreme_wind_days = filtered_history[filtered_history['WS10M'] > extreme_wind_threshold].shape[0]
    p_extreme_wind = round((extreme_wind_days / total_days) * 100, 1)

    # --- C. TRẢ VỀ KẾT QUẢ ---
    return {
        "date_context": f"Dữ liệu dựa trên 30 năm lịch sử (1985-2015) của ngày {target_date.day}/{target_date.month}.",
        "climatological_means": {
            "avg_tmax_c": round(avg_tmax, 1),
            "avg_tmin_c": round(filtered_history['T2M_MIN'].mean(), 1),
            "avg_humidity_percent": round(avg_rh, 1),
            "avg_wind_speed_ms": round(avg_ws, 1),
            "avg_pressure_hpa": round(avg_ps, 1),
            "avg_uv_index": round(avg_uv, 1),
            "avg_discomfort_index_c": round(avg_di, 1),
        },
        "probabilities": {
            "p_rain_percent": p_rain,
            "p_extreme_heat_percent": p_extreme_heat,
            "p_extreme_wind_percent": p_extreme_wind,
            "main_risk_level": "CAO" if p_extreme_heat >= 15 or p_extreme_wind >= 15 else (
                "VỪA" if p_rain >= 40 else "THẤP")
        }
    }