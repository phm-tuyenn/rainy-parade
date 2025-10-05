import 'bootstrap/dist/css/bootstrap.min.css';
import GGMap from "./GGMap";
import { Row, Col } from 'react-bootstrap';
import { useState } from 'react';

function App() {
  const [content, setContent] = useState("")
  const [point, setPoint] = useState({})
  const handleData = (content, point) => {
    setContent(content)
    setPoint(point)
  }

  return (<Row style={{width: "100vw", height: "100vh"}}>
    <Col md={{span: 8}}><GGMap onData={handleData}/></Col>
    <Col md={{span: 4}}>
      {content}
      <br/>
      {JSON.stringify(point)}
    </Col>
  </Row>);
}

export default App;
