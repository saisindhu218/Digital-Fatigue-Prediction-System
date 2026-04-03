import { useUsageData } from '@/hooks/useUsageData';
import { motion } from 'framer-motion';
import { Brain, Sparkles, AlertTriangle, Target } from 'lucide-react';

/* -------- HELPERS -------- */

function formatHours(hours: number) {
  const totalMinutes = Math.round(hours * 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

/* -------- MAIN -------- */

export default function PredictionsPage() {
  const { data } = useUsageData();
  if (!data) return null;

  const { fatigue, productivity } = data.predictions;

  /* -------- AI PERSONALITY -------- */

  let personality = "Balanced User";
  let description = "You maintain a healthy balance between focus and breaks.";

  if (fatigue.fatigue_score > 60) {
    personality = "Overworked User";
    description = "You tend to work continuously without enough breaks, leading to fatigue.";
  } else if (productivity.productivity_score < 60) {
    personality = "Distracted User";
    description = "Frequent app switching and distractions are reducing your efficiency.";
  } else if (productivity.productivity_score > 80) {
    personality = "Highly Focused";
    description = "You are maintaining strong focus and consistent productivity.";
  }

  /* -------- RISK LEVEL -------- */

  let risk = "Low";
  let riskColor = "text-green-400";

  if (fatigue.fatigue_score > 60) {
    risk = "High";
    riskColor = "text-red-400";
  } else if (productivity.productivity_score < 70) {
    risk = "Moderate";
    riskColor = "text-yellow-400";
  }

  /* -------- FOCUS SCORE -------- */

  const focusScore = Math.round(
    (productivity.productivity_score - fatigue.fatigue_score / 2)
  );

  /* -------- AI EXPLANATION -------- */

  const explanation = `
Based on your recent usage patterns, your productivity is ${productivity.productivity_score}% 
while fatigue is ${fatigue.fatigue_score}%. 

This indicates that your efficiency is ${
    productivity.productivity_score > 75 ? "good" : "affected"
  }, but ${
    fatigue.fatigue_score > 50 ? "fatigue is increasing" : "fatigue is under control"
  }.
`;

/* -------- AI ACTIONABLE INSIGHTS -------- */

// biggest issue
let biggestIssue = "Balanced usage";
let issueValue = 0;

if (fatigue.fatigue_score > productivity.productivity_score) {
  biggestIssue = "High Fatigue";
  issueValue = fatigue.fatigue_score;
} else {
  biggestIssue = "Low Productivity";
  issueValue = 100 - productivity.productivity_score;
}

// best working time (simple logic)
const bestTime =
  fatigue.fatigue_score < 40
    ? "Morning (9AM - 12PM)"
    : "Evening (6PM - 9PM)";

// improvement potential
const improvement = Math.round(
  (100 - productivity.productivity_score) * 0.6
);

// recoverable time
const recoverableHours = productivity.productivity_loss_hours * 0.6;

return (
  <div className="space-y-6 animate-fade-in">

    {/* HEADER */}
    <div>
      <h1 className="text-2xl font-bold">AI Predictions</h1>
      <p className="text-sm text-muted-foreground">
        Simple insights from your recent activity
      </p>
    </div>

    {/* 🧠 SIMPLE SUMMARY */}
    <div className="glass-card p-6 rounded-2xl">
      <p className="text-sm text-muted-foreground mb-2">Summary</p>

      <p className="text-lg font-medium">
        You are a <span className="text-primary font-semibold">{personality}</span>.
      </p>

      <p className="text-sm text-muted-foreground mt-1">
        {description}
      </p>
    </div>

    {/* 📊 KEY STATS */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

      <div className="glass-card p-4 rounded-xl text-center">
        <p className="text-xs text-muted-foreground">Fatigue</p>
        <p className="text-lg font-bold">{fatigue.fatigue_score}%</p>
      </div>

      <div className="glass-card p-4 rounded-xl text-center">
        <p className="text-xs text-muted-foreground">Productivity</p>
        <p className="text-lg font-bold">{productivity.productivity_score}%</p>
      </div>

      <div className="glass-card p-4 rounded-xl text-center">
        <p className="text-xs text-muted-foreground">Focus</p>
        <p className="text-lg font-bold">{focusScore}%</p>
      </div>

      <div className="glass-card p-4 rounded-xl text-center">
        <p className="text-xs text-muted-foreground">Risk</p>
        <p className={`text-lg font-bold ${riskColor}`}>{risk}</p>
      </div>

    </div>

    {/* ⚠️ MAIN ISSUE */}
    <div className="glass-card p-6 rounded-2xl">
      <p className="text-sm text-muted-foreground mb-1">Main Issue</p>

      <p className="text-lg font-semibold text-red-400">
        {biggestIssue}
      </p>

      <p className="text-xs text-muted-foreground mt-2">
        This is affecting your performance the most.
      </p>
    </div>

    {/* 💡 WHAT YOU SHOULD DO */}
    <div className="glass-card p-6 rounded-2xl">
      <p className="text-sm text-muted-foreground mb-3">What you can do</p>

      <div className="space-y-2 text-sm">
        <div>• Try to work during <span className="text-green-400 font-medium">{bestTime}</span></div>
        <div>• You can improve by <span className="text-yellow-400 font-medium">{improvement}%</span></div>
      </div>
    </div>

    {/* 🤖 SIMPLE EXPLANATION */}
    <div className="glass-card p-6 rounded-2xl">
      <p className="text-sm text-muted-foreground mb-2">Explanation</p>

      <p className="text-sm text-muted-foreground leading-relaxed">
        Your productivity is {productivity.productivity_score}% while fatigue is {fatigue.fatigue_score}%.
        This means your performance is {productivity.productivity_score > 75 ? "good" : "affected"}.
      </p>
    </div>

{/* 🔥 IMPACT HIGHLIGHT (BETTER DESIGN) */}

<div className="glass-card p-6 rounded-2xl">

  <p className="text-sm text-red-400 mb-2 font-medium">
     Impact on your day
  </p>

  <p className="text-xl font-semibold">
    You are losing <span className="text-red-400 font-bold">
      {formatHours(productivity.productivity_loss_hours)}
    </span> every day
  </p>

  <p className="text-sm text-muted-foreground mt-2">
    If you improve your habits, you can recover up to{" "}
    <span className="text-green-400 font-medium">
      {formatHours(recoverableHours)}
    </span>
  </p>

</div>

  </div>
);
}