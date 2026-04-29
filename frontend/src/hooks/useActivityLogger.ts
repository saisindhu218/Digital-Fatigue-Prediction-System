import { useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// Simple in-browser activity logger: logs keystrokes, mouse, focus, blur, visibility
export function useActivityLogger() {
  const { user } = useAuth();
  const activityBuffer = useRef<any[]>([]);
  const lastSend = useRef(Date.now());

  useEffect(() => {
    if (!user?.id) return;

    function logEvent(type: string, extra: any = {}) {
      activityBuffer.current.push({
        type,
        ts: new Date().toISOString(),
        ...extra,
      });
    }

    // Event listeners
    const onMouseMove = () => logEvent("mousemove");
    const onKeyDown = (e: KeyboardEvent) => logEvent("keydown", { key: e.key });
    const onFocus = () => logEvent("focus");
    const onBlur = () => logEvent("blur");
    const onVisibility = () => logEvent(document.visibilityState);

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("focus", onFocus);
    window.addEventListener("blur", onBlur);
    document.addEventListener("visibilitychange", onVisibility);

    // Send buffer every 30s or if > 20 events
    const interval = setInterval(() => {
      if (activityBuffer.current.length === 0) return;
      const payload = activityBuffer.current.splice(0, activityBuffer.current.length);
      api.logActivity(user.id, payload).catch(() => {});
      lastSend.current = Date.now();
    }, 30000);

    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("visibilitychange", onVisibility);
      clearInterval(interval);
    };
  }, [user?.id]);
}
