import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main className="shell">
      <p className="eyebrow">Stage 1 Started</p>
      <h1>Crypto Wallet Intelligence</h1>
      <p>
        Whale wallet database and movement tracking foundations are underway. V1
        is research and paper-trading only; live trading is disabled.
      </p>
      <ul>
        <li>Wallet-led intelligence by default</li>
        <li>Local PostgreSQL with Stage 1 wallet tracking tables</li>
        <li>Wallet management API foundation</li>
        <li>Ollama qwen3:4b for low-risk local tasks</li>
      </ul>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
