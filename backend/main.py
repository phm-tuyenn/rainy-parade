from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from datetime import date, timedelta

# Import các hàm từ các module backend đã tạo
from .data_fetcher import (
    fetch_historical_climatology,
    fetch_air_quality,
    fetch_short_term_forecast,
)
from .climatological_predictor import (
    transform_power_data_to_dataframe, #NASA POWER IS REQUIRED
    calculate_climatological_metrics,
    calculate_discomfort_index
)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://rainy-parade-j1dd.vercel.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    target_date: date


# --- ENDPOINT TỔNG HỢP DUY NHẤT ---

@app.post("/api/forecast", response_model=Dict[str, Any])
def get_full_forecast_for_day(request: PredictionRequest):
    """
    Endpoint tổng hợp: Xác suất Khí hậu (Dài hạn) + Dự báo Chi tiết (Ngắn hạn) + AQI.
    Sử dụng NASA POWER cho lịch sử và Open-Meteo cho dự báo/AQI.
    """

    # 1. TÍNH XÁC SUẤT KHÍ HẬU DÀI HẠN (NASA POWER)
    raw_climatology_data = fetch_historical_climatology(
        request.latitude,
        request.longitude
    )

    if not raw_climatology_data:
        raise HTTPException(status_code=500,
                            detail="Lỗi khi truy cập dữ liệu lịch sử NASA POWER. Không thể tính Xác suất Khí hậu.")

    # Tiền xử lý dữ liệu và tính toán Xác suất/Trung bình Lịch sử
    historical_df = transform_power_data_to_dataframe(raw_climatology_data)
    climatological_metrics = calculate_climatological_metrics(historical_df, request.target_date)

    if climatological_metrics.get("error"):
        raise HTTPException(status_code=500, detail=climatological_metrics["error"])

    # 2. DỰ BÁO CHI TIẾT NGẮN HẠN (OPEN-METEO)
    today = date.today()
    delta = request.target_date - today
    is_short_term_forecast = delta.days >= 0 and delta.days <= 16  # Open-Meteo cho 16 ngày

    short_term_data = None

    if is_short_term_forecast:
        # Lấy dự báo 16 ngày chi tiết
        forecast_raw = fetch_short_term_forecast(request.latitude, request.longitude)

        # Open-Meteo trả về các mảng cùng độ dài, ta tìm index của ngày mục tiêu
        time_list = forecast_raw.get('time', [])

        try:
            target_date_str = str(request.target_date)  # YYYY-MM-DD
            target_index = time_list.index(target_date_str)

            # Trích xuất dữ liệu tại index đó
            t_max = forecast_raw['temperature_2m_max'][target_index]
            humidity = forecast_raw['relative_humidity_2m'][target_index]
            wind_speed = forecast_raw['wind_speed_10m_max'][target_index]
            rain_prob = forecast_raw['precipitation_probability'][target_index]
            uv_index = forecast_raw['uv_index_max'][target_index]
            pressure = forecast_raw['surface_pressure'][target_index]

            # Tính chỉ số thông minh
            short_term_data = {
                "source": "Open-Meteo Forecast API (7-16 ngày)",
                "t_max_c": t_max,
                "humidity_percent": humidity,
                "wind_speed_ms": wind_speed,
                "pressure_hpa": pressure,
                "uv_index": uv_index,
                "rain_prob_percent": rain_prob,
                "discomfort_index_c": calculate_discomfort_index(t_max, humidity, wind_speed),
            }
        except ValueError:
            # Ngày mục tiêu không nằm trong phạm vi 16 ngày (hoặc API lỗi)
            pass
        except KeyError:
            # Lỗi cấu trúc dữ liệu trả về từ API
            pass

    # 3. LẤY CHẤT LƯỢNG KHÔNG KHÍ HIỆN TẠI (OPEN-METEO AQI)
    # Open-Meteo AQI không cần API Key
    aqi_info = fetch_air_quality(request.latitude, request.longitude)

    # 4. TỔNG HỢP KẾT QUẢ CUỐI CÙNG
    return {
        "query_date": str(request.target_date),
        "climatological_probability_and_means": climatological_metrics,
        "short_term_forecast_details": short_term_data,
        "air_quality_context": aqi_info,
        "data_summary": "Dữ liệu Xác suất được tính từ NASA POWER (1985-2015). Dự báo chi tiết và AQI được cung cấp bởi Open-Meteo."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    #fuck it