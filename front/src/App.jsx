import React, { useEffect, useState } from "react";
import "./App.css";
import WebSocket from "isomorphic-ws";

const App = () => {
  const [imageSrc, setImageSrc] = useState(null);
  const [isSmoking, setIsSmoking] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(process.env.REACT_APP_WEB_SOCKET_URL);

    // Set the binaryType to 'blob'
    ws.binaryType = "arraybuffer"; //blob 대신 arraybuffer 형태로 가져오기

    ws.onopen = () => {
      ws.send('{"key":"1"}');
      console.log("connected from server");
    }; //더미데이터

    ws.onmessage = (e) => {
      var arraybuffer = e.data;
      var bytes = new Uint8Array(arraybuffer); //Uint8Array 형태로 데이터 가져오기
      var b64 = new TextDecoder().decode(bytes.slice(4)); //앞의 4 데이터는 piggyback된 smoking state

      //맨앞의 바이트값이  84면 smoking, 87이면 non smoking
      if (bytes[0] === 87) {
        setIsSmoking(false);
      } else {
        setIsSmoking(true);
      }
      setImageSrc(b64);
    };

    ws.onclose = () => {
      console.log("disconnected from server");
    };

    // Clean up the WebSocket connection when the component unmounts
    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="App">
      <span>Smoking Detect</span>
      <div
        className={"img-wrapper " + (isSmoking ? " border-t " : " border-f ")}
      >
        {isSmoking ? (
          <div className="text back-t">Smoking</div>
        ) : (
          <div className="text back-f">Non smoking</div>
        )}

        {imageSrc && (
          <img
            className={"img"}
            src={`data:image/png;base64,${imageSrc}`}
            alt="Received from server"
          />
        )}
      </div>
    </div>
  );
};

export default App;
