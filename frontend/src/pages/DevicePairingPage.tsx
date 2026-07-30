import { motion } from 'framer-motion';
import { Smartphone, Laptop, Wifi, WifiOff, QrCode, Copy, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';
import { useUsageData } from '@/hooks/useUsageData';

const API_BASE =
  "https://digital-fatigue-prediction-system.onrender.com/api/v1";

function formatISTDateTime(value?: string | null): string {
  if (!value) return 'Never';

  const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value);
  const normalizedValue = hasTimezone ? value : `${value}Z`;
  const date = new Date(normalizedValue);
  if (Number.isNaN(date.getTime())) return 'Invalid date';

  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

export default function DevicePairingPage() {

  const [pairingCode,setPairingCode] = useState<string>("");
  const [qrCodeUrl, setQrCodeUrl] = useState<string>("");
  const [qrExpiresAt, setQrExpiresAt] = useState<string | null>(null);
  const [copied,setCopied] = useState(false);
  const [status,setStatus] = useState<any>(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState<string | null>(null);
  const usageQuery = useUsageData();

  const userId = localStorage.getItem("user_id");

  const saveActiveUser = async () => {
    if (!userId) return;

    await fetch(`${API_BASE}/pairing/save-user`,{
      method:"POST",
      headers:{ "Content-Type":"application/json"},
      body:JSON.stringify({user_id:userId})
    });
  };

  /* ---------------- GET DEVICE STATUS ---------------- */

  const loadStatus = async () => {
    if (!userId) return;

    try{
      const res = await fetch(`${API_BASE}/pairing/status?user_id=${userId}`);
      const data = await res.json();
      setStatus(data);
      return data;
    }catch(e){
      console.error(e);
      setError("Unable to load device status. Please check your network.");
      return null;
    }
  };

  /* ---------------- GENERATE PAIR CODE ---------------- */

  const generateCode = async (statusData?: any) => {
    if (!userId) {
      throw new Error("Missing user session");
    }

    // Short manual code flow
    const res = await fetch(`${API_BASE}/pairing/generate?user_id=${userId}`,{
      method:"POST"
    });

    const data = await res.json();
    setPairingCode(data.pairing_code);

    // QR scan flow
    const sourceDevice = (statusData?.devices || []).find((d: any) => d.device_type === 'laptop')
      || (statusData?.devices || [])[0];

    const qrRes = await fetch(`${API_BASE}/pairing/generate-qr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_id: sourceDevice?.device_id || `portal_${userId}`,
        device_type: sourceDevice?.device_type || 'laptop',
        device_name: sourceDevice?.device_name || 'FatigueAI Dashboard',
        user_id: userId,
      }),
    });

    if (!qrRes.ok) {
      throw new Error('Failed to generate QR code');
    }

    const qrData = await qrRes.json();
    setQrCodeUrl(qrData.qr_code_url || '');
    setQrExpiresAt(qrData.expires_at || null);
  };

  /* ---------------- COPY CODE ---------------- */

  const handleCopy = () => {
    if (!pairingCode) return;

    navigator.clipboard.writeText(pairingCode);
    setCopied(true);

    setTimeout(()=>setCopied(false),2000);
  };

  /* ---------------- LOAD ON START ---------------- */

  useEffect(()=>{
    const initialize = async () => {
      if (!userId) {
        setError("No active user found. Please log in again.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        await saveActiveUser();
        const statusData = await loadStatus();
        await generateCode(statusData);
      } catch (e) {
        console.error(e);
        setError("Could not initialize device pairing. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };

    initialize();
    const interval = setInterval(loadStatus,5000);

    return ()=>clearInterval(interval);
  },[]);

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Device Pairing</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Loading pairing status...
          </p>
        </div>
        <div className="glass-card rounded-2xl p-6">
          <p className="text-sm text-muted-foreground">Fetching device status and pairing code.</p>
        </div>
      </div>
    );
  }

  if (!status && error) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Device Pairing</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage connected devices and sync status
          </p>
        </div>
        <div className="glass-card rounded-2xl p-6 border border-destructive/30 bg-destructive/5">
          <p className="text-sm text-destructive">{error}</p>
          <p className="text-xs text-muted-foreground mt-2">If the problem persists, please log out and sign back in.</p>
        </div>
      </div>
    );
  }

  /* ---------------- DEVICE LIST ---------------- */

  const devices = status?.devices || [];
  const fallbackLaptopUsage = usageQuery.data?.laptop_usage || [];
  const inferredLaptop = devices.length === 0 ? fallbackLaptopUsage[0] : null;

  const laptopTimestamps = fallbackLaptopUsage
    .map((usage: any) => usage?.timestamp)
    .filter((ts: string | undefined) => !!ts)
    .sort((a: string, b: string) => new Date(a).getTime() - new Date(b).getTime());

  const inferredLaptopPairedAt = laptopTimestamps.length ? laptopTimestamps[0] : null;
  const inferredLaptopLastActive = laptopTimestamps.length ? laptopTimestamps[laptopTimestamps.length - 1] : null;

  let displayDevices = devices;

  if (displayDevices.length === 0 && inferredLaptop) {
    displayDevices = [{
      device_id: inferredLaptop.device_id || 'current-laptop',
      device_name: 'Laptop Device',
      device_type: 'laptop',
      status: 'connected',
      last_active: inferredLaptopLastActive || inferredLaptop.timestamp,
      paired_at: inferredLaptopPairedAt,
    }];
  }

  displayDevices = displayDevices.filter((device: any) => {
    const name = (device?.device_name || '').toLowerCase();
    const id = (device?.device_id || '').toLowerCase();
    const hasTestMarker = /test|sample|mock|demo/.test(name) || /test|sample|mock|demo/.test(id);

    return device?.status === 'connected' && !hasTestMarker;
  });

  return (

    <div className="space-y-6 animate-fade-in">

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Device Pairing</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage connected devices and sync status
        </p>
      </div>

      {/* PAIRING */}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <motion.div
          initial={{opacity:0,y:12}}
          animate={{opacity:1,y:0}}
          className="glass-card rounded-2xl p-6"
        >

          <h2 className="font-semibold mb-4">Pair New Device</h2>

          <div className="flex items-center justify-center mb-5">

            <div className="w-48 h-48 rounded-xl bg-secondary flex items-center justify-center border border-border/50">

              {qrCodeUrl
                ? <img
                    src={qrCodeUrl}
                    alt="Pairing QR Code"
                    className="w-44 h-44 rounded-lg object-contain"
                  />
                : <QrCode className="w-24 h-24 text-muted-foreground/30"/>
              }

            </div>

          </div>

          <p className="text-xs text-muted-foreground text-center mb-4">
            Scan this QR code with the FatigueAI mobile app to pair your device
          </p>

          {qrExpiresAt && (
            <p className="text-[11px] text-muted-foreground text-center mb-3">
              QR valid until {formatISTDateTime(qrExpiresAt)} IST
            </p>
          )}

          <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary/50">

            <span className="text-sm text-muted-foreground flex-1">
              Pairing Code:
            </span>

            <code className="text-sm font-mono font-semibold tracking-wider">
              {pairingCode}
            </code>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleCopy}
            >

              {copied
                ? <CheckCircle className="w-4 h-4 text-success"/>
                : <Copy className="w-4 h-4"/>
              }

            </Button>

          </div>

        </motion.div>


        {/* CONNECTED DEVICES */}

        <motion.div
          initial={{opacity:0,y:12}}
          animate={{opacity:1,y:0}}
          transition={{delay:0.1}}
          className="glass-card rounded-2xl p-6"
        >

          <h2 className="font-semibold mb-4">Connected Devices</h2>

          <div className="space-y-4">

            {displayDevices.length === 0 ? (
              <div className="p-8 text-center">
                <Smartphone className="w-12 h-12 text-muted-foreground/50 mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No devices connected yet.</p>
                <p className="text-xs text-muted-foreground mt-1">Use the pairing code above to connect your first device.</p>
              </div>
            ) : (
              displayDevices.map(device => (

                <div key={device.device_id}
                  className="p-4 rounded-xl bg-secondary/50 border border-border/30">

                  <div className="flex items-center gap-3 mb-3">

                    <div className="p-2.5 rounded-lg bg-primary/10">

                      {device.device_type==="laptop"
                        ? <Laptop className="w-4 h-4 text-primary"/>
                        : <Smartphone className="w-4 h-4 text-primary"/>
                      }

                    </div>

                    <div className="flex-1">

                      <p className="text-sm font-medium">
                        {device.device_name}
                      </p>

                      <p className="text-xs text-muted-foreground capitalize">
                        {device.device_type}
                      </p>

                    </div>

                    <div className="flex items-center gap-1.5">

                      {device.status==="connected"
                        ? <>
                            <Wifi className="w-3.5 h-3.5 text-success"/>
                            <span className="text-xs text-success">Connected</span>
                          </>
                        : <>
                            <WifiOff className="w-3.5 h-3.5 text-destructive"/>
                            <span className="text-xs text-destructive">Disconnected</span>
                          </>
                      }

                    </div>

                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">

                    <div className="p-2.5 rounded-lg bg-background/50">

                      <p className="text-muted-foreground">Last Active</p>

                      <p className="font-medium mt-0.5">
                        {formatISTDateTime(device.last_active)}
                      </p>

                    </div>

                    <div className="p-2.5 rounded-lg bg-background/50">

                      <p className="text-muted-foreground">Paired At</p>

                      <p className="font-medium mt-0.5">
                        {device.paired_at ? formatISTDateTime(device.paired_at) : 'Not paired'}
                      </p>

                    </div>

                  </div>
                     

                     {device.device_type === "mobile" && (
  <Button
    variant="destructive"
    size="sm"
    className="mt-2 px-3 py-1 text-xs w-auto"
    onClick={async () => {
      await fetch(`${API_BASE}/pairing/disconnect?device_id=${device.device_id}`, {
        method: "POST"
      });
      loadStatus();
    }}
  >
    Disconnect
  </Button>
)}
                </div>

              ))
            )}

          </div>

        </motion.div>

      </div>

    </div>

  );

}