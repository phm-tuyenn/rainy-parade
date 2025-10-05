from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from datetime import date, datetime, timedelta

# Import các hàm từ các file khác
from .data_fetcher import fetch_historical_climatology, fetch_short_term_forecast, fetch_air_quality
from .climatological_predictor import transform_power_data_to_dataframe, calculate_climatological_metrics, \
    calculate_discomfort_index

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Climatological Weather Predictor API",
    description="API dự báo khí hậu và thời tiết dựa trên dữ liệu lịch sử NASA POWER và dự báo ngắn hạn Open-Meteo."
)


# Định nghĩa cấu trúc dữ liệu đầu vào (Payload)
class PredictionRequest(BaseModel):
    latitude: float
    longitude: float
    target_date: date


@app.get("/")
def read_root():
    """Endpoint kiểm tra trạng thái API."""
    return {"status": "Service is running", "version": "1.0.1"}


# ==============================================================================
# ENDPOINT CHÍNH
# ==============================================================================

@app.post("/api/forecast", response_model=Dict[str, Any])
def get_full_forecast_for_day(request: PredictionRequest):
    """
    Endpoint chính: Tính toán Xác suất Khí hậu, Dự báo Ngắn hạn và Chất lượng Không khí
    cho một ngày và địa điểm cụ thể.
    """

    # 1. DỮ LIỆU KHÍ HẬU LỊCH SỬ (NASA POWER)
    # Lấy dữ liệu thô (đã được cấu hình để lấy từ 1994 đến năm hiện tại)
    raw_climatology_data = fetch_historical_climatology(request.latitude, request.longitude)

    # Chuyển dữ liệu thô sang DataFrame và làm sạch (-999.0 thành NaN)
    historical_df = transform_power_data_to_dataframe(raw_climatology_data)

    # Tính toán các chỉ số xác suất và trung bình khí hậu
    climatological_results = calculate_climatological_metrics(historical_df, request.target_date)

    # 2. DỰ BÁO CHI TIẾT NGẮN HẠN (OPEN-METEO)

    # Xác định xem ngày mục tiêu có nằm trong phạm vi dự báo 14 ngày không
    today = date.today()
    delta = request.target_date - today
    is_short_term_forecast = delta.days >= 0 and delta.days < 16

    short_term_data = None

    if is_short_term_forecast:
        # Lấy dữ liệu dự báo ngắn hạn (sử dụng openmeteo_requests client)
        # Hàm này trả về một dictionary của các giá trị của ngày đầu tiên.
        forecast_raw = fetch_short_term_forecast(request.latitude, request.longitude)

        if forecast_raw:
            try:
                # SỬ DỤNG TÊN BIẾN _MAX ĐÃ ĐƯỢC SỬA LỖI
                t_max = forecast_raw['temperature_2m_max']
                humidity = forecast_raw['relative_humidity_2m_max']
                wind_speed = forecast_raw['wind_speed_10m_max']
                precipitation_mm = forecast_raw['precipitation_sum']
                uv_index = forecast_raw['uv_index_max']
                pressure = forecast_raw['surface_pressure_max']

                # Tính chỉ số khó chịu cho ngày dự báo
                discomfort_index = calculate_discomfort_index(t_max, humidity, wind_speed)

                short_term_data = {
                    "source": "Open-Meteo Daily Forecast",
                    "t_max_c": t_max,
                    "humidity_percent": humidity,
                    "wind_speed_ms": wind_speed,
                    "pressure_hpa": pressure,
                    "uv_index": uv_index,
                    "rain_prob_percent": precipitation_mm,
                    "discomfort_index_c": discomfort_index,
                }
            except KeyError as e:
                # Xử lý nếu tên khóa vẫn không khớp (rất hiếm khi xảy ra với client chính thức)
                print(f"Lỗi Key Error khi parsing dữ liệu Open-Meteo: Thiếu key {e}")
                pass
            except IndexError:
                # Xử lý nếu dữ liệu không có giá trị
                pass

    # 3. CHẤT LƯỢNG KHÔNG KHÍ (OPEN-METEO AQI)
    # Lấy dữ liệu AQI (chỉ lấy cho ngày hiện tại)
    air_quality_data = {}
    if request.target_date == today:
        air_quality_data = fetch_air_quality(request.latitude, request.longitude)

    # 4. TỔNG HỢP VÀ TRẢ VỀ KẾT QUẢ

    # Kết quả dự báo ngắn hạn (nếu có) sẽ ưu tiên hơn trung bình khí hậu
    final_weather = short_term_data if short_term_data else climatological_results.get("climatological_means", {})

    return {
        "location": {"latitude": request.latitude, "longitude": request.longitude},
        "target_date": request.target_date.isoformat(),

        "current_prediction": final_weather,
        "climatological_probabilities": climatological_results.get("probabilities", {}),
        "air_quality_index": air_quality_data,
    }