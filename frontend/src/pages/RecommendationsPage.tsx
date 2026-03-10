import { motion } from 'framer-motion';
import { Coffee, Moon, Repeat, Target, Smartphone, Eye, Timer, Brain } from 'lucide-react';

const recommendations = [
  {
    icon: Coffee, title: 'Take Regular Breaks',
    description: 'Follow the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds. Take a 5-minute break every 45 minutes.',
    priority: 'high', impact: 'Reduces fatigue by ~25%',
  },
  {
    icon: Moon, title: 'Reduce Late-Night Usage',
    description: 'Your night usage ratio is high. Avoid screens 1 hour before bed to improve sleep quality and reduce morning fatigue.',
    priority: 'high', impact: 'Improves recovery by ~30%',
  },
  {
    icon: Repeat, title: 'Reduce Context Switching',
    description: 'You average 18 app switches per session. Batch similar tasks together and use focus blocks to minimize switching costs.',
    priority: 'medium', impact: 'Saves ~0.7 hours/day',
  },
  {
    icon: Target, title: 'Improve Focus Sessions',
    description: 'Schedule 90-minute deep work blocks with no notifications. Your peak focus hours are 10 AM - 12 PM.',
    priority: 'medium', impact: 'Boosts productivity by ~20%',
  },
  {
    icon: Smartphone, title: 'Limit Social Media',
    description: 'Social media accounts for 1.2 hours of productivity loss daily. Set app timers and batch check times.',
    priority: 'medium', impact: 'Saves ~1.2 hours/day',
  },
  {
    icon: Eye, title: 'Manage Notifications',
    description: 'You receive 100+ notifications daily. Disable non-essential notifications and check messages at set intervals.',
    priority: 'low', impact: 'Reduces distractions by ~40%',
  },
  {
    icon: Timer, title: 'Optimize Session Length',
    description: 'Your average session is 25 minutes. Aim for 45-90 minute focused sessions with clear goals.',
    priority: 'low', impact: 'Increases efficiency by ~15%',
  },
  {
    icon: Brain, title: 'Monitor Cognitive Load',
    description: 'Your cognitive load score is 65%. Balance demanding tasks with lighter activities throughout the day.',
    priority: 'low', impact: 'Reduces mental fatigue by ~20%',
  },
];

function getPriorityStyles(priority: string) {
  switch (priority) {
    case 'high': return 'border-l-destructive bg-destructive/5';
    case 'medium': return 'border-l-warning bg-warning/5';
    default: return 'border-l-info bg-info/5';
  }
}

function getPriorityBadge(priority: string) {
  switch (priority) {
    case 'high': return 'bg-destructive/15 text-destructive';
    case 'medium': return 'bg-warning/15 text-warning';
    default: return 'bg-info/15 text-info';
  }
}

export default function RecommendationsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Recommendations</h1>
        <p className="text-sm text-muted-foreground mt-1">AI-powered suggestions to improve your digital wellbeing</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.map((rec, i) => (
          <motion.div
            key={rec.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className={`glass-card rounded-xl p-5 border-l-4 ${getPriorityStyles(rec.priority)}`}
          >
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-secondary shrink-0">
                <rec.icon className="w-4 h-4 text-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <h3 className="font-semibold text-sm">{rec.title}</h3>
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wide ${getPriorityBadge(rec.priority)}`}>
                    {rec.priority}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed mb-3">{rec.description}</p>
                <div className="text-xs font-medium text-primary">{rec.impact}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
