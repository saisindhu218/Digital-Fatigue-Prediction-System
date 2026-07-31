import { motion } from 'framer-motion';
import { Download, CheckCircle2, Loader2, Laptop, Copy, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

interface AgentSetupPageProps {
  onConnected: () => void;
  onSkip: () => void;
}

export default function AgentSetupPage({ onConnected, onSkip }: Readonly<AgentSetupPageProps>) {
  const [pairingCode, setPairingCode] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [checking, setChecking] = useState(true);

  const userId = localStorage.getItem("user_id");

  const generateCode = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_BASE}/pairing/generate?user_id=${userId}`, { method: "POST" });
      const data = await res.json();
      setPairingCode(data.pairing_code);
    } catch (e) {
      console.error("Failed to generate pairing code", e);
    }
  };

  const checkConnected = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API_BASE}/pairing/agent-status?user_id=${userId}`);
      if (!res.ok) return;
      const data = await res.json();
      const anyOnline = (data.devices || []).some((d: any) => d.online);
      setChecking(false);
      if (anyOnline) onConnected();
    } catch (e) {
      setChecking(false);
      console.error("Failed to check agent status", e);
    }
  };

  const handleCopy = () => {
    if (!pairingCode) return;
    navigator.clipboard.writeText(pairingCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  useEffect(() => {
    generateCode();
    checkConnected();

    // Refresh the pairing code every 4 minutes (codes expire after 5)
    // so it never goes stale while someone's mid-setup.
    const codeInterval = setInterval(generateCode, 4 * 60 * 1000);
    // Poll every 4s -- as soon as the agent's first heartbeat lands,
    // this flips straight into the dashboard with no manual refresh.
    const statusInterval = setInterval(checkConnected, 4000);

    return () => {
      clearInterval(codeInterval);
      clearInterval(statusInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-8 max-w-lg w-full"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-lg bg-primary/10">
            <Laptop className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Connect this laptop</h1>
        </div>

        <p className="text-sm text-muted-foreground mb-6">
          To start tracking your fatigue &amp; productivity, install the small background
          agent below. It runs quietly and updates your dashboard automatically —
          no need to keep this browser tab open.
        </p>

        <div className="space-y-3 mb-6">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/15 text-primary text-xs font-semibold flex items-center justify-center mt-0.5">1</div>
            <div className="flex-1">
              <p className="text-sm font-medium">Download the agent</p>
              <a href="/downloads/CongiGuardAgent.exe" download>
                <Button className="mt-2 gap-2" size="sm">
                  <Download className="w-4 h-4" />
                  Download for Windows
                </Button>
              </a>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/15 text-primary text-xs font-semibold flex items-center justify-center mt-0.5">2</div>
            <div className="flex-1">
              <p className="text-sm font-medium">Run it once, then enter this code</p>
              <p className="text-xs text-muted-foreground mt-1">
                Open the downloaded file and, when it asks, enter:
              </p>
              <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary/50 mt-2">
                <code className="text-sm font-mono font-semibold tracking-wider flex-1">
                  {pairingCode || "········"}
                </code>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleCopy}>
                  {copied ? <CheckCircle className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/15 text-primary text-xs font-semibold flex items-center justify-center mt-0.5">3</div>
            <div className="flex-1">
              <p className="text-sm font-medium">That's it</p>
              <p className="text-xs text-muted-foreground mt-1">
                This page will detect it automatically and take you to your dashboard —
                no need to refresh.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
          {checking
            ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Waiting for the agent to connect...</>
            : <><CheckCircle2 className="w-3.5 h-3.5" /> Not connected yet — keep this tab open after running the agent.</>
          }
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={onSkip}
            className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
          >
            Skip for now, I'll set this up later
          </button>
        </div>
      </motion.div>
    </div>
  );
}
