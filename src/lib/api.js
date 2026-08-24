const API = import.meta.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_API_URL || '';
export async function request(path, options = {}) {
  const token = localStorage.getItem('ingrelens_token');
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.');
  return data;
}
export const auth = (path, body) => request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export async function submitScan({ file, text, productName, mode }) {
  const form = new FormData(); if (file) form.append('file', file); if (text) form.append('text', text); form.append('product_name', productName); form.append('mode', mode);
  return request('/api/scan', { method: 'POST', body: form });
}