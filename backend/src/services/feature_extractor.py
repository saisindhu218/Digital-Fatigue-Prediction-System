"""
REAL LIVE Feature extraction for fatigue and productivity ML models
Uses behavioral metrics: keystrokes, mouse, idle, app switching, cognitive load
Supports app_name + window_title for browser tab awareness
"""

import numpy as np
from datetime import datetime
from typing import Dict,List,Optional

class LiveFeatureExtractor:

    def extract_features_from_live_data(self,laptop_data:List[Dict],mobile_data:List[Dict],user_id:Optional[str]=None)->Dict[str,float]:

        all_data=laptop_data+mobile_data
        if not all_data:
            return self._get_default_features()

        try:

            total_screen_seconds=sum(self._get_duration(x) for x in all_data)
            total_screen_hours=total_screen_seconds/3600

            session_count=len(all_data)
            avg_session_hours=total_screen_hours/max(session_count,1)

            total_idle_seconds=sum(float(x.get("idle_time_seconds",0)) for x in laptop_data)
            idle_ratio=total_idle_seconds/max(total_screen_seconds,1)

            total_keystrokes=sum(int(x.get("keystrokes",0)) for x in laptop_data)
            keystrokes_per_hour=total_keystrokes/max(total_screen_hours,1)

            total_mouse=sum(
                int(x.get("mouse_clicks",0))+int(x.get("mouse_moves",0))
                for x in laptop_data
            )
            mouse_per_hour=total_mouse/max(total_screen_hours,1)

            total_switches=sum(int(x.get("app_switches",0)) for x in laptop_data)
            switches_per_hour=total_switches/max(total_screen_hours,1)

            breaks=self._calculate_breaks(all_data)
            night_ratio=self._calculate_night_ratio(all_data)
            productive_ratio=self._calculate_productive_ratio(all_data)
            cognitive_load=self._calculate_cognitive_load(laptop_data)

            focus_score=self._calculate_focus_score(productive_ratio,idle_ratio,switches_per_hour)

            fatigue_index=self._calculate_fatigue_index(
                total_screen_hours,idle_ratio,keystrokes_per_hour,
                mouse_per_hour,switches_per_hour,cognitive_load
            )

            return{
                "screen_time":round(total_screen_hours,2),
                "avg_session":round(avg_session_hours,2),
                "breaks":breaks,
                "night_ratio":round(night_ratio,2),
                "productive_ratio":round(productive_ratio,2),
                "focus_score":round(focus_score,2),
                "idle_ratio":round(idle_ratio,3),
                "keystrokes_per_hour":round(keystrokes_per_hour,2),
                "mouse_per_hour":round(mouse_per_hour,2),
                "switches_per_hour":round(switches_per_hour,2),
                "cognitive_load":round(cognitive_load,2),
                "fatigue_index":round(fatigue_index,2)
            }

        except Exception as e:
            print("Feature extraction error:",e)
            return self._get_default_features()

    def _get_duration(self,item:Dict)->float:
        if "usage_duration" in item:
            return float(item["usage_duration"])*60
        if "screen_time" in item:
            return float(item["screen_time"])
        if "duration" in item:
            return float(item["duration"])
        return 60

    def _calculate_breaks(self,data:List[Dict])->int:

        if len(data)<2:
            return 0

        sorted_data=sorted(data,key=lambda x:self._get_timestamp(x) or datetime.utcnow())
        breaks=0

        for i in range(1,len(sorted_data)):
            prev=self._get_timestamp(sorted_data[i-1])
            curr=self._get_timestamp(sorted_data[i])

            if prev and curr:
                gap=(curr-prev).total_seconds()
                if gap>600:
                    breaks+=1

        return breaks

    def _get_timestamp(self,item:Dict)->Optional[datetime]:

        ts=item.get("timestamp")

        if isinstance(ts,datetime):
            return ts

        if isinstance(ts,str):
            try:
                return datetime.fromisoformat(ts.replace("Z","+00:00"))
            except:
                return None

        return None

    def _calculate_night_ratio(self,data:List[Dict])->float:

        night_seconds=0
        total_seconds=0

        for item in data:
            duration=self._get_duration(item)
            total_seconds+=duration
            ts=self._get_timestamp(item)

            if ts and (ts.hour>=22 or ts.hour<=5):
                night_seconds+=duration

        return night_seconds/max(total_seconds,1)

    def _calculate_productive_ratio(self,data:List[Dict])->float:

        productive_keywords=[
            "code","pycharm","studio","terminal",
            "word","excel","docs","learning",
            "notepad","powershell","github",
            "stackoverflow","research"
        ]

        productive=0
        total=0

        for item in data:

            duration=self._get_duration(item)
            total+=duration

            name=str(item.get("active_app") or "")+str(item.get("app_name") or "")+str(item.get("window_title") or "")
            name=name.lower()

            if any(x in name for x in productive_keywords):
                productive+=duration

        return productive/max(total,1)

    def _calculate_cognitive_load(self,data:List[Dict])->float:

        load=0
        total=0

        for item in data:

            category=str(item.get("app_category","MEDIUM")).upper()

            if category=="HIGH":
                load+=3
            elif category=="MEDIUM":
                load+=2
            else:
                load+=1

            total+=1

        return load/max(total,1)

    def _calculate_focus_score(self,productive_ratio,idle_ratio,switches_per_hour)->float:

        score=(productive_ratio*100-idle_ratio*50-switches_per_hour*2)

        return max(0,min(100,score))

    def _calculate_fatigue_index(self,screen,idle,keys,mouse,switches,cognitive)->float:

        fatigue=(screen*5+idle*50+switches*1.5+cognitive*10-keys*0.01-mouse*0.005)

        return max(0,min(100,fatigue))

    def _get_default_features(self)->Dict[str,float]:

        return{
            "screen_time":2.0,
            "avg_session":0.5,
            "breaks":1,
            "night_ratio":0.1,
            "productive_ratio":0.6,
            "focus_score":70,
            "idle_ratio":0.1,
            "keystrokes_per_hour":200,
            "mouse_per_hour":300,
            "switches_per_hour":10,
            "cognitive_load":2,
            "fatigue_index":30
        }