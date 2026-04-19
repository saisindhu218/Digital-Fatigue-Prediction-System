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

type Driver = {
  title: string;
  impact: 'High' | 'Medium' | 'Low';
  reason: string;
};

type ActionStep = {
  step: string;
  reason: string;
};

function buildPredictionDrivers(
  fatigueScore: number,
  productivityScore: number,
  fatigueFactors: string[],
  breakdown?: Record<string, number>
): Driver[] {
  const drivers: Driver[] = [];

  if (fatigueScore >= 65) {
    drivers.push({
      title: 'Fatigue load is high',
      impact: 'High',
      reason: `Current fatigue score is ${fatigueScore}%, which can reduce sustained focus.`,
    });
  }

  if (productivityScore <= 60) {
    drivers.push({
      title: 'Productivity level is below target',
      impact: 'High',
      reason: `Productivity is ${productivityScore}%, indicating avoidable efficiency loss.`,
    });
  }

  const contextSwitching = breakdown?.['Context Switching'] ?? 0;
  const distractions = breakdown?.['Distractions'] ?? 0;

  if (contextSwitching > distractions && contextSwitching > 0) {
    drivers.push({
      title: 'Frequent context switching',
      impact: 'Medium',
      reason: `Switching cost is one of the main contributors to lost productive time (${contextSwitching.toFixed(2)} hr).`,
    });
  }

  if (distractions >= contextSwitching && distractions > 0) {
    drivers.push({
      title: 'Distraction-heavy usage',
      impact: 'Medium',
      reason: `Distraction time is materially affecting output (${distractions.toFixed(2)} hr).`,
    });
  }

  if (fatigueFactors.length > 0) {
    drivers.push({
      title: 'Model-detected fatigue signals',
      impact: 'Medium',
      reason: fatigueFactors.slice(0, 2).join(' and '),
    });
  }

  if (drivers.length === 0) {
    drivers.push({
      title: 'No dominant negative driver',
      impact: 'Low',
      reason: 'Your current usage pattern looks balanced with no strong risk spike.',
    });
  }

  return drivers.slice(0, 3);
}

function buildSmartActionPlan(
  fatigueScore: number,
  productivityScore: number,
  riskLabel: string,
  bestTime: string
): ActionStep[] {
  const steps: ActionStep[] = [];

  if (fatigueScore >= 65) {
    steps.push({
      step: 'Run a 50-10 focus cycle for the next two hours (50 min work, 10 min break).',
      reason: 'This directly reduces fatigue accumulation while keeping output steady.',
    });
  }

  if (productivityScore <= 65) {
    steps.push({
      step: 'Work in single-task mode and mute non-essential notifications for the next session.',
      reason: 'Lower interruptions usually improves productivity in the same day.',
    });
  }

  steps.push({
    step: `Schedule your highest-priority task during ${bestTime}.`,
    reason: 'This aligns difficult work with your better performance window.',
  });

  if (riskLabel === 'High') {
    steps.push({
      step: 'Take a 15-minute reset now (walk, stretch, water) before the next work block.',
      reason: 'When risk is high, immediate reset prevents compounding fatigue-driven loss.',
    });
  }

  if (steps.length < 3) {
    steps.push({
      step: 'Do a 2-minute end-of-block review: done, pending, next first task.',
      reason: 'Quick review improves continuity and reduces re-start friction.',
    });
  }

  return steps.slice(0, 3);
}

function buildExplanationLines(
  fatigueScore: number,
  productivityScore: number,
  riskLabel: string,
  biggestIssueLabel: string,
  recoverableHours: number
) {
  const efficiencyState = productivityScore >= 75 ? 'good' : 'currently constrained';
  const fatigueState = fatigueScore <= 45 ? 'well-controlled' : 'elevated';

  return [
    `Your current productivity is ${productivityScore}% and fatigue is ${fatigueScore}%.`,
    `Overall efficiency is ${efficiencyState}, while fatigue is ${fatigueState}.`,
    `Primary driver to address now: ${biggestIssueLabel}.`,
    `Current risk level is ${riskLabel.toLowerCase()}, and you can recover about ${formatHours(recoverableHours)} with consistent habit correction.`,
  ];
}

