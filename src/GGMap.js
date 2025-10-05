import {APIProvider, Map, InfoWindow} from '@vis.gl/react-google-maps';
import { useEffect, useState } from 'react';

export default function GGMap({ onData }) {
  const [point, setPoint] = useState({lat: 0, lng: 0, updated: false})
  const [content, setContent] = useState("nothing bro wtf you find")

  const handleClick = (ev) => {
    let point = ev.detail.latLng
    fetch(`https://maps.googleapis.com/maps/api/geocode/json?latlng=${point.lat},${point.lng}&key=AIzaSyBXJQ9KUyxq3WAaU8InwzUbWi1GMCiShco`)
    .then(res => res.json())
    .then((res) => {
      if (res.results[3]) {
        setContent(res.results[3].formatted_address)
      } else setContent("nothing bro wtf you find")
    })
    setPoint({lat: point.lat, lng: point.lng, updated: true})
  };
  
  useEffect(() => {
    onData(content, point)
  }, [content])

  useEffect(() => {
    if (!point.updated && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setPoint({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            updated: true
          });
          onData(content, point)
        },
        (err) => {
          console.log(err.message);
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    } else {
      console.log("Geolocation is not supported by this browser.");
    }
  }, [])

  return (
    <APIProvider apiKey={"AIzaSyBXJQ9KUyxq3WAaU8InwzUbWi1GMCiShco"}>
      <Map
        style={{width: '100%', height: '100%'}}
        defaultCenter={{lat: point.lat, lng: point.lng}}
        defaultZoom={3}
        gestureHandling='greedy'
        onClick={handleClick}
      >
        {(content !== "nothing bro wtf you find") ?
        <InfoWindow position={{lat: point.lat, lng: point.lng}}>
          {content}
          <br/>
          {JSON.stringify(point)}
        </InfoWindow> : <></>
        }
      </Map>
  </APIProvider>
  );
}
