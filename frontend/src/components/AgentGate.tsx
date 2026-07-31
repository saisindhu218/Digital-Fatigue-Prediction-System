import { Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import AgentSetupPage from '@/pages/AgentSetupPage';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const SKIP_KEY = "agent_setup_skipped";

/**
 * Wraps the protected dashboard routes. On first login (or any time no
 * agent has ever connected for this account), shows the "Connect this
 * laptop" onboarding page instead of the dashboard. Once heartbeat data
 * confirms a device is online -- from ANY browser, since this is keyed
 * off user_id, not this session -- it unlocks automatically.
 *
 * "Skip for now" is remembered per-browser (localStorage) so people
 * aren't nagged every single page load, but a fresh browser/device will
 * still see it once, and it re-appears each new login.
 */
export default function AgentGate() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'needs-setup'>('checking');
  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");

  const checkAgent = async () => {
    if (!userId) {
      setStatus('connected'); // don't block rendering if something's off; ProtectedRoute handles auth
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/pairing/agent-status?user_id=${userId}`);
      if (!res.ok) {
        setStatus('needs-setup');
        return;
      }
      const data = await res.json();
      const anyOnline = (data.devices || []).some((d: any) => d.online);

      if (anyOnline) {
        sessionStorage.removeItem(SKIP_KEY);
        setStatus('connected');
      } else if (sessionStorage.getItem(SKIP_KEY) === "true") {
        setStatus('connected');
      } else {
        setStatus('needs-setup');
      }
    } catch (e) {
      console.error("Failed to check agent status", e);
      // Network hiccup shouldn't lock someone out of a dashboard they
      // may have already set up -- fail open.
      setStatus('connected');
    }
  };

  useEffect(() => {
    checkAgent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (status === 'checking') {
    return null;
  }

  if (status === 'needs-setup') {
    return (
      <AgentSetupPage
        onConnected={() => {
          setStatus('connected');
          navigate('/dashboard', { replace: true });
        }}
        onSkip={() => {
          sessionStorage.setItem(SKIP_KEY, "true");
          setStatus('connected');
        }}
      />
    );
  }

  return <Outlet />;
}
