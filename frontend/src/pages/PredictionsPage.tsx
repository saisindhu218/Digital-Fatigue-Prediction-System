import { useUsageData } from '@/hooks/useUsageData';

/* -------- HELPERS -------- */

function formatHours(hours: number) {
  const totalMinutes = Math.round(hours * 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

function getPersonality(fatigueScore: number, productivityScore: number) {
  if (fatigueScore > 60) {
    return {
      title: 'Overworked User',
      description: 'You tend to work continuously without enough breaks, leading to fatigue.',
    };
  }

  if (productivityScore < 60) {
    return {
      title: 'Distracted User',
      description: 'Frequent app switching and distractions are reducing your efficiency.',
    };
  }

  if (productivityScore > 80) {
    return {
      title: 'Highly Focused',
      description: 'You are maintaining strong focus and consistent productivity.',
    };
  }

  return {
    title: 'Balanced User',
    description: 'You maintain a healthy balance between focus and breaks.',
  };
}

function getRisk(fatigueScore: number, productivityScore: number) {
  if (fatigueScore > 60) {
    return { label: 'High', colorClass: 'text-red-400' };
  }

  if (productivityScore < 70) {
    return { label: 'Moderate', colorClass: 'text-yellow-400' };
  }

  return { label: 'Low', colorClass: 'text-green-400' };
}

function getSuggestedActions(fatigueScore: number, productivityScore: number) {
  if (fatigueScore > 70) {
    return [
      'Take a short break after each focused session.',
      'Limit app switching while working.',
      'Do a quick stretch or walk to refresh your focus.',
    ];
  }

  if (productivityScore < 60) {
    return [
      'Use time blocks of 25 minutes with short breaks.',
      'Turn off non-essential notifications.',
      'Focus on one task at a time.',
    ];
  }

  return [
    'Keep the current pace with periodic breaks.',
    'Stay hydrated and avoid multitasking.',
    'Review progress at regular intervals.',
  ];
}

function getBiggestIssue(fatigueScore: number, productivityScore: number) {
  if (fatigueScore > productivityScore) {
    return { label: 'High Fatigue', value: fatigueScore };
  }

  return { label: 'Low Productivity', value: 100 - productivityScore };
}

/* -------- MAIN -------- */

export default function PredictionsPage() {
  const { data } = useUsageData();
  if (!data) return null;

  const { fatigue, productivity } = data.predictions;

  const personality = getPersonality(fatigue.fatigue_score, productivity.productivity_score);
  const risk = getRisk(fatigue.fatigue_score, productivity.productivity_score);

  const focusScore = Math.round(
    (productivity.productivity_score - fatigue.fatigue_score / 2)
  );

  const explanation = `
Based on your recent usage patterns, your productivity is ${productivity.productivity_score}% 
while fatigue is ${fatigue.fatigue_score}%. 

This indicates that your efficiency is ${
    productivity.productivity_score > 75 ? "good" : "affected"
  }, but ${
    fatigue.fatigue_score > 50 ? "fatigue is increasing" : "fatigue is under control"
  }.
`;

  const biggestIssue = getBiggestIssue(fatigue.fatigue_score, productivity.productivity_score);

const bestTime =
  fatigue.fatigue_score < 40
    ? "Morning (9AM - 12PM)"
    : "Evening (6PM - 9PM)";

const improvement = Math.round(
  (100 - productivity.productivity_score) * 0.6
);

const recoverableHours = productivity.productivity_loss_hours * 0.6;
const fatigueFactors = fatigue.factors ?? [];
  const suggestedActions = getSuggestedActions(fatigue.fatigue_score, productivity.productivity_score);

return (
  <div className="space-y-6 animate-fade-in">

    {/* HEADER */}
    <div className="space-y-1">
      <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary via-violet-400 to-cyan-400 bg-clip-text text-transparent">
        AI Predictions
      </h1>
      <p className="text-sm text-muted-foreground max-w-2xl">
        Simple insights from your recent activity
      </p>
    </div>

    {/* 🧠 SIMPLE SUMMARY */}
    <div className="glass-card p-6 rounded-2xl border border-primary/15 bg-gradient-to-br from-primary/8 via-background to-background shadow-sm">
      <div className="flex items-center justify-between gap-3 mb-3">
        <p className="text-sm text-muted-foreground">Summary</p>
        <span className="text-[11px] uppercase tracking-[0.18em] text-primary/90 bg-primary/10 px-2.5 py-1 rounded-full">
          Current profile
        </span>
      </div>

      <p className="text-xl md:text-2xl font-semibold leading-tight">
        You are a <span className="text-primary font-semibold">{personality.title}</span>.
      </p>

      <p className="text-sm text-muted-foreground mt-2 max-w-3xl">
        {personality.description}
      </p>
    </div>

    {/* 📊 KEY STATS */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

      <div className="glass-card p-4 rounded-xl text-center border border-red-500/15 bg-red-500/5">
        <p className="text-xs text-muted-foreground">Fatigue</p>
        <p className="text-2xl font-bold text-red-400">{fatigue.fatigue_score}%</p>
      </div>

      <div className="glass-card p-4 rounded-xl text-center border border-emerald-500/15 bg-emerald-500/5">
        <p className="text-xs text-muted-foreground">Productivity</p>
        <p className="text-2xl font-bold text-emerald-400">{productivity.productivity_score}%</p>
      </div>

      <div className="glass-card p-4 rounded-xl text-center border border-cyan-500/15 bg-cyan-500/5">
        <p className="text-xs text-muted-foreground">Focus</p>
        <p className="text-2xl font-bold text-cyan-400">{focusScore}%</p>
      </div>

      <div className="glass-card p-4 rounded-xl text-center border border-amber-500/15 bg-amber-500/5">
        <p className="text-xs text-muted-foreground">Risk</p>
        <p className={`text-2xl font-bold ${risk.colorClass}`}>{risk.label}</p>
      </div>

    </div>

    {/* ⚠️ MAIN ISSUE */}
    <div className="glass-card p-6 rounded-2xl border border-border/60 bg-secondary/20">
      <p className="text-sm text-muted-foreground mb-2">Main Issue</p>

      <p className="text-2xl font-semibold text-red-400">
        {biggestIssue.label}
      </p>

      <p className="text-sm text-muted-foreground mt-2">
        This is affecting your performance the most. Estimated impact: {biggestIssue.value}%
      </p>
    </div>

    {/* 💡 WHAT YOU SHOULD DO */}
    <div className="glass-card p-6 rounded-2xl border border-border/60 bg-secondary/10">
      <p className="text-sm text-muted-foreground mb-3">What you can do</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/5 px-3 py-3">
          Try to work during <span className="text-emerald-400 font-medium">{bestTime}</span>
        </div>
        <div className="rounded-lg border border-amber-500/15 bg-amber-500/5 px-3 py-3">
          You can improve by <span className="text-amber-400 font-medium">{improvement}%</span>
        </div>
      </div>
    </div>

    {/* 🤖 SIMPLE EXPLANATION */}
    <div className="glass-card p-6 rounded-2xl border border-border/60 bg-secondary/10">
      <p className="text-sm font-bold text-foreground mb-3">Explanation</p>

      <div className="flex items-start gap-2 max-w-4xl">
        <span className="mt-2 h-2 w-2 rounded-full bg-muted-foreground/50 shrink-0" />
        <p className="text-sm text-muted-foreground leading-7 whitespace-pre-line">
          {explanation.trim()}
        </p>
      </div>
    </div>

{/* 🔥 IMPACT HIGHLIGHT (BETTER DESIGN) */}

<div className="glass-card p-6 rounded-2xl border border-red-500/15 bg-red-500/5">

  <p className="text-sm font-bold text-foreground mb-2">
     Impact on your day
  </p>

  <p className="text-2xl font-semibold leading-tight">
    You are losing <span className="text-red-400 font-bold">
      {formatHours(productivity.productivity_loss_hours)}
    </span> every day
  </p>

  <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
    If you improve your habits, you can recover up to{" "}
    <span className="text-green-400 font-medium">
      {formatHours(recoverableHours)}
    </span>
  </p>

</div>

    {/* 📌 PREDICTION DRIVERS */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="glass-card p-6 rounded-2xl">
        <p className="text-sm font-bold text-foreground mb-2">Prediction Drivers</p>
        {fatigueFactors.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {fatigueFactors.map((factor) => (
              <li key={factor} className="flex items-start gap-2">
                <span className="mt-1 h-2.5 w-2.5 rounded-full bg-violet-500" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No fatigue drivers were detected.</p>
        )}
      </div>

      <div className="glass-card p-6 rounded-2xl">
        <p className="text-sm font-bold text-foreground mb-2">Smart Action Plan</p>
        <ul className="space-y-3 text-sm">
          {suggestedActions.map((action) => (
            <li key={action} className="flex items-start gap-2">
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-green-400" />
              <span>{action}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>

  </div>
);
}