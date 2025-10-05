import requests
from typing import Dict, Any, List
import pandas as pd
from datetime import date

# --- 1. CONFIG API URLs & VARIABLES ---

# NASA POWER API cho Dữ liệu Lịch sử (Yêu cầu BẮT BUỘC)
POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
# Các biến số cần thiết: Nhiệt độ, Mưa, Gió, Áp suất, Độ ẩm, UV
POWER_VARIABLES = "T2M_MAX,T2M_MIN,PRECTOT,WS10M,PS,RH2M,ALLSKY_SFC_UV_INDEX"

# OPEN-METEO cho Dự báo Ngắn hạn (MIỄN PHÍ, KHÔNG CẦN KEY)
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_VARIABLES = "temperature_2m_max,relative_humidity_2m,wind_speed_10m_max,precipitation_probability,uv_index_max,surface_pressure"

# OPEN-METEO cho Chất lượng Không khí (AQI) (MIỄN PHÍ, KHÔNG CẦN KEY)
AQI_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
AQI_VARIABLES = "pm10,pm2_5"  # Lấy PM2.5 và PM10


# --- 2. HÀM FETCH DỮ LIỆU LỊCH SỬ (NASA POWER) ---

def fetch_historical_climatology(lat: float, lon: float, start_year: str = "1994", end_year: str = "2024") -> Dict[
    str, Any]:
    """
    Lấy dữ liệu khí hậu lịch sử hàng ngày (30 năm) với đầy đủ biến số từ NASA POWER.
    """
    print(f">>> Đang lấy dữ liệu lịch sử NASA POWER DAILY cho ({lat}, {lon})...")

    parameters = {
        "parameters": POWER_VARIABLES,
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
        "start": start_year,
        "end": end_year
    }

    try:
        response = requests.get(POWER_DAILY_URL, params=parameters, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('properties', {}).get('parameter', {})

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi NASA POWER API (Historical Daily): {e}")
        return {}


# --- 3. HÀM FETCH DỰ BÁO NGẮN HẠN (OPEN-METEO) ---

def fetch_short_term_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    Lấy dự báo thời tiết 7-16 ngày (daily) từ Open-Meteo Forecast API.
    """
    print(f">>> Đang lấy dự báo ngắn hạn (Open-Meteo) cho ({lat}, {lon})...")

    parameters = {
        "latitude": lat,
        "longitude": lon,
        "daily": FORECAST_VARIABLES,
        "forecast_days": 16,  # Lấy tối đa 16 ngày
        "timezone": "auto"
    }

    try:
        response = requests.get(FORECAST_API_URL, params=parameters, timeout=10)
        response.raise_for_status()
        return response.json().get('daily', {})

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi Open-Meteo Forecast API: {e}")
        return {}


# --- 4. HÀM FETCH CHẤT LƯỢNG KHÔNG KHÍ (OPEN-METEO) ---

def fetch_air_quality(lat: float, lon: float) -> Dict[str, Any]:
    """
    Lấy dữ liệu Chất lượng Không khí (AQI) hiện tại/gần nhất từ Open-Meteo AQI API.
    """
    print(f">>> Đang lấy dữ liệu Chất lượng Không khí (Open-Meteo) cho ({lat}, {lon})...")

    parameters = {
        "latitude": lat,
        "longitude": lon,
        "hourly": AQI_VARIABLES,
        "forecast_days": 1,  # Chỉ lấy dữ liệu hiện tại/gần nhất
        "timezone": "auto"
    }

    try:
        response = requests.get(AQI_API_URL, params=parameters, timeout=10)
        response.raise_for_status()

        # Chỉ lấy dữ liệu hourly gần nhất
        hourly_data = response.json().get('hourly', {})
        if hourly_data and hourly_data.get('pm2_5') and hourly_data.get('pm2_5')[0] is not None:
            # Trả về giá trị đầu tiên (hiện tại/gần nhất)
            return {
                "pm25_concentration": hourly_data['pm2_5'][0],
                "pm10_concentration": hourly_data['pm10'][0]
            }
        return {}

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi Open-Meteo AQI API: {e}")
        return {}