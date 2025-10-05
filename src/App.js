import 'bootstrap/dist/css/bootstrap.min.css';
import GGMap from "./GGMap";
import { Row, Col } from 'react-bootstrap';
import { useEffect, useState } from 'react';

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
    <Col md={{span: 4}} className='py-3'>
      <h4>{(content !== "nothing bro wtf you find" ? content : "Đang tìm kiếm ...")}</h4>
      <h6><b>Kinh độ: {point.lng}° | Vĩ độ: {point.lat}°</b></h6>
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
      {(wait) ? <p>Đang tải ...</p> : <hr/>}
      <Data key="tmaxc" label={"Nhiệt độ cao nhất: "} data={data.climatological_probability_and_means.climatological_means.avg_tmax_c}/>
      <Data key="tminc" label={"Nhiệt độ thấp nhất: "} data={data.climatological_probability_and_means.climatological_means.avg_tmin_c}/>
      <Data key="humid" label={"Độ ẩm: "} data={data.climatological_probability_and_means.climatological_means.avg_humidity_percent}/>
      <Data key="wind" label={"Tốc độ gió: "} data={data.climatological_probability_and_means.climatological_means.avg_wind_speed_ms}/>
      <Data key="pressure" label={"Áp suất không khí: "} data={data.climatological_probability_and_means.climatological_means.avg_pressure_hpa}/>
      <Data key="uv" label={"Chỉ số tia UV: "} data={data.climatological_probability_and_means.climatological_means.avg_uv_index}/>
      
    </Col>
  </Row>);
}