function getImpactBadgeClass(impact: Driver['impact']) {
  if (impact === 'High') return 'text-red-400 bg-red-500/10';
  if (impact === 'Medium') return 'text-yellow-400 bg-yellow-500/10';
  return 'text-green-400 bg-green-500/10';
}

function getBiggestIssue(fatigueScore: number, productivityScore: number) {
  if (fatigueScore > productivityScore) {
    return { label: 'High Fatigue', value: fatigueScore };
  }

  return { label: 'Low Productivity', value: 100 - productivityScore };
}

function getRecentTrendDirection(
  metric: 'fatigue' | 'productivity',
  trend: Array<{ day: string; score: number }>
) {
  const validTrend = trend.filter(
    (point) => typeof point.score === 'number' && Number.isFinite(point.score)
  );

  if (validTrend.length < 4) {
    return {
      title: 'Not enough trend data yet',
      detail: 'Collecting more activity to detect direction.',
      toneClass: 'text-muted-foreground',
    };
  }

  const scores = validTrend.map((point) => point.score);
  const windowSize = Math.min(3, Math.floor(scores.length / 2));

  if (windowSize < 2) {
    return {
      title: 'Not enough trend data yet',
      detail: 'Collecting more activity to detect direction.',
      toneClass: 'text-muted-foreground',
    };
  }

  const previousWindow = scores.slice(-2 * windowSize, -windowSize);
  const recentWindow = scores.slice(-windowSize);

  const previousAvg = previousWindow.reduce((sum, value) => sum + value, 0) / previousWindow.length;
  const recentAvg = recentWindow.reduce((sum, value) => sum + value, 0) / recentWindow.length;
  const delta = Math.round((recentAvg - previousAvg) * 10) / 10;

  if (Math.abs(delta) < 2) {
    return {
      title: 'Mostly stable',
      detail: `Recent average changed by ${delta > 0 ? '+' : ''}${delta} percentage points.`,
      toneClass: 'text-yellow-400',
    };
  }

  if (metric === 'fatigue') {
    return delta < 0
      ? {
          title: 'Improving',
          detail: `Fatigue is down by ${Math.abs(delta)} percentage points vs earlier period (good sign).`,
          toneClass: 'text-green-400',
        }
      : {
          title: 'Needs attention',
          detail: `Fatigue is up by ${Math.abs(delta)} percentage points vs earlier period.`,
          toneClass: 'text-red-400',
        };
  }

  return delta > 0
    ? {
        title: 'Improving',
        detail: `Productivity is up by ${Math.abs(delta)} percentage points vs earlier period.`,
        toneClass: 'text-green-400',
      }
    : {
        title: 'Needs attention',
        detail: `Productivity is down by ${Math.abs(delta)} percentage points vs earlier period.`,
        toneClass: 'text-red-400',
      };
}

