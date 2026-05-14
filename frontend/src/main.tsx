import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

type WhaleWallet = {
  id: string;
  wallet_address: string;
  normalized_address: string;
  chain: string;
  label: string | null;
  wallet_type: string;
  notes: string | null;
  enabled: boolean;
  alert_threshold_usd: string;
  watch_priority: number;
  confidence_weighting: string;
  copy_trade_enabled: boolean;
  do_not_copy: boolean;
  last_seen_at: string | null;
  tags: string[];
  sectors_of_interest: string[];
  created_at: string;
  updated_at: string;
};

type WalletMovement = {
  id: string;
  wallet_id: string;
  chain: string;
  transaction_hash: string;
  movement_type: string;
  token_symbol: string;
  token_contract: string | null;
  token_amount: string | null;
  estimated_usd_value: string | null;
  from_address: string | null;
  to_address: string | null;
  protocol: string | null;
  block_number: number | null;
  transaction_time: string;
  price_at_trade_time: string | null;
  gas_fee: string | null;
  alert_threshold_crossed: boolean;
  processed_by_agent: boolean;
  data_quality_score: number;
  manual_review_required: boolean;
  raw_api_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type WalletSummary = {
  total_wallets: number;
  enabled_wallets: number;
  do_not_copy_wallets: number;
  movement_count: number;
  manual_review_movements: number;
};

const API_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL ?? 'http://127.0.0.1:8000';

const walletTypes = [
  'Unknown',
  'Whale',
  'Smart Money',
  'VC/Fund',
  'Exchange',
  'Market Maker',
  'Influencer Wallet',
  'Developer Wallet',
  'Suspicious',
  'Do Not Copy',
];

const movementTypes = [
  'DEX buy',
  'DEX sell',
  'CEX deposit',
  'CEX withdrawal',
  'Wallet-to-wallet transfer',
  'Bridge movement',
  'Stablecoin accumulation',
  'Stablecoin deployment',
  'New token position',
  'Position increase',
  'Position reduction',
  'Full exit',
];

const emptySummary: WalletSummary = {
  total_wallets: 0,
  enabled_wallets: 0,
  do_not_copy_wallets: 0,
  movement_count: 0,
  manual_review_movements: 0,
};

function splitList(value: string): string[] {
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

function formatUsd(value: string | number | null): string {
  if (value === null || value === '') return 'n/a';
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(number);
}

function dateForInput(): string {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

function App() {
  const [wallets, setWallets] = useState<WhaleWallet[]>([]);
  const [movements, setMovements] = useState<WalletMovement[]>([]);
  const [summary, setSummary] = useState<WalletSummary>(emptySummary);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [movementSaving, setMovementSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [chainFilter, setChainFilter] = useState('');
  const [movementFilter, setMovementFilter] = useState<'all' | 'review' | 'alerts'>('all');
  const [form, setForm] = useState({
    wallet_address: '',
    chain: 'ethereum',
    label: '',
    wallet_type: 'Unknown',
    alert_threshold_usd: '100000',
    watch_priority: '3',
    confidence_weighting: '1.00',
    copy_trade_enabled: false,
    do_not_copy: false,
    tags: '',
    sectors_of_interest: '',
    notes: '',
  });
  const [movementForm, setMovementForm] = useState({
    wallet_id: '',
    movement_type: 'DEX buy',
    token_symbol: '',
    token_contract: '',
    token_amount: '',
    estimated_usd_value: '',
    transaction_hash: '',
    protocol: '',
    transaction_time: dateForInput(),
    data_quality_score: '75',
  });

  const filteredWallets = useMemo(() => {
    if (!chainFilter) return wallets;
    return wallets.filter((wallet) => wallet.chain === chainFilter);
  }, [chainFilter, wallets]);

  const filteredMovements = useMemo(() => {
    if (movementFilter === 'review') return movements.filter((movement) => movement.manual_review_required);
    if (movementFilter === 'alerts') return movements.filter((movement) => movement.alert_threshold_crossed);
    return movements;
  }, [movementFilter, movements]);

  async function api<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
      ...options,
    });
    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;
      try {
        const body = await response.json();
        detail = body.detail ?? detail;
      } catch {
        // Keep default detail.
      }
      throw new Error(detail);
    }
    return response.json();
  }

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      const [walletData, movementData, summaryData] = await Promise.all([
        api<WhaleWallet[]>('/wallets?limit=250'),
        api<WalletMovement[]>('/wallet-movements?limit=100'),
        api<WalletSummary>('/wallets/summary'),
      ]);
      setWallets(walletData);
      setMovements(movementData);
      setSummary(summaryData);
      setMovementForm((current) => ({ ...current, wallet_id: current.wallet_id || walletData[0]?.id || '' }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load wallet intelligence');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function submitWallet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await api<WhaleWallet>('/wallets', {
        method: 'POST',
        body: JSON.stringify({
          wallet_address: form.wallet_address,
          chain: form.chain.trim().toLowerCase(),
          label: form.label || null,
          wallet_type: form.do_not_copy ? 'Do Not Copy' : form.wallet_type,
          notes: form.notes || null,
          alert_threshold_usd: form.alert_threshold_usd,
          watch_priority: Number(form.watch_priority),
          confidence_weighting: form.confidence_weighting,
          copy_trade_enabled: form.do_not_copy ? false : form.copy_trade_enabled,
          do_not_copy: form.do_not_copy,
          tags: splitList(form.tags),
          sectors_of_interest: splitList(form.sectors_of_interest),
        }),
      });
      setMessage('Wallet added. It will remain paper-trading/research only.');
      setForm((current) => ({
        ...current,
        wallet_address: '',
        label: '',
        tags: '',
        sectors_of_interest: '',
        notes: '',
        copy_trade_enabled: false,
        do_not_copy: false,
      }));
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save wallet');
    } finally {
      setSaving(false);
    }
  }

  async function submitMovement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const wallet = wallets.find((item) => item.id === movementForm.wallet_id);
    if (!wallet) {
      setError('Select a watched wallet before adding a movement.');
      return;
    }
    setMovementSaving(true);
    setError('');
    setMessage('');
    try {
      await api<WalletMovement>('/wallet-movements', {
        method: 'POST',
        body: JSON.stringify({
          wallet_id: movementForm.wallet_id,
          chain: wallet.chain,
          transaction_hash: movementForm.transaction_hash,
          movement_type: movementForm.movement_type,
          token_symbol: movementForm.token_symbol,
          token_contract: movementForm.token_contract || null,
          token_amount: movementForm.token_amount || null,
          estimated_usd_value: movementForm.estimated_usd_value || null,
          protocol: movementForm.protocol || null,
          transaction_time: new Date(movementForm.transaction_time).toISOString(),
          data_quality_score: Number(movementForm.data_quality_score),
          raw_api_payload: {
            source: 'manual_stage1_entry',
            paper_trading_only: true,
          },
        }),
      });
      setMessage('Movement stored. Large movements create review alerts only — no live trading.');
      setMovementForm((current) => ({
        ...current,
        token_symbol: '',
        token_contract: '',
        token_amount: '',
        estimated_usd_value: '',
        transaction_hash: '',
        protocol: '',
        transaction_time: dateForInput(),
      }));
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save movement');
    } finally {
      setMovementSaving(false);
    }
  }

  async function toggleWallet(wallet: WhaleWallet) {
    setError('');
    setMessage('');
    try {
      await api<WhaleWallet>(`/wallets/${wallet.id}/enabled?enabled=${!wallet.enabled}`, {
        method: 'PATCH',
      });
      setMessage(`${wallet.label || wallet.normalized_address} ${wallet.enabled ? 'disabled' : 'enabled'}.`);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update wallet');
    }
  }

  return (
    <main className="app-shell">
      <section className="hero panel">
        <div>
          <p className="eyebrow">Stage 1 · Whale Wallets + Movements</p>
          <h1>Wallet-led intelligence console</h1>
          <p>
            Add watched wallets and manually record wallet movements while polling integrations are built. V1 remains
            research and paper-trading only — no private keys, seed phrases or live trade execution.
          </p>
        </div>
        <button className="ghost-button" onClick={loadData} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </section>

      <section className="stats-grid">
        <Stat label="Total wallets" value={summary.total_wallets} />
        <Stat label="Enabled" value={summary.enabled_wallets} />
        <Stat label="Do Not Copy" value={summary.do_not_copy_wallets} />
        <Stat label="Movements" value={summary.movement_count} />
        <Stat label="Manual review" value={summary.manual_review_movements} />
      </section>

      {error && <div className="notice error">{error}</div>}
      {message && <div className="notice success">{message}</div>}

      <section className="content-grid">
        <form className="panel wallet-form" onSubmit={submitWallet}>
          <div>
            <p className="eyebrow">Add wallet</p>
            <h2>Watchlist entry</h2>
          </div>

          <label>
            Wallet address
            <input required value={form.wallet_address} placeholder="0x…" onChange={(event) => setForm({ ...form, wallet_address: event.target.value })} />
          </label>

          <div className="form-row">
            <label>
              Chain
              <input required value={form.chain} onChange={(event) => setForm({ ...form, chain: event.target.value })} />
            </label>
            <label>
              Wallet type
              <select value={form.wallet_type} disabled={form.do_not_copy} onChange={(event) => setForm({ ...form, wallet_type: event.target.value })}>
                {walletTypes.map((type) => <option key={type}>{type}</option>)}
              </select>
            </label>
          </div>

          <label>
            Label
            <input value={form.label} placeholder="e.g. ETH early accumulator" onChange={(event) => setForm({ ...form, label: event.target.value })} />
          </label>

          <div className="form-row three">
            <label>
              Alert USD
              <input type="number" min="0" value={form.alert_threshold_usd} onChange={(event) => setForm({ ...form, alert_threshold_usd: event.target.value })} />
            </label>
            <label>
              Priority
              <select value={form.watch_priority} onChange={(event) => setForm({ ...form, watch_priority: event.target.value })}>
                <option value="1">1 · Highest</option><option value="2">2</option><option value="3">3 · Normal</option><option value="4">4</option><option value="5">5 · Low</option>
              </select>
            </label>
            <label>
              Confidence
              <input type="number" min="0" max="5" step="0.1" value={form.confidence_weighting} onChange={(event) => setForm({ ...form, confidence_weighting: event.target.value })} />
            </label>
          </div>

          <label>Tags<input value={form.tags} placeholder="comma separated" onChange={(event) => setForm({ ...form, tags: event.target.value })} /></label>
          <label>Sectors of interest<input value={form.sectors_of_interest} placeholder="AI, DeFi, infrastructure" onChange={(event) => setForm({ ...form, sectors_of_interest: event.target.value })} /></label>
          <label>Notes<textarea value={form.notes} placeholder="Why this wallet is worth watching." onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>

          <div className="checks">
            <label><input type="checkbox" checked={form.copy_trade_enabled} disabled={form.do_not_copy} onChange={(event) => setForm({ ...form, copy_trade_enabled: event.target.checked })} />Paper copy-review allowed</label>
            <label><input type="checkbox" checked={form.do_not_copy} onChange={(event) => setForm({ ...form, do_not_copy: event.target.checked, copy_trade_enabled: false })} />Do Not Copy</label>
          </div>

          <button className="primary-button" disabled={saving}>{saving ? 'Saving…' : 'Add watched wallet'}</button>
        </form>

        <section className="panel wallet-list">
          <div className="list-header">
            <div><p className="eyebrow">Watched wallets</p><h2>{filteredWallets.length} shown</h2></div>
            <label className="compact-label">Chain filter<input value={chainFilter} placeholder="all" onChange={(event) => setChainFilter(event.target.value.trim().toLowerCase())} /></label>
          </div>

          {loading ? <p className="muted">Loading wallets…</p> : filteredWallets.length === 0 ? <p className="muted">No wallets yet. Add the first watched wallet to begin Stage 1 tracking.</p> : (
            <div className="cards">
              {filteredWallets.map((wallet) => (
                <article className="wallet-card" key={wallet.id}>
                  <div className="wallet-card-top">
                    <div><h3>{wallet.label || 'Unlabelled wallet'}</h3><p className="address">{wallet.normalized_address}</p></div>
                    <span className={wallet.enabled ? 'badge enabled' : 'badge disabled'}>{wallet.enabled ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="wallet-meta"><span>{wallet.chain}</span><span>{wallet.wallet_type}</span><span>Priority {wallet.watch_priority}</span><span>{formatUsd(wallet.alert_threshold_usd)} alert</span></div>
                  {(wallet.tags.length > 0 || wallet.sectors_of_interest.length > 0) && <div className="tag-row">{[...wallet.tags, ...wallet.sectors_of_interest].map((tag) => <span key={tag}>{tag}</span>)}</div>}
                  <div className="policy-row"><span>{wallet.copy_trade_enabled ? 'Paper copy-review allowed' : 'No copy-review'}</span>{wallet.do_not_copy && <strong>Do Not Copy</strong>}</div>
                  <button className="ghost-button" onClick={() => toggleWallet(wallet)}>{wallet.enabled ? 'Disable' : 'Enable'}</button>
                </article>
              ))}
            </div>
          )}
        </section>
      </section>

      <section className="content-grid movements-grid">
        <form className="panel wallet-form" onSubmit={submitMovement}>
          <div>
            <p className="eyebrow">Add movement</p>
            <h2>Manual movement entry</h2>
            <p className="muted">Use this smoke workflow until automated wallet polling is added.</p>
          </div>
          <label>
            Wallet
            <select required value={movementForm.wallet_id} onChange={(event) => setMovementForm({ ...movementForm, wallet_id: event.target.value })}>
              <option value="">Select wallet</option>
              {wallets.map((wallet) => <option key={wallet.id} value={wallet.id}>{wallet.label || wallet.normalized_address} · {wallet.chain}</option>)}
            </select>
          </label>
          <div className="form-row">
            <label>Movement type<select value={movementForm.movement_type} onChange={(event) => setMovementForm({ ...movementForm, movement_type: event.target.value })}>{movementTypes.map((type) => <option key={type}>{type}</option>)}</select></label>
            <label>Token symbol<input required value={movementForm.token_symbol} placeholder="ETH" onChange={(event) => setMovementForm({ ...movementForm, token_symbol: event.target.value.toUpperCase() })} /></label>
          </div>
          <label>Transaction hash<input required value={movementForm.transaction_hash} placeholder="0x transaction hash" onChange={(event) => setMovementForm({ ...movementForm, transaction_hash: event.target.value })} /></label>
          <label>Token contract<input value={movementForm.token_contract} placeholder="0x token contract" onChange={(event) => setMovementForm({ ...movementForm, token_contract: event.target.value })} /></label>
          <div className="form-row three">
            <label>Token amount<input type="number" step="any" value={movementForm.token_amount} onChange={(event) => setMovementForm({ ...movementForm, token_amount: event.target.value })} /></label>
            <label>Estimated USD<input type="number" min="0" step="any" value={movementForm.estimated_usd_value} onChange={(event) => setMovementForm({ ...movementForm, estimated_usd_value: event.target.value })} /></label>
            <label>Quality 0-100<input type="number" min="0" max="100" value={movementForm.data_quality_score} onChange={(event) => setMovementForm({ ...movementForm, data_quality_score: event.target.value })} /></label>
          </div>
          <div className="form-row">
            <label>Protocol<input value={movementForm.protocol} placeholder="Uniswap, Binance, bridge…" onChange={(event) => setMovementForm({ ...movementForm, protocol: event.target.value })} /></label>
            <label>Transaction time<input type="datetime-local" value={movementForm.transaction_time} onChange={(event) => setMovementForm({ ...movementForm, transaction_time: event.target.value })} /></label>
          </div>
          <button className="primary-button" disabled={movementSaving || wallets.length === 0}>{movementSaving ? 'Saving…' : 'Store movement'}</button>
        </form>

        <section className="panel wallet-list">
          <div className="list-header">
            <div><p className="eyebrow">Recent movements</p><h2>{filteredMovements.length} shown</h2></div>
            <label className="compact-label">View<select value={movementFilter} onChange={(event) => setMovementFilter(event.target.value as 'all' | 'review' | 'alerts')}><option value="all">All</option><option value="review">Manual review</option><option value="alerts">Large alerts</option></select></label>
          </div>
          {filteredMovements.length === 0 ? <p className="muted">No movements yet. Store a movement to begin building signal history.</p> : (
            <div className="cards">
              {filteredMovements.map((movement) => {
                const wallet = wallets.find((item) => item.id === movement.wallet_id);
                return (
                  <article className="wallet-card movement-card" key={movement.id}>
                    <div className="wallet-card-top">
                      <div><h3>{movement.movement_type} · {movement.token_symbol}</h3><p className="address">{movement.transaction_hash}</p></div>
                      <span className={movement.alert_threshold_crossed ? 'badge alert' : 'badge enabled'}>{movement.alert_threshold_crossed ? 'Large alert' : 'Stored'}</span>
                    </div>
                    <div className="wallet-meta"><span>{wallet?.label || wallet?.normalized_address || 'Unknown wallet'}</span><span>{movement.chain}</span><span>{formatUsd(movement.estimated_usd_value)}</span><span>Quality {movement.data_quality_score}</span></div>
                    <div className="policy-row"><span>{new Date(movement.transaction_time).toLocaleString()}</span>{movement.manual_review_required && <strong>Manual review</strong>}</div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return <div className="stat-card"><span>{label}</span><strong>{value}</strong></div>;
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode><App /></React.StrictMode>,
);
