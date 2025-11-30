import { useState, useEffect } from 'react';

function App() {
  const [health, setHealth] = useState<string>('checking...');

  useEffect(() => {
    // Check backend health
    fetch('http://127.0.0.1:4100/health')
      .then(res => res.json())
      .then(data => setHealth(data.status))
      .catch(() => setHealth('error'));
  }, []);

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Atlas - Local-First Personal OS</h1>
      <p>Backend status: <strong>{health}</strong></p>
      <div style={{ marginTop: '2rem' }}>
        <h2>Getting Started</h2>
        <ul>
          <li>Backend is running on http://127.0.0.1:4100</li>
          <li>API docs available at http://127.0.0.1:4100/docs</li>
          <li>Start building your UI components in src/components</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
