import { motion } from 'framer-motion';
import { Smartphone, Laptop, Wifi, WifiOff, QrCode, Copy, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';

const API_BASE = "http://localhost:8000/api/v1";

export default function DevicePairingPage() {

  const [pairingCode,setPairingCode] = useState<string>("");
  const [copied,setCopied] = useState(false);
  const [status,setStatus] = useState<any>(null);

  const userId = localStorage.getItem("user_id");

  /* ---------------- GET DEVICE STATUS ---------------- */

  const loadStatus = async () => {

    try{

      const res = await fetch(`${API_BASE}/pairing/status?user_id=${userId}`);
      const data = await res.json();

      setStatus(data);

    }catch(e){
      console.error(e);
    }
  };

  /* ---------------- GENERATE PAIR CODE ---------------- */

  const generateCode = async () => {

    try{

      await fetch(`${API_BASE}/pairing/save-user`,{
        method:"POST",
        headers:{ "Content-Type":"application/json"},
        body:JSON.stringify({user_id:userId})
      });

      const res = await fetch(`${API_BASE}/pairing/generate`,{
        method:"POST"
      });

      const data = await res.json();

      setPairingCode(data.pairing_code);

    }catch(e){
      console.error(e);
    }
  };

  /* ---------------- COPY CODE ---------------- */

  const handleCopy = () => {

    navigator.clipboard.writeText(pairingCode);
    setCopied(true);

    setTimeout(()=>setCopied(false),2000);
  };

  /* ---------------- LOAD ON START ---------------- */

  useEffect(()=>{

    loadStatus();
    generateCode();

    const interval = setInterval(loadStatus,5000);

    return ()=>clearInterval(interval);

  },[]);

  if(!status) return null;

  /* ---------------- DEVICE LIST ---------------- */

  const devices = [

    {
      type:"laptop",
      name:"Laptop",
      status: status.laptop ? "connected" : "disconnected",
      lastSynced: status.last_synced || "never",
      dataPoints: status.data_points || 0
    },

    {
      type:"mobile",
      name:"Mobile",
      status: status.mobile ? "connected" : "disconnected",
      lastSynced: status.last_synced || "never",
      dataPoints: status.data_points || 0
    }

  ];

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

              <QrCode className="w-24 h-24 text-muted-foreground/30"/>

            </div>

          </div>

          <p className="text-xs text-muted-foreground text-center mb-4">
            Scan this QR code with the FatigueAI mobile app to pair your device
          </p>

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

            {devices.map(device => (

              <div key={device.type}
                className="p-4 rounded-xl bg-secondary/50 border border-border/30">

                <div className="flex items-center gap-3 mb-3">

                  <div className="p-2.5 rounded-lg bg-primary/10">

                    {device.type==="laptop"
                      ? <Laptop className="w-4 h-4 text-primary"/>
                      : <Smartphone className="w-4 h-4 text-primary"/>
                    }

                  </div>

                  <div className="flex-1">

                    <p className="text-sm font-medium">
                      {device.name}
                    </p>

                    <p className="text-xs text-muted-foreground capitalize">
                      {device.type}
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

                    <p className="text-muted-foreground">Last Synced</p>

                    <p className="font-medium mt-0.5">
                      {device.lastSynced}
                    </p>

                  </div>

                  <div className="p-2.5 rounded-lg bg-background/50">

                    <p className="text-muted-foreground">Data Points</p>

                    <p className="font-medium mt-0.5">
                      {device.dataPoints}
                    </p>

                  </div>

                </div>

              </div>

            ))}

          </div>

        </motion.div>

      </div>

    </div>

  );

}