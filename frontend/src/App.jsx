import React from 'react';
import Login from './Login';

function App(){
  return (
    <div style={{padding:20}} dir="rtl">
      <h1>Irbid Accounting — Scaffold</h1>
      <p>FastAPI backend + React frontend — i18n & RTL enabled (setup)</p>
      <Login />
    </div>
  );
}

export default App;
