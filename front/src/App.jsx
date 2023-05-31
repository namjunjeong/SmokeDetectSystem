import { useEffect, useState } from 'react';

function App() {
  let [img, changeImg] = useState(null); //이미지 바뀔때마다 렌더링
  let [smoking, changeSmoking] = useState(false); //smoking state 바뀔떄마다 렌더링

  useEffect(()=>{
    const ws = new WebSocket("ws://localhost:3001");
    ws.binaryType = "arraybuffer"; //blob 대신 arraybuffer 형태로 가져오기

    ws.onopen = () => ws.send('{"key":"1"}'); //더미데이터

    ws.onmessage =(e)=>{
      var arraybuffer = e.data; 
      var bytes = new Uint8Array(arraybuffer); //Uint8Array 형태로 데이터 가져오기
      var b64 = new TextDecoder().decode(bytes.slice(4)) //앞의 4 데이터는 piggyback된 smoking state

       //맨앞의 바이트값이  84면 smoking, 87이면 non smoking
      if (bytes[0] === 87) {changeSmoking(false)} else {changeSmoking(true)};
      changeImg(b64)
    }
  },[])

  return (
    <div className="App">
      <header className="App-header">
        <div>
          <div>smoking? : {smoking  ? 'smoking' : 'not smoking' }</div>
          <div><img src={`data:image/png;base64,${img}`}/></div>
        </div>
      </header>
    </div>
  );
}

export default App;
