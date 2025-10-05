import 'bootstrap/dist/css/bootstrap.min.css';
import GGMap from "./GGMap";
import { Row, Col, Spinner } from 'react-bootstrap';
import { useState } from 'react';

const placeholderData = {
  "query_date": "",
  "climatological_probability_and_means": {
    "date_context": "",
    "climatological_means": {
      "avg_tmax_c": 0,
      "avg_tmin_c": 0,
      "avg_humidity_percent": 0,
      "avg_wind_speed_ms": 0,
      "avg_pressure_hpa": 0,
      "avg_uv_index": 0,
      "avg_discomfort_index_c": 0
    },
    "probabilities": {
      "p_rain_percent": 0,
      "p_extreme_heat_percent": 0,
      "p_extreme_wind_percent": 0,
      "main_risk_level": "THẤP"
    }
  },
  "short_term_forecast_details": null,
  "air_quality_context": {
    "pm25_concentration": 0,
    "pm10_concentration": 0
  },
  "data_summary": ""
}

const getDay = (day) => {
  const yyyy = day.getFullYear();
  let mm = day.getMonth() + 1; // Months start at 0!
  let dd = day.getDate();

  if (dd < 10) dd = '0' + dd;
  if (mm < 10) mm = '0' + mm;

  const formattedToday = yyyy + "-" + mm + "-" + dd;
  return formattedToday
}

function Data({key, label, data}) {
  return (<>
    <label for={key}>{label}</label>
    <i id={key}> {data}</i>
    <br/>
  </>)
}

export default function App() {
  const [content, setContent] = useState("")
  const [point, setPoint] = useState({})
  const [data, setData] = useState(placeholderData)
  const [targetDate, setTargetDate] = useState(getDay(new Date()))
  const [wait, setWait] = useState(false)

  const updateData = (date) => {
    setWait(true)
    setData(placeholderData)
    fetch("https://rainy-parade-api-only.vercel.app/api/forecast", {
      method: "POST",
      mode: "cors",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "latitude": point.lat,
        "longitude": point.lng,
        "target_date": date
      })
    })
    .then(res => {
      if (res.status === 200) return res.json()
      else return {error: true}
    }).then(res => { 
      if (!res.error) setData(res)
      else setData(placeholderData)
      setWait(false)
    })
  }

  const handleData = (content, point) => {
    updateData(targetDate)
    setContent(content)
    setPoint(point)
  }

  return (<Row style={{width: "100vw", height: "100vh"}}>
    <Col md={{span: 8}}><GGMap onData={handleData}/></Col>
    <Col md={{span: 4}} className='pt-4'>
      <h4 className='pb-1'>{(content !== "nothing bro wtf you find" ? content : "Đang tìm kiếm ...")}</h4>
      <h6><b>Kinh độ: {Math.round(point.lng)}° | Vĩ độ: {Math.round(point.lat)}°</b></h6>
      <label for="date">Ngày cần dự đoán: </label>
      <input
        type="date"
        id="date"
        value={targetDate}
        min={getDay(new Date())}
        max={getDay(new Date(new Date().setDate(new Date().getDate() + 180)))}
        onChange={(e) => {
          setTargetDate(e.target.value)
          updateData(e.target.value)
        }}/>
        <br/>
      <i style={{fontSize: "small"}}>Hãy chọn nơi muốn dự đoán trên bản đồ và ngày cần dự đoán. <br/> Nếu không thể tìm thấy vị trí hiện tại của bạn, hãy nhấn nút màu xanh ở góc trái dưới màn hình.</i>
      <hr/>
      {(wait) ? <Spinner animation="border" role="status">
          <span className="visually-hidden"><p>Đang tải ...</p></span>
        </Spinner> : <>
        <h4><b>Dự đoán thời tiết ngày {targetDate}</b></h4>
        <Data key="tmaxc" label={"Nhiệt độ cao nhất: "} data={data.climatological_probability_and_means.climatological_means.avg_tmax_c}/>
        <Data key="tminc" label={"Nhiệt độ thấp nhất: "} data={data.climatological_probability_and_means.climatological_means.avg_tmin_c}/>
        <Data key="humid" label={"Độ ẩm: "} data={data.climatological_probability_and_means.climatological_means.avg_humidity_percent}/>
        <Data key="wind" label={"Tốc độ gió: "} data={data.climatological_probability_and_means.climatological_means.avg_wind_speed_ms}/>
        <Data key="pressure" label={"Áp suất không khí: "} data={data.climatological_probability_and_means.climatological_means.avg_pressure_hpa}/>
        <Data key="uv" label={"Chỉ số tia UV: "} data={data.climatological_probability_and_means.climatological_means.avg_uv_index}/>
        <hr/>
        <Data key="rainp" label={"Khả năng mưa: "} data={data.climatological_probability_and_means.probabilities.p_rain_percent}/>
        <Data key="hotp" label={"Khả năng nắng nóng gay gắt: "} data={data.climatological_probability_and_means.probabilities.p_extreme_heat_percent}/>
        <Data key="wind" label={"Khả năng có gió lớn: "} data={data.climatological_probability_and_means.probabilities.p_extreme_wind_percent}/>
        <Data key="risk" label={"Mức độ rủi ro: "} data={data.climatological_probability_and_means.probabilities.main_risk_level}/>
        <hr/>
        <Data key="pm25" label={"Chỉ số bụi mịn PM25: "} data={data.air_quality_context.pm25_concentration}/>
        <Data key="pm10" label={"Chỉ số bụi mịn PM10: "} data={data.air_quality_context.pm10_concentration}/>
      </>}
    </Col>
  </Row>);
}
