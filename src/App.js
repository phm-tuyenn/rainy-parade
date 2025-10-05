import 'bootstrap/dist/css/bootstrap.min.css';
import GGMap from "./GGMap";
import { Row, Col } from 'react-bootstrap';
import { useEffect, useState } from 'react';

const getDay = (day) => {
  const yyyy = day.getFullYear();
  let mm = day.getMonth() + 1; // Months start at 0!
  let dd = day.getDate();

  if (dd < 10) dd = '0' + dd;
  if (mm < 10) mm = '0' + mm;

  const formattedToday = yyyy + "-" + mm + "-" + dd;
  return formattedToday
}

export default function App() {
  const [content, setContent] = useState("")
  const [point, setPoint] = useState({})
  const [lol, setLol] = useState("")
  const [targetDate, setTargetDate] = useState(getDay(new Date()))
  const [wait, setWait] = useState(false)

  const updateData = (date) => {
    setWait(true)
    fetch("http://127.0.0.1:8000/api/forecast", {
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
    .then(res => res.json()) 
    .then(res => { 
      setLol(JSON.stringify(res))
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
    <Col md={{span: 4}}>
      {content}
      <br/>
      {JSON.stringify(point)}
      <br/>
      {(wait) ? <p>Đang tải</p> : <></>}
      <label for="date">Date:</label>
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
      {lol}
    </Col>
  </Row>);
}
