import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main className="shell">
      <p className="eyebrow">Stage 0 Foundation</p>
      <h1>Crypto Wallet Intelligence</h1>
      <p>
        FastAPI + React skeleton is ready. V1 is research and paper-trading only;
        live trading is disabled.
      </p>
      <ul>
        <li>Wallet-led intelligence by default</li>
        <li>PostgreSQL foundation</li>
        <li>Ollama qwen3:4b for low-risk local tasks</li>
        <li>ChatGPT primary with Anthropic fallback for development reasoning</li>
      </ul>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
