import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Camera, Settings, Activity, Hand, Power,
  BookOpen, History, Volume2, MousePointer,
  Layers, ChevronDown
} from 'lucide-react';

// Human-readable labels for each action
const ACTION_LABELS = {
  none:            'No Action',
  cursor_move:     '🖱️ Move Cursor',
  left_click:      '🖱️ Left Click',
  right_click:     '🖱️ Right Click',
  play_pause:      '⏯️ Play / Pause',
  volume_up:       '🔊 Volume Up',
  volume_down:     '🔉 Volume Down',
  mute:            '🔇 Mute',
  next_track:      '⏭️ Next Track',
  prev_track:      '⏮️ Prev Track',
  next_slide:      '▶️ Next Slide',
  prev_slide:      '◀️ Prev Slide',
  scroll_up:       '⬆️ Scroll Up',
  scroll_down:     '⬇️ Scroll Down',
  open_chrome:     '🌐 Open Chrome',
  open_explorer:   '📁 Open Explorer',
  open_calc:       '🔢 Open Calculator',
  open_vscode:     '💻 Open VS Code',
  open_spotify:    '🎵 Open Spotify',
  open_terminal:   '🖥️ Open Terminal',
  alt_tab:         '🔄 Alt + Tab',
  win_key:         '🪟 Windows Key',
  close_window:    '❌ Close Window',
  copy:            '📋 Copy',
  paste:           '📋 Paste',
  undo:            '↩️ Undo',
  custom_shortcut: '⌨️ Custom Shortcut',
};

const ALL_ACTIONS = Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label }));

export default function App() {
  const [activeTab, setActiveTab]       = useState('live');
  const [ws, setWs]                     = useState(null);
  const [connected, setConnected]       = useState(false);
  const [isDetecting, setIsDetecting]   = useState(false);
  const [gesture, setGesture]           = useState('None');
  const [hand, setHand]                 = useState('');
  const [action, setAction]             = useState('Idle');
  const [videoFrame, setVideoFrame]     = useState(null);
  const [logs, setLogs]                 = useState([]);
  const [mappings, setMappings]         = useState({});
  const [history, setHistory]           = useState([]);
  const [editGesture, setEditGesture]   = useState(null);
  const [sensitivity, setSensitivity]   = useState(2800);
  const [sensitivityRange, setSensitivityRange] = useState({ min: 500, max: 8000 });
  const wsRef = useRef(null);

  // ── WebSocket connection ──────────────────────────────────────────────────
  useEffect(() => {
    let socket;
    let retryTimer;

    const connect = () => {
      socket = new WebSocket('ws://localhost:8765');
      wsRef.current = socket;

      socket.onopen = () => {
        setConnected(true);
        setWs(socket);
        socket.send(JSON.stringify({ action: 'get_mappings' }));
        socket.send(JSON.stringify({ action: 'get_settings' }));
      };

      socket.onmessage = (evt) => {
        const data = JSON.parse(evt.data);

        if (data.type === 'update') {
          if (data.frame)   setVideoFrame(data.frame);
          if (data.gesture) setGesture(data.gesture);
          if (data.hand)    setHand(data.hand);
          if (data.action)  setAction(data.action);
          if (data.gesture && data.gesture !== 'None' && data.action && data.action !== 'Idle') {
            setLogs(prev => [
              { gesture: data.gesture, action: data.action, time: new Date().toLocaleTimeString() },
              ...prev
            ].slice(0, 12));
          }
        } else if (data.type === 'mappings') {
          setMappings(data.data);
        } else if (data.type === 'mapping_updated') {
          socket.send(JSON.stringify({ action: 'get_mappings' }));
        } else if (data.type === 'history') {
          setHistory(data.data);
        } else if (data.type === 'settings') {
          setSensitivity(data.data.sensitivity);
          setSensitivityRange({ min: data.data.min_sensitivity, max: data.data.max_sensitivity });
        }
      };

      socket.onclose = () => {
        setConnected(false);
        setWs(null);
        wsRef.current = null;
        retryTimer = setTimeout(connect, 2500);
      };

      socket.onerror = () => socket.close();
    };

    connect();
    return () => {
      clearTimeout(retryTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // ── Helpers ───────────────────────────────────────────────────────────────
  const send = useCallback((payload) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  const toggleDetection = () => {
    if (!connected) return;
    if (isDetecting) {
      send({ action: 'stop' });
      setIsDetecting(false);
      setVideoFrame(null);
    } else {
      send({ action: 'start' });
      setIsDetecting(true);
    }
  };

  const updateMapping = (gestureName, mappedAction, shortcut = '') => {
    send({ action: 'update_mapping', gesture: gestureName, mapped_action: mappedAction, shortcut });
    setMappings(prev => ({
      ...prev,
      [gestureName]: { action: mappedAction, shortcut }
    }));
    setEditGesture(null);
  };

  const loadHistory = () => send({ action: 'get_history' });

  const updateSensitivity = (value) => {
    const num = Number(value);
    setSensitivity(num); // update immediately for a responsive slider
    send({ action: 'update_sensitivity', sensitivity: num });
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-screen select-none overflow-hidden"
      style={{
        background: '#1E1E1E',
        fontFamily: "'Inter', system-ui, sans-serif",
        color: '#264F78',
      }}
    >
      {/* ── Title Bar ─────────────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-4 py-2.5 border-b"
        style={{
          WebkitAppRegion: 'drag',
          borderColor: 'rgba(255,255,255,0.07)',
          background: 'rgba(255,255,255,0.03)',
        }}
      >
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: '#264F78' }}>
            <Hand size={14} color="white" />
          </div>
          <span className="text-white font-semibold text-sm tracking-tight">GestureVision</span>
        </div>
        <div className="flex items-center gap-2" style={{ WebkitAppRegion: 'no-drag' }}>
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
            connected ? 'text-[#264F78] bg-[#264F78]/15' : 'text-red-300 bg-red-500/15'
          }`}>
            {connected ? '● Connected' : '○ Offline'}
          </span>
        </div>
      </div>

      {/* ── Body ──────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 py-3" style={{ WebkitAppRegion: 'no-drag', scrollbarWidth: 'thin' }}>

        {/* ═══════ LIVE TAB ═══════ */}
        {activeTab === 'live' && (
          <div className="flex flex-col gap-3">

            {/* Gesture + Action status */}
            <div className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest mb-0.5">Gesture</p>
                  <p className="text-white font-bold text-lg leading-tight">{gesture}</p>
                  {hand && <p className="text-[10px] text-slate-500">{hand} hand</p>}
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-slate-400 uppercase tracking-widest mb-0.5">Action</p>
                  <p className="font-semibold text-sm" style={{ color: '#264F78' }}>{action}</p>
                </div>
              </div>
            </div>

            {/* Start / Stop button */}
            <button
              onClick={toggleDetection}
              disabled={!connected}
              className="w-full py-3.5 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm transition-all duration-200 active:scale-95"
              style={isDetecting
                ? { background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5' }
                : { background: '#264F78', color: 'white', boxShadow: '0 4px 20px rgba(38,79,120,0.3)' }
              }
            >
              <Power size={16} />
              {isDetecting ? 'Stop Detection' : 'Start Detection'}
            </button>

            {/* Live Camera Feed */}
            <div className="rounded-xl overflow-hidden flex items-center justify-center"
              style={{
                minHeight: 160,
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid rgba(255,255,255,0.06)'
              }}>
              {isDetecting && videoFrame ? (
                <img
                  src={`data:image/jpeg;base64,${videoFrame}`}
                  alt="Live"
                  className="w-full h-auto"
                  style={{ display: 'block' }}
                />
              ) : (
                <div className="flex flex-col items-center gap-2 py-8 text-slate-500">
                  <Camera size={28} className="opacity-40" />
                  <p className="text-xs opacity-60">
                    {connected ? 'Click Start Detection to begin' : 'Waiting for backend…'}
                  </p>
                </div>
              )}
            </div>

            {/* Recent activity */}
            {logs.length > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1.5">Recent Activity</p>
                <div className="flex flex-col gap-1">
                  {logs.map((log, i) => (
                    <div key={i}
                      className="flex justify-between items-center px-2.5 py-1.5 rounded-lg text-xs"
                      style={{
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.05)',
                        opacity: 1 - i * 0.07
                      }}
                    >
                      <span className="text-white font-medium">{log.gesture}</span>
                      <span style={{ color: '#264F78' }}>{log.action}</span>
                      <span className="text-slate-600">{log.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══════ GESTURE LIBRARY TAB ═══════ */}
        {activeTab === 'library' && (
          <div className="flex flex-col gap-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">
              Tap a gesture to change its action
            </p>

            {Object.entries(mappings).length === 0 && (
              <p className="text-slate-500 text-xs text-center py-6">Loading gesture library…</p>
            )}

            {Object.entries(mappings).map(([gestureName, cfg]) => (
              <div key={gestureName}>
                <button
                  onClick={() => setEditGesture(editGesture === gestureName ? null : gestureName)}
                  className="w-full flex justify-between items-center px-3 py-2.5 rounded-xl text-left transition-all"
                  style={{
                    background: editGesture === gestureName
                      ? 'rgba(16,185,129,0.1)'
                      : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${editGesture === gestureName ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.07)'}`,
                  }}
                >
                  <div>
                    <p className="text-white text-sm font-medium">{gestureName}</p>
                    <p className="text-xs" style={{ color: '#264F78' }}>{ACTION_LABELS[cfg.action] || cfg.action}</p>
                  </div>
                  <ChevronDown size={14} className="text-slate-500"
                    style={{ transform: editGesture === gestureName ? 'rotate(180deg)' : 'none', transition: '0.2s' }}
                  />
                </button>

                {/* Inline editor */}
                {editGesture === gestureName && (
                  <div className="mt-1 rounded-xl px-3 py-3 flex flex-col gap-2"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <p className="text-[10px] text-slate-400 uppercase tracking-widest">Choose Action</p>
                    <select
                      defaultValue={cfg.action}
                      onChange={e => updateMapping(gestureName, e.target.value)}
                      className="w-full text-xs rounded-lg px-2 py-1.5"
                      style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                    >
                      {ALL_ACTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ═══════ HISTORY TAB ═══════ */}
        {activeTab === 'history' && (
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center mb-1">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest">Detection Log</p>
              <button
                onClick={loadHistory}
                className="text-[10px] transition-colors"
                style={{ color: '#264F78' }}
              >↻ Refresh</button>
            </div>
            {history.length === 0 ? (
              <p className="text-slate-500 text-xs text-center py-6">No history yet. Start detecting!</p>
            ) : history.map((h, i) => (
              <div key={i} className="flex justify-between items-center px-2.5 py-2 rounded-lg text-xs"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span className="text-white font-medium">{h.gesture}</span>
                <span style={{ color: '#264F78' }}>{h.action}</span>
                <span className="text-slate-600 text-[10px]">{new Date(h.time).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        )}

        {/* ═══════ SETTINGS TAB ═══════ */}
        {activeTab === 'settings' && (
          <div className="flex flex-col gap-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Configuration</p>

            <div className="rounded-xl p-3 flex flex-col gap-3"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
              <div>
                <label className="text-xs text-slate-400 block mb-1.5">Camera</label>
                <select className="w-full text-sm rounded-lg px-2 py-1.5"
                  style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}>
                  <option>0 — Default Camera</option>
                  <option>1 — External Camera</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1.5">Gesture Confidence Threshold</label>
                <input type="range" min="1" max="10" defaultValue="7"
                  className="w-full" style={{ accentColor: '#264F78' }} />
              </div>

              <div>
                <label className="text-xs text-slate-400 flex justify-between mb-1.5">
                  <span>Cursor Sensitivity</span>
                  <span className="font-medium" style={{ color: '#264F78' }}>{sensitivity}</span>
                </label>
                <input
                  type="range"
                  min={sensitivityRange.min}
                  max={sensitivityRange.max}
                  step="100"
                  value={sensitivity}
                  onChange={e => updateSensitivity(e.target.value)}
                  disabled={!connected}
                  className="w-full" style={{ accentColor: '#264F78' }}
                />
                <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
                  <span>Precise</span>
                  <span>Fast</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">
                  Controls how far the cursor moves per unit of hand motion when using the
                  Pointing Finger (Move Cursor) gesture. Changes apply immediately and are saved.
                </p>
              </div>
            </div>

            <div className="rounded-xl p-3"
              style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <p className="text-xs text-slate-400 font-medium mb-1">Supported Gestures</p>
              <ul className="text-[11px] text-slate-500 space-y-0.5">
                {[
                  '✋ Open Palm — configurable',
                  '✊ Closed Fist — Play/Pause (default)',
                  '☝️ Pointing Finger — Cursor move (default)',
                  '🤌 Pinch — Left click (default)',
                  '✌️ Victory Sign — Next slide (default)',
                  '👍 Thumbs Up — Volume up (default)',
                  '👎 Thumbs Down — Volume down (default)',
                  '🤟 Rock Sign — Mute (default)',
                  '🖖 Three Fingers — Open Chrome (default)',
                ].map((g, i) => <li key={i}>{g}</li>)}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* ── Nav Bar ───────────────────────────────────────────────────────── */}
      <div
        className="flex justify-around items-center py-2 px-1"
        style={{
          WebkitAppRegion: 'no-drag',
          background: 'rgba(255,255,255,0.03)',
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        {[
          { id: 'live',     icon: <Activity size={18} />,   label: 'Live'    },
          { id: 'library',  icon: <BookOpen size={18} />,   label: 'Library' },
          { id: 'history',  icon: <History size={18} />,    label: 'History' },
          { id: 'settings', icon: <Settings size={18} />,   label: 'Settings'},
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); if (tab.id === 'history') loadHistory(); }}
            className="flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all"
            style={{
              color:      activeTab === tab.id ? '#264F78' : 'rgba(255,255,255,0.35)',
              background: activeTab === tab.id ? 'rgba(38,79,120,0.12)' : 'transparent',
            }}
          >
            {tab.icon}
            <span className="text-[9px] font-medium">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
