import { useNavigate } from "react-router-dom";
import { Activity, TimerReset } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-6rem] left-[-4rem] h-72 w-72 rounded-full bg-[hsl(var(--primary)/0.10)] blur-3xl" />
        <div className="absolute right-[-5rem] top-24 h-80 w-80 rounded-full bg-[hsl(var(--info)/0.10)] blur-3xl" />
        <div className="absolute bottom-[-5rem] left-1/3 h-64 w-64 rounded-full bg-[hsl(var(--success)/0.08)] blur-3xl" />
      </div>

      <main className="relative z-10 mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between border-b border-border/50 pb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-muted-foreground">FatigueAI</p>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">Fatigue and productivity tracker</h1>
          </div>
          <div className="hidden md:flex items-center gap-2 rounded-full border border-border/70 bg-card/70 px-4 py-2 text-sm text-muted-foreground backdrop-blur">
            <TimerReset className="h-4 w-4 text-[hsl(var(--accent))]" />
            Track work habits in one place
          </div>
        </header>

        <section className="grid flex-1 items-center gap-8 py-12 lg:grid-cols-[1.05fr_0.95fr] lg:py-14">
          <div className="max-w-2xl">
            <p className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-card/80 px-4 py-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4 text-[hsl(var(--primary))]" />
              Simple tracking. Clear predictions. Useful reminders.
            </p>

            <h2 className="mt-6 text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Understand your day at a glance.
            </h2>

            <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
              FatigueAI tracks activity, predicts fatigue, and shows the dashboard insights you need.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <div className="rounded-full border border-border/70 bg-card/80 px-4 py-2 text-sm text-foreground">
                Activity tracking
              </div>
              <div className="rounded-full border border-border/70 bg-card/80 px-4 py-2 text-sm text-foreground">
                Fatigue prediction
              </div>
              <div className="rounded-full border border-border/70 bg-card/80 px-4 py-2 text-sm text-foreground">
                Notifications
              </div>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6 sm:p-8">
            <div className="rounded-2xl border border-border/60 bg-card/60 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold uppercase tracking-[0.25em] text-muted-foreground">Today</p>
                <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">Live</span>
              </div>

              <div className="mt-5 space-y-3">
                <div className="stat-card">
                  <p className="text-sm font-medium text-muted-foreground">Usage</p>
                  <p className="mt-2 text-lg font-semibold text-foreground">Laptop + mobile activity</p>
                </div>
                <div className="stat-card">
                  <p className="text-sm font-medium text-muted-foreground">Prediction</p>
                  <p className="mt-2 text-lg font-semibold text-foreground">Fatigue and productivity trends</p>
                </div>
                <div className="stat-card">
                  <p className="text-sm font-medium text-muted-foreground">Action</p>
                  <p className="mt-2 text-lg font-semibold text-foreground">Notifications and reminders</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <footer className="pb-2 pt-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button size="lg" className="h-12 px-8 text-base" onClick={() => navigate('/login')}>
              Login
            </Button>
            <Button size="lg" variant="outline" className="h-12 px-8 text-base" onClick={() => navigate('/signup')}>
              Sign Up
            </Button>
          </div>
        </footer>
      </main>
    </div>
  );
}