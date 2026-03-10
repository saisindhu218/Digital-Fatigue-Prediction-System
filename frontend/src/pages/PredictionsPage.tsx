import { useUsageData } from '@/hooks/useUsageData';
import { ChartCard } from '@/components/ChartCard';
import { motion } from 'framer-motion';
import { Brain, TrendingDown, AlertTriangle, CheckCircle, Info } from 'lucide-react';

function getLevelColor(level: string) {
  switch (level.toLowerCase()) {
    case 'low': return 'text-success';
    case 'medium': return 'text-warning';
    case 'high': return 'text-destructive';
    default: return 'text-muted-foreground';
  }
}

function getScoreColor(score: number) {
  if (score >= 80) return 'hsl(145,65%,48%)';
  if (score >= 60) return 'hsl(38,92%,55%)';
  return 'hsl(0,72%,55%)';
}

export default function PredictionsPage() {
  const { data } = useUsageData();
  if (!data) return null;
  const { fatigue, productivity } = data.predictions;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Predictions</h1>
        <p className="text-sm text-muted-foreground mt-1">Machine learning insights on your digital behavior</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fatigue Card */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-primary/15">
              <Brain className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold">Fatigue Prediction</h2>
              <p className="text-xs text-muted-foreground">ML confidence: {fatigue.confidence}%</p>
            </div>
          </div>

          {/* Score ring */}
          <div className="flex items-center justify-center mb-6">
            <div className="relative w-36 h-36">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(225,12%,16%)" strokeWidth="6" />
                <circle cx="50" cy="50" r="42" fill="none" stroke={getScoreColor(100 - fatigue.fatigue_score)} strokeWidth="6" strokeLinecap="round" strokeDasharray={`${fatigue.fatigue_score * 2.64} 264`} />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold">{fatigue.fatigue_score}%</span>
                <span className={`text-xs font-medium ${getLevelColor(fatigue.fatigue_level)}`}>{fatigue.fatigue_level}</span>
              </div>
            </div>
          </div>

          {/* Factors */}
          {fatigue.factors && (
            <div>
              <p className="text-xs text-muted-foreground mb-3 font-medium">Key Contributing Factors</p>
              <div className="space-y-2">
                {fatigue.factors.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm p-2.5 rounded-lg bg-secondary/50">
                    <AlertTriangle className="w-3.5 h-3.5 text-warning shrink-0" />
                    <span className="text-muted-foreground">{f}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* Productivity Card */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-info/15">
              <TrendingDown className="w-5 h-5 text-info" />
            </div>
            <div>
              <h2 className="font-semibold">Productivity Prediction</h2>
              <p className="text-xs text-muted-foreground">Daily productivity analysis</p>
            </div>
          </div>

          <div className="flex items-center justify-center mb-6">
            <div className="relative w-36 h-36">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(225,12%,16%)" strokeWidth="6" />
                <circle cx="50" cy="50" r="42" fill="none" stroke={getScoreColor(productivity.productivity_score)} strokeWidth="6" strokeLinecap="round" strokeDasharray={`${productivity.productivity_score * 2.64} 264`} />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold">{productivity.productivity_score}%</span>
                <span className="text-xs text-muted-foreground">Score</span>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-destructive/10 mb-5 flex items-start gap-3">
            <Info className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium">Productivity Loss</p>
              <p className="text-2xl font-bold mt-0.5">{productivity.productivity_loss_hours} hours/day</p>
            </div>
          </div>

          {productivity.breakdown && (
            <div>
              <p className="text-xs text-muted-foreground mb-3 font-medium">Loss Breakdown</p>
              <div className="space-y-2">
                {Object.entries(productivity.breakdown).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between text-sm p-2.5 rounded-lg bg-secondary/50">
                    <span className="text-muted-foreground">{key}</span>
                    <span className="font-medium">{val}h</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Summary */}
      <ChartCard title="Prediction Summary" subtitle="AI model assessment">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-secondary/50 text-center">
            <p className="text-xs text-muted-foreground mb-1">Model Confidence</p>
            <p className="text-2xl font-bold">{fatigue.confidence}%</p>
            <div className="flex items-center justify-center gap-1 mt-1">
              <CheckCircle className="w-3 h-3 text-success" />
              <span className="text-xs text-success">Reliable</span>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-secondary/50 text-center">
            <p className="text-xs text-muted-foreground mb-1">Risk Level</p>
            <p className={`text-2xl font-bold ${getLevelColor(fatigue.fatigue_level)}`}>{fatigue.fatigue_level}</p>
            <p className="text-xs text-muted-foreground mt-1">Based on behavior patterns</p>
          </div>
          <div className="p-4 rounded-xl bg-secondary/50 text-center">
            <p className="text-xs text-muted-foreground mb-1">Daily Impact</p>
            <p className="text-2xl font-bold">{productivity.productivity_loss_hours}h</p>
            <p className="text-xs text-muted-foreground mt-1">Estimated time lost</p>
          </div>
        </div>
      </ChartCard>
    </div>
  );
}
