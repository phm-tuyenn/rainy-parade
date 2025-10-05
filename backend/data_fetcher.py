import requests
from typing import Dict, Any, List
import pandas as pd
from datetime import date
from urllib.parse import urlencode
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd # Cần cho việc xử lý dữ liệu Open-Meteo

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo_client = openmeteo_requests.Client(session = retry_session)
# --- 1. CONFIG API URLs & VARIABLES ---

# NASA POWER API cho Dữ liệu Lịch sử (Yêu cầu BẮT BUỘC)
POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
# Các biến số cần thiết: Nhiệt độ, Mưa, Gió, Áp suất, Độ ẩm, UV
POWER_VARIABLES = "T2M_MAX,T2M_MIN,PRECTOT,WS10M,PS,RH2M,ALLSKY_SFC_UV_INDEX"

# OPEN-METEO cho Dự báo Ngắn hạn
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
# Thay đổi FORECAST_VARIABLES thành LIST (Danh sách) thay vì chuỗi
FORECAST_VARIABLES = [
    "temperature_2m_max",
    "relative_humidity_2m_max",
    "wind_speed_10m_max",
    "precipitation_sum",
    "uv_index_max",
    "surface_pressure_max"
]
# OPEN-METEO cho Chất lượng Không khí (AQI)
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
    Lấy dự báo thời tiết 7-16 ngày (daily) từ Open-Meteo bằng openmeteo_requests.
    """
    print(f">>> Đang lấy dự báo ngắn hạn (Open-Meteo Client) cho ({lat}, {lon})...")

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": FORECAST_VARIABLES,  # Truyền LIST biến số trực tiếp
        "forecast_days": 16,
        "timezone": "auto"
    }

    try:
        # Gọi API bằng client chính thức
        responses = openmeteo_client.weather_api(FORECAST_API_URL, params=params)

        # Xử lý phản hồi (chỉ lấy phản hồi đầu tiên)
        response = responses[0]

        # Chuyển dữ liệu daily sang DataFrame để dễ dàng truy cập và kiểm tra
        daily = response.Daily()

        # Lấy tất cả các cột dữ liệu theo thứ tự đã yêu cầu
        daily_data = {}
        for i, var_name in enumerate(FORECAST_VARIABLES):
            daily_data[var_name] = daily.Variables(i).ValuesAsNumpy()

        # Dữ liệu dự báo của ngày đầu tiên (index 0)
        # Chúng ta chỉ cần trả về một dictionary của ngày đầu tiên (index 0)
        first_day_forecast = {}
        for key, values in daily_data.items():
            if len(values) > 0:
                first_day_forecast[key] = values[0].item()  # .item() để chuyển numpy float sang python float

        return first_day_forecast

    except Exception as e:
        print(f"Lỗi khi gọi Open-Meteo Forecast API Client: {e}")
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