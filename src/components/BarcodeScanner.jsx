import React, { useEffect, useRef, useState } from 'react';
import { BrowserMultiFormatReader } from '@zxing/browser';
import { X, ScanLine, Keyboard, Check } from 'lucide-react';

export default function BarcodeScanner({ onDetected, onCancel }) {
  const videoRef = useRef(null);
  const controlsRef = useRef(null);
  const [manual, setManual] = useState('');
  const [error, setError] = useState('');
  const [showManual, setShowManual] = useState(false);

  useEffect(() => {
    if (showManual) return undefined;
    const reader = new BrowserMultiFormatReader();
    let cancelled = false;
    (async () => {
      try {
        const devices = await BrowserMultiFormatReader.listVideoInputDevices();
        const back = devices.find(d => /back|rear|environment/i.test(d.label)) || devices[devices.length - 1];
        controlsRef.current = await reader.decodeFromVideoDevice(back?.deviceId, videoRef.current, (result, err, controls) => {
          if (cancelled) return;
          if (result) {
            controls?.stop();
            onDetected(result.getText());
          }
        });
      } catch (e) {
        setError('Camera access is unavailable. Enter the barcode number manually.');
        setShowManual(true);
      }
    })();
    return () => {
      cancelled = true;
      try { controlsRef.current?.stop(); } catch { /* noop */ }
    };
  }, [showManual, onDetected]);

  function submitManual(e) {
    e.preventDefault();
    const code = manual.replace(/\s+/g, '');
    if (!/^\d{6,14}$/.test(code)) {
      setError('Enter 6–14 digits from the barcode.');
      return;
    }
    onDetected(code);
  }

  return (
    <div className="camera-screen" data-testid="barcode-scanner">
      <header>
        <button data-testid="barcode-close-button" onClick={onCancel}><X /></button>
        <span>BARCODE SCAN</span>
        <button data-testid="barcode-manual-toggle" onClick={() => { setError(''); setShowManual(s => !s); }}><Keyboard size={18} /></button>
      </header>
      {!showManual ? (
        <>
          <div className="camera-body">
            <video ref={videoRef} autoPlay playsInline muted data-testid="barcode-video" />
            <div className="guide barcode-guide"><i /><i /><i /><i /><span><ScanLine size={13} /> Align the barcode inside the frame</span></div>
          </div>
          <div className="camera-controls">
            {error && <p className="error" data-testid="barcode-error">{error}</p>}
            <button className="camera-upload" data-testid="barcode-manual-button" onClick={() => setShowManual(true)}><Keyboard size={16} /> Enter barcode manually</button>
          </div>
        </>
      ) : (
        <form className="barcode-manual" onSubmit={submitManual} data-testid="barcode-manual-form">
          <span className="kicker">ENTER BARCODE DIGITS</span>
          <input data-testid="barcode-manual-input" inputMode="numeric" pattern="\d*" value={manual} onChange={e => setManual(e.target.value)} placeholder="e.g. 3017620422003" autoFocus />
          {error && <p className="error" data-testid="barcode-error">{error}</p>}
          <button className="button primary" data-testid="barcode-manual-submit"><Check size={17} /> Look up product</button>
          <button type="button" className="camera-upload" onClick={() => { setShowManual(false); setError(''); }}>Back to camera</button>
        </form>
      )}
    </div>
  );
}
