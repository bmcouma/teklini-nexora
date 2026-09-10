import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { hasApiKey, setApiKey } from "../lib/api";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/new", label: "New Incident" },
];

export function AppShell() {
  const [key, setKey] = useState("");
  const [configured, setConfigured] = useState(hasApiKey());

  function saveKey() {
    setApiKey(key);
    setConfigured(Boolean(key.trim()));
  }

  return (
    <div className="flex min-h-screen flex-col bg-graphite md:flex-row">
      <aside className="flex w-full shrink-0 flex-col border-b border-border bg-graphite-2 md:w-60 md:border-b-0 md:border-r">
        <div className="flex items-center gap-2 border-b border-border px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-cyan/10 text-cyan">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M4 12L10 6M4 12L10 18M4 12H14M20 12L14 6M20 12L14 18"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <p className="font-heading text-sm font-semibold text-white">Teklini Nexora</p>
            <p className="text-[11px] text-silver/50">IT Operations</p>
          </div>
        </div>

        <nav className="flex gap-1 px-3 py-4 md:flex-col">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-cyan/10 text-cyan"
                    : "text-silver/70 hover:bg-graphite-3 hover:text-silver"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto border-t border-border px-5 py-4 text-[11px] text-silver/40">
          <div className="mb-4">
            <p className="mb-2 text-silver/60">API access</p>
            <p className="mb-2">{configured ? "Session key configured" : "Demo mode or public API"}</p>
            <input
              type="password"
              value={key}
              onChange={(event) => setKey(event.target.value)}
              placeholder="Enter session API key"
              aria-label="Session API key"
              className="mb-2 w-full rounded border border-border bg-graphite px-2 py-1.5 text-[11px] text-silver outline-none focus:border-cyan"
            />
            <button
              type="button"
              onClick={saveKey}
              className="mr-2 rounded border border-cyan/30 px-2 py-1 text-cyan hover:bg-cyan/10"
            >
              Use key
            </button>
            {configured && (
              <button
                type="button"
                onClick={() => {
                  setKey("");
                  setApiKey("");
                  setConfigured(false);
                }}
                className="rounded border border-border px-2 py-1 text-silver/60 hover:text-silver"
              >
                Clear
              </button>
            )}
            <p className="mt-2">Keys are user-provided and kept for this browser session only.</p>
          </div>
          Multi-Agent Intelligence for IT Operations
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
