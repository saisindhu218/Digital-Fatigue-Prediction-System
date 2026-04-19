import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useUsageData } from '@/hooks/useUsageData';
import { api } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { UserCircle2, ShieldCheck, Palette, Save, Bell, Activity, Clock3, Sparkles, Loader2 } from 'lucide-react';

function formatHours(hours: number) {
  const totalMinutes = Math.round(hours * 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;

  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} hr`;
  return `${h} hr ${m} min`;
}

function getInitials(nameOrEmail: string) {
  const parts = nameOrEmail.trim().split(' ').filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return nameOrEmail.slice(0, 2).toUpperCase();
}

export default function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const { theme } = useTheme();
  const { data: usageData } = useUsageData();

  const initialName = user?.name || user?.email?.split('@')[0] || '';
  const [displayName, setDisplayName] = useState(initialName);
  const [savedMessage, setSavedMessage] = useState('');
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  // Preferences
  const [breakAlerts, setBreakAlerts] = useState(true);
  const [fatigueAlerts, setFatigueAlerts] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(false);

  // Goals
  const [targetFocusScore, setTargetFocusScore] = useState(80);
  const [maxFatigueThreshold, setMaxFatigueThreshold] = useState(75);
  const [dailyScreenLimitHours, setDailyScreenLimitHours] = useState(8.0);
  const [preferredWorkSlot, setPreferredWorkSlot] = useState('09:00-17:00');

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [apiError, setApiError] = useState('');

  // Fetch preferences and goals on mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [prefs, goals] = await Promise.all([
          api.getPreferences(),
          api.getGoals(),
        ]);

        setBreakAlerts(prefs.break_alerts);
        setFatigueAlerts(prefs.fatigue_alerts);
        setWeeklyDigest(prefs.weekly_digest);

        setTargetFocusScore(goals.target_focus_score);
        setMaxFatigueThreshold(goals.max_fatigue_threshold);
        setDailyScreenLimitHours(goals.daily_screen_limit_hours);
        setPreferredWorkSlot(goals.preferred_work_slot);

        console.log('✅ Preferences and goals loaded from backend');
      } catch (error) {
        console.error('Failed to load preferences/goals:', error);
        setApiError('Failed to sync settings from server');
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  const handleSaveSettings = async () => {
    if (!user) return;

    setIsSaving(true);
    setApiError('');

    try {
      await Promise.all([
        api.updatePreferences({
          break_alerts: breakAlerts,
          fatigue_alerts: fatigueAlerts,
          weekly_digest: weeklyDigest,
        }),
        api.updateGoals({
          target_focus_score: targetFocusScore,
          max_fatigue_threshold: maxFatigueThreshold,
          daily_screen_limit_hours: dailyScreenLimitHours,
          preferred_work_slot: preferredWorkSlot,
        }),
      ]);

      setSavedMessage('Settings saved successfully.');
      setTimeout(() => setSavedMessage(''), 2000);
    } catch (error) {
      console.error('Failed to save profile settings:', error);
      setApiError('Failed to save profile settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSave = () => {
    const trimmed = displayName.trim();
    if (!trimmed) return;

    updateProfile({ name: trimmed });
    setSavedMessage('Profile updated successfully.');
    setIsEditingProfile(false);
    setTimeout(() => setSavedMessage(''), 2000);
  };

  const handleCancelEdit = () => {
    setDisplayName(initialName);
    setIsEditingProfile(false);
  };

  const accountType = 'Standard User';
  const securityStatus = 'Protected with authenticated session';

  const summary = usageData?.summary;
  const predictions = usageData?.predictions;
  const focusScore = summary?.focus_score ?? 0;
  const fatigueScore = predictions?.fatigue?.fatigue_score ?? 0;
  const productivityScore = predictions?.productivity?.productivity_score ?? 0;

  let performanceLabel = 'Needs attention';
  if (productivityScore >= 75 && fatigueScore <= 50) {
    performanceLabel = 'Strong';
  } else if (productivityScore >= 60) {
    performanceLabel = 'Moderate';
  }

  const profileCompletion = (() => {
    let score = 40;
    if (displayName.trim().length >= 2) score += 20;
    if (user?.email) score += 20;
    if (breakAlerts || fatigueAlerts || weeklyDigest) score += 20;
    return Math.min(100, score);
  })();

  if (!user) return null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your account, preferences, and personal productivity profile
        </p>
      </div>

      {apiError && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-400">
          {apiError}
        </div>
      )}

      <div className="glass-card p-6 rounded-xl border border-primary/20 bg-primary/5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-primary/15 border border-primary/25 flex items-center justify-center">
              <span className="text-base font-semibold text-primary">{getInitials(displayName || user?.email || 'U')}</span>
            </div>
            <div>
              <p className="text-lg font-semibold">{displayName || 'User'}</p>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{accountType}</Badge>
            <Badge variant="outline">Theme: {theme}</Badge>
            <Badge variant="outline">Profile completion: {profileCompletion}%</Badge>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="glass-card p-6 rounded-xl">
          <div className="flex items-center gap-3 mb-5">
            <UserCircle2 className="w-5 h-5 text-primary" />
            <p className="font-semibold">Account Information</p>
          </div>

          <div className="flex items-center gap-4 mb-5">
            <div className="h-14 w-14 rounded-full bg-primary/15 border border-primary/25 flex items-center justify-center">
              <span className="text-sm font-semibold text-primary">{getInitials(displayName || user?.email || 'U')}</span>
            </div>
            <div>
              <p className="font-medium">{displayName || 'User'}</p>
              <p className="text-xs text-muted-foreground">{accountType}</p>
            </div>
          </div>

          {isEditingProfile ? (
            <div className="space-y-4">
              <div>
                <label htmlFor="profile-display-name" className="text-xs text-muted-foreground">Display Name</label>
                <input
                  id="profile-display-name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Enter display name"
                />
              </div>

              <div>
                <label htmlFor="profile-email" className="text-xs text-muted-foreground">Email</label>
                <input
                  id="profile-email"
                  value={user.email}
                  disabled
                  className="mt-1 w-full rounded-md border border-input bg-muted/60 px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
                />
              </div>

              <div>
                <label htmlFor="profile-user-id" className="text-xs text-muted-foreground">User ID</label>
                <input
                  id="profile-user-id"
                  value={user.id}
                  disabled
                  className="mt-1 w-full rounded-md border border-input bg-muted/60 px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleSave}
                  className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm font-medium hover:opacity-90"
                >
                  <Save className="w-4 h-4" />
                  Save Profile
                </button>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm font-medium hover:bg-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground">Display Name</p>
                <p className="mt-1 text-sm font-medium">{displayName || 'User'}</p>
              </div>

              <div>
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="mt-1 text-sm font-medium">{user.email}</p>
              </div>

              <div>
                <p className="text-xs text-muted-foreground">User ID</p>
                <p className="mt-1 text-sm font-medium break-all text-xs">{user.id}</p>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditingProfile(true)}
                  className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm font-medium hover:opacity-90"
                >
                  Edit Profile
                </button>
                {savedMessage && <span className="text-sm text-green-400">{savedMessage}</span>}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4 xl:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-card p-5 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-primary" />
                <p className="text-sm font-semibold">Activity Snapshot</p>
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-muted-foreground">
                  Screen time today: <span className="text-foreground font-medium">{formatHours(summary?.total_screen_time ?? 0)}</span>
                </p>
                <p className="text-muted-foreground">
                  Focus score: <span className="text-foreground font-medium">{focusScore}%</span>
                </p>
                <p className="text-muted-foreground">
                  Performance state: <span className="text-foreground font-medium">{performanceLabel}</span>
                </p>
              </div>
            </div>

            <div className="glass-card p-5 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="w-4 h-4 text-green-400" />
                <p className="text-sm font-semibold">Security</p>
              </div>
              <p className="text-sm text-muted-foreground">{securityStatus}</p>
              <p className="text-xs text-muted-foreground mt-2">Session is active on this browser only.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-card p-5 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Bell className="w-4 h-4 text-primary" />
                <p className="text-sm font-semibold">Notification Preferences</p>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Control which notifications you receive
              </p>
              <div className="mt-3 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground flex items-center gap-2">
                    <Bell className="w-3.5 h-3.5" />
                    Break reminders
                  </div>
                  <Switch
                    checked={breakAlerts}
                    onCheckedChange={setBreakAlerts}
                    disabled={isLoading}
                  />
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground flex items-center gap-2">
                    <Clock3 className="w-3.5 h-3.5" />
                    Fatigue alerts
                  </div>
                  <Switch
                    checked={fatigueAlerts}
                    onCheckedChange={setFatigueAlerts}
                    disabled={isLoading}
                  />
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5" />
                    Weekly digest
                  </div>
                  <Switch
                    checked={weeklyDigest}
                    onCheckedChange={setWeeklyDigest}
                    disabled={isLoading}
                  />
                </div>

                <div className="pt-2 flex items-center justify-between gap-3">
                  <button
                    type="button"
                    onClick={handleSaveSettings}
                    disabled={isSaving || isLoading}
                    className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50"
                  >
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Save Settings
                  </button>

                  {savedMessage && (
                    <span className="text-xs text-green-400">{savedMessage}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="glass-card p-5 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <p className="text-sm font-semibold">Productivity Goals</p>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Set targets to personalize recommendations
              </p>

              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                    <span>Target focus score</span>
                    <span className="text-foreground font-medium">{targetFocusScore}%</span>
                  </div>
                  <input
                    type="range"
                    min={50}
                    max={95}
                    step={1}
                    value={targetFocusScore}
                    onChange={(e) => setTargetFocusScore(Number(e.target.value))}
                    disabled={isLoading}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                    <span>Max fatigue threshold</span>
                    <span className="text-foreground font-medium">{maxFatigueThreshold}%</span>
                  </div>
                  <input
                    type="range"
                    min={35}
                    max={80}
                    step={1}
                    value={maxFatigueThreshold}
                    onChange={(e) => setMaxFatigueThreshold(Number(e.target.value))}
                    disabled={isLoading}
                    className="w-full"
                  />
                </div>

                <div>
                  <label htmlFor="daily-screen-limit" className="text-xs text-muted-foreground">Daily screen limit (hours)</label>
                  <input
                    id="daily-screen-limit"
                    type="number"
                    min={2}
                    max={14}
                    step={0.5}
                    value={dailyScreenLimitHours}
                    onChange={(e) => setDailyScreenLimitHours(parseFloat(e.target.value) || 8)}
                    disabled={isLoading}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                  />
                </div>

                <div>
                  <label htmlFor="preferred-work-slot" className="text-xs text-muted-foreground">Preferred work hours</label>
                  <input
                    id="preferred-work-slot"
                    type="text"
                    value={preferredWorkSlot}
                    onChange={(e) => setPreferredWorkSlot(e.target.value)}
                    disabled={isLoading}
                    placeholder="e.g., 09:00-17:00"
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
