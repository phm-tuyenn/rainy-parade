import 'bootstrap/dist/css/bootstrap.min.css';
import GGMap from "./GGMap";
import { Row, Col } from 'react-bootstrap';
import { useState } from 'react';

function App() {
  const [content, setContent] = useState("")
  const [point, setPoint] = useState({})
  const [lol, setLol] = useState("")

  const handleData = (content, point) => {
    fetch("http://127.0.0.1:8000/api/forecast", {
      method: "POST",
      mode: "cors",
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "latitude": point.lat,
        "longitude": point.lng,
        "target_date": "2025-10-05"
      })
    })
    .then(res => res.json()) 
    .then(res => setLol(JSON.stringify(res)))
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
      {lol}
    </Col>
  </Row>);
}

export default App;
