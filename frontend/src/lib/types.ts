export interface User{
  id:string;
  email:string;
  name?:string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export interface LaptopUsage{
  active_app:string;
  app_category:string;
  usage_duration:number;

  session_length_minutes?:number;
  idle_time_seconds?:number;
  keystrokes?:number;
  mouse_clicks?:number;
  mouse_moves?:number;
  app_switches?:number;
  time_of_day?:string;
}

export interface MobileUsage{
  app_name:string;
  category?:string;
  screen_time:number;
  notifications_received:number;
}

export interface FatiguePrediction{
  fatigue_level:string;
  fatigue_score:number;
  confidence:number;
  factors?:string[];
}

export interface ProductivityPrediction{
  productivity_loss_hours:number;
  productivity_score:number;
  breakdown?:Record<string,number>;
}

export interface Predictions{
  fatigue:FatiguePrediction;
  productivity:ProductivityPrediction;
}

export interface Summary{
  total_screen_time:number;
  total_sessions:number;
  avg_session_length:number;
  focus_score:number;
  break_frequency:number;
  peak_hours:string;
  most_used_app:string;
  cognitive_load?:number;
}

export interface Trends{
  fatigueTrend:{day:string;score:number}[];
  productivityTrend:{day:string;score:number}[];
}

export interface UsageResponse{
  summary:Summary;

  predictions:Predictions;

  laptop_usage:LaptopUsage[];

  mobile_usage:MobileUsage[];

  trends?:Trends;
}

export interface DeviceInfo{
  device_id:string;
  device_type:string;
  status:'connected'|'disconnected';
  last_synced:string;
  data_points:number;
}