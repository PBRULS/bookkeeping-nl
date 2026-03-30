/**
 * api.js — Thin wrapper around fetch() for all backend calls.
 * Base URL is always the same origin (localhost:5000).
 */
const API_BASE = "/api";

const Api = {
  async get(path, params = {}) {
    const url = new URL(API_BASE + path, location.origin);
    Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
    const res = await fetch(url);
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async post(path, body) {
    const res = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async put(path, body) {
    const res = await fetch(API_BASE + path, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await res.json();
    return res.json();
  },

  async patch(path, body) {
    const res = await fetch(API_BASE + path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await res.json();
    return res.json();
  },

  downloadUrl(path, params = {}) {
    const url = new URL(API_BASE + path, location.origin);
    Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
    return url.toString();
  },
};