function getCurrentRiskZone(fatigueScore: number, productivityScore: number) {
  if (fatigueScore >= 70 || productivityScore <= 45) {
    return {
      label: 'High Risk Zone',
      detail: 'Take a short reset break now before continuing focused work.',
      badgeClass: 'text-red-400 border-red-500/40 bg-red-500/10',
    };
  }

  if (fatigueScore >= 50 || productivityScore <= 65) {
    return {
      label: 'Moderate Risk Zone',
      detail: 'Continue, but add a brief break in the next work block.',
      badgeClass: 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10',
    };
  }

  return {
    label: 'Low Risk Zone',
    detail: 'Current state is healthy. Keep the same rhythm and hydration.',
    badgeClass: 'text-green-400 border-green-500/40 bg-green-500/10',
  };
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

  const fatigueTrend = data.trends?.fatigueTrend ?? [];
  const productivityTrend = data.trends?.productivityTrend ?? [];

  const fatigueDirection = getRecentTrendDirection('fatigue', fatigueTrend);
  const productivityDirection = getRecentTrendDirection('productivity', productivityTrend);
  const currentRiskZone = getCurrentRiskZone(
    fatigue.fatigue_score,
    productivity.productivity_score
  );
  const predictionDrivers = buildPredictionDrivers(
    fatigue.fatigue_score,
    productivity.productivity_score,
    fatigueFactors,
    productivity.breakdown
  );
  const smartActionPlan = buildSmartActionPlan(
    fatigue.fatigue_score,
    productivity.productivity_score,
    risk.label,
    bestTime
  );
  const explanationLines = buildExplanationLines(
    fatigue.fatigue_score,
    productivity.productivity_score,
    risk.label,
    biggestIssue.label,
    recoverableHours
  );

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

    {/* 📈 EASY-TO-UNDERSTAND LIVE INSIGHTS */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="glass-card p-5 rounded-2xl border border-border/60 bg-secondary/10">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Fatigue Trend</p>
        <p className={`text-xl font-semibold ${fatigueDirection.toneClass}`}>{fatigueDirection.title}</p>
        <p className="text-xs text-muted-foreground mt-1">Measured as fatigue score (%) change from previous point</p>
        <p className="text-sm text-muted-foreground mt-2">{fatigueDirection.detail}</p>
      </div>

      <div className="glass-card p-5 rounded-2xl border border-border/60 bg-secondary/10">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Productivity Trend</p>
        <p className={`text-xl font-semibold ${productivityDirection.toneClass}`}>{productivityDirection.title}</p>
        <p className="text-xs text-muted-foreground mt-1">Measured as productivity score (%) change from previous point</p>
        <p className="text-sm text-muted-foreground mt-2">{productivityDirection.detail}</p>
      </div>

      <div className="glass-card p-5 rounded-2xl border border-border/60 bg-secondary/10">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Current Risk Zone</p>
        <span className={`inline-flex rounded-full border px-3 py-1 text-sm font-medium ${currentRiskZone.badgeClass}`}>
          {currentRiskZone.label}
        </span>
        <p className="text-sm text-muted-foreground mt-3">{currentRiskZone.detail}</p>
        <p className="text-sm mt-2">
          <span className="text-foreground font-medium">Next best action:</span>{' '}
          <span className="text-muted-foreground">{smartActionPlan[0]?.step}</span>
        </p>
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

    {/* 🤖 EXPLANATION INSIGHT CARD */}
    <div className="glass-card p-6 rounded-2xl border border-border/60 bg-secondary/10 shadow-sm">
      <div className="flex items-center justify-between gap-3 mb-4">
        <p className="text-sm font-bold text-foreground">Explanation</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4 text-sm">
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-2">
          <p className="text-xs text-muted-foreground">Primary issue</p>
          <p className="font-medium text-cyan-300 mt-0.5">{biggestIssue.label}</p>
        </div>
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2">
          <p className="text-xs text-muted-foreground">Current risk</p>
          <p className="font-medium text-amber-300 mt-0.5">{risk.label}</p>
        </div>
      </div>

      <div className="space-y-2 text-sm text-muted-foreground leading-7 max-w-4xl">
        {explanationLines.map((line) => (
          <div key={line} className="flex items-start gap-2">
            <span className="mt-2 h-1.5 w-1.5 rounded-full bg-primary/70 shrink-0" />
            <p>{line}</p>
          </div>
        ))}
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
        <div className="space-y-3 text-sm">
          {predictionDrivers.map((driver) => (
            <div key={driver.title} className="rounded-lg border border-border/60 p-3 bg-secondary/10">
              <div className="flex items-center justify-between gap-2">
                <p className="font-medium text-foreground">{driver.title}</p>
                <span className={`text-xs px-2 py-0.5 rounded-full ${getImpactBadgeClass(driver.impact)}`}>
                  {driver.impact} impact
                </span>
              </div>
              <p className="text-muted-foreground mt-1">{driver.reason}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card p-6 rounded-2xl">
        <p className="text-sm font-bold text-foreground mb-2">Smart Action Plan</p>
        <div className="space-y-3 text-sm">
          {smartActionPlan.map((action, index) => (
            <div key={action.step} className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
              <p className="font-medium text-foreground">Step {index + 1}: {action.step}</p>
              <p className="text-muted-foreground mt-1">Why: {action.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </div>

  </div>
);
}