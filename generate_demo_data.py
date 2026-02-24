"""
Generate realistic demo health data for Fitbit Analytics
Based on real Fitbit Takeout structure - with HUMAN variation and FLUID HR
"""

import json
import csv
import random
from datetime import datetime, timedelta
import os

# Demo person: 30yo male, healthy but HUMAN (variable patterns)
DEMO_AGE = 30
DEMO_GENDER = "MALE"
DEMO_HEIGHT_CM = 178
DEMO_WEIGHT_KG = 73
DEMO_NAME = "Demo User"

# Base paths
BASE_DIR = "/Users/stableunit-hamza/Desktop/fitbit_analytics/Demo_data/Fitbit"
EXPORT_DIR = os.path.join(BASE_DIR, "Global Export Data")
HRV_DIR = os.path.join(BASE_DIR, "Heart Rate Variability")
SPO2_DIR = os.path.join(BASE_DIR, "Oxygen Saturation (SpO2)")
STRESS_DIR = os.path.join(BASE_DIR, "Stress Score")
SLEEP_SCORE_DIR = os.path.join(BASE_DIR, "Sleep Score")
PROFILE_DIR = os.path.join(BASE_DIR, "Your Profile")

# Generate 14 days of data
START_DATE = datetime(2026, 1, 20)
DAYS = 14


def get_next_hr(current_hr, target_hr, activity_type="resting"):
    """
    Generate next HR value with realistic fluid movement
    Based on real Fitbit data: 66% of readings stay same or change by 1 bpm
    Average change is ~1.8 bpm
    """
    # Determine direction toward target
    diff = target_hr - current_hr
    
    if activity_type == "sleeping":
        # Very stable during sleep
        change_weights = [
            (0, 0.50),   # 50% stay same
            (1, 0.30),   # 30% change by 1
            (-1, 0.15),  # 15% change by -1
            (2, 0.03),   # 3% change by 2
            (-2, 0.02),  # 2% change by -2
        ]
    elif activity_type == "resting":
        # Moderate stability
        change_weights = [
            (0, 0.30),   # 30% stay same
            (1, 0.25),   # 25% change by 1
            (-1, 0.20),  # 20% change by -1
            (2, 0.12),   # 12% change by 2
            (-2, 0.08),  # 8% change by -2
            (3, 0.03),   # 3% change by 3
            (-3, 0.02),  # 2% change by -3
        ]
    else:  # active
        # More variable during activity
        change_weights = [
            (0, 0.15),   # 15% stay same
            (1, 0.22),   # 22% change by 1
            (-1, 0.18),  # 18% change by -1
            (2, 0.18),   # 18% change by 2
            (-2, 0.14),  # 14% change by -2
            (3, 0.08),   # 8% change by 3
            (-3, 0.04),  # 4% change by -3
            (4, 0.01),   # 1% change by 4
        ]
    
    # Pick a change based on weights
    changes, weights = zip(*change_weights)
    change = random.choices(changes, weights=weights)[0]
    
    # Apply change, but tend toward target
    new_hr = current_hr + change
    
    # Gentle pull toward target (if far away, higher chance to move toward it)
    if abs(diff) > 5 and random.random() < 0.3:
        new_hr += (1 if diff > 0 else -1)
    
    return new_hr


def generate_sleep_schedule(date, day_index):
    """Generate realistic variable sleep patterns like real human data"""
    is_weekend = date.weekday() >= 5
    
    # Bedtime varies: 22:30 to 01:00 (with weekend tendency for later)
    if is_weekend and random.random() < 0.6:
        bed_hour = random.randint(0, 1)  # After midnight on weekends
        bed_minute = random.randint(0, 59)
    else:
        if random.random() < 0.7:
            bed_hour = random.randint(22, 23)
        else:
            bed_hour = random.randint(0, 1)
        bed_minute = random.randint(0, 59)
    
    # Sleep duration varies: 5h to 9h
    sleep_duration_hours = random.choice([
        random.uniform(4.5, 5.5),   # Short night (20%)
        random.uniform(6.0, 7.0),   # Normal weeknight (40%)
        random.uniform(7.0, 8.0),   # Good night (30%)
        random.uniform(8.0, 9.2),   # Long weekend sleep (10%)
    ])
    
    sleep_date = date - timedelta(days=1)
    
    if bed_hour >= 22:
        start_time = datetime(sleep_date.year, sleep_date.month, sleep_date.day, bed_hour, bed_minute, 0)
    else:
        start_time = datetime(date.year, date.month, date.day, bed_hour, bed_minute, 0)
    
    end_time = start_time + timedelta(hours=sleep_duration_hours)
    
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    minutes_in_bed = int(sleep_duration_hours * 60)
    
    efficiency = random.randint(85, 96)
    minutes_asleep = int(minutes_in_bed * efficiency / 100)
    minutes_awake = minutes_in_bed - minutes_asleep
    
    # Deep sleep VARIES significantly
    if sleep_duration_hours < 5.5:
        deep_minutes = random.randint(20, 50)
    elif random.random() < 0.15:
        deep_minutes = random.randint(0, 30)
    else:
        deep_minutes = random.randint(55, 95)
    
    rem_minutes = random.randint(70, 110)
    light_minutes = max(0, minutes_asleep - deep_minutes - rem_minutes)
    wake_minutes = minutes_awake
    
    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": duration_ms,
        "minutes_in_bed": minutes_in_bed,
        "minutes_asleep": minutes_asleep,
        "minutes_awake": minutes_awake,
        "efficiency": efficiency,
        "deep_minutes": deep_minutes,
        "rem_minutes": rem_minutes,
        "light_minutes": light_minutes,
        "wake_minutes": wake_minutes
    }


def generate_heart_rate_for_day(date, sleep_info):
    """Generate realistic heart rate with FLUID, GRADUAL changes
    Like real Fitbit data: changes 0-3 bpm at a time, trending smoothly
    """
    data = []
    base_time = datetime(date.year, date.month, date.day, 0, 0, 0)
    
    sleep_start = sleep_info["start_time"]
    sleep_end = sleep_info["end_time"]
    
    # Define activity periods with TARGET HRs (not fixed values)
    # HR will fluidly move toward these targets
    activity_periods = []
    
    # Random activity - not every day is the same
    activity_level = random.choice([
        "high",    # 20%
        "normal",  # 50%
        "low",     # 25%
        "rest",    # 5%
    ])
    
    if activity_level == "high":
        for _ in range(random.randint(2, 3)):
            start_h = random.randint(7, 20)
            start_m = random.randint(0, 59)
            duration = random.randint(30, 90)
            target_hr = random.randint(100, 145)
            activity_periods.append((start_h, start_m, duration, target_hr))
    elif activity_level == "normal":
        for _ in range(random.randint(1, 2)):
            start_h = random.randint(8, 19)
            start_m = random.randint(0, 59)
            duration = random.randint(20, 60)
            target_hr = random.randint(90, 125)
            activity_periods.append((start_h, start_m, duration, target_hr))
    elif activity_level == "low":
        if random.random() < 0.6:
            start_h = random.randint(12, 18)
            start_m = random.randint(0, 59)
            duration = random.randint(15, 30)
            target_hr = random.randint(85, 110)
            activity_periods.append((start_h, start_m, duration, target_hr))
    
    current = base_time
    current_hr = random.randint(52, 58)  # Start with sleeping HR
    
    while current < base_time + timedelta(days=1):
        # Determine if sleeping
        is_sleeping = (current >= sleep_start and current < sleep_end) or \
                      (sleep_start > sleep_end and (current >= sleep_start or current < sleep_end))
        
        # Determine target HR and activity type
        if is_sleeping:
            target_hr = random.randint(52, 62)
            activity_type = "sleeping"
        else:
            # Check if in activity period
            in_activity = False
            target_hr = random.randint(62, 78)  # Default resting
            activity_type = "resting"
            
            for start_h, start_m, duration_mins, period_target in activity_periods:
                period_start = datetime(current.year, current.month, current.day, start_h, start_m, 0)
                period_end = period_start + timedelta(minutes=duration_mins)
                if period_start <= current < period_end:
                    in_activity = True
                    activity_type = "active"
                    # Ramp up and down
                    progress = (current - period_start).total_seconds() / (duration_mins * 60)
                    if progress < 0.15:
                        target_hr = random.randint(75, 90)  # Warming up
                    elif progress > 0.85:
                        target_hr = random.randint(75, 90)  # Cooling down
                    else:
                        target_hr = period_target  # Active
                    break
        
        # Generate next HR with fluid movement toward target
        current_hr = get_next_hr(current_hr, target_hr, activity_type)
        
        # Clamp to realistic bounds
        current_hr = max(48, min(155, current_hr))
        
        data.append({
            "dateTime": current.strftime("%m/%d/%y %H:%M:%S"),
            "value": {
                "bpm": current_hr,
                "confidence": random.choice([1, 1, 1, 1, 2, 2, 3])
            }
        })
        
        # Heart rate every 5 seconds on average
        current += timedelta(seconds=random.randint(4, 7))
    
    return data


def generate_steps_calories_data(dates, sleep_infos):
    """Generate variable steps and calories based on actual activity patterns"""
    steps_data = []
    calories_data = []
    
    base_time = dates[0]
    end_time = dates[-1] + timedelta(days=1)
    current = base_time
    
    daily_steps = {}
    
    while current < end_time:
        date_key = current.date()
        
        if date_key not in daily_steps:
            daily_steps[date_key] = 0
            activity_level = random.choice([
                (0.15, 12000, 18000),
                (0.45, 7000, 12000),
                (0.30, 3000, 7000),
                (0.10, 1000, 3000),
            ])
        
        hour, minute = current.hour, current.minute
        
        if 7 <= hour < 22:
            if random.random() < 0.3:
                if activity_level[1] > 10000:
                    steps = random.randint(30, 120)
                elif activity_level[1] > 6000:
                    steps = random.randint(15, 80)
                else:
                    steps = random.randint(0, 40)
            else:
                steps = 0
        else:
            steps = 0
        
        steps_data.append({
            "dateTime": current.strftime("%m/%d/%y %H:%M:%S"),
            "value": str(steps)
        })
        
        daily_steps[date_key] += steps
        
        if steps > 50:
            cal = round(random.uniform(3.0, 6.0), 2)
        elif steps > 0:
            cal = round(random.uniform(1.5, 3.0), 2)
        elif hour < 7 or hour >= 23:
            cal = round(random.uniform(0.9, 1.2), 2)
        else:
            cal = round(random.uniform(1.1, 1.6), 2)
        
        calories_data.append({
            "dateTime": current.strftime("%m/%d/%y %H:%M:%S"),
            "value": str(cal)
        })
        
        current += timedelta(minutes=1)
    
    return steps_data, calories_data, daily_steps


def generate_sleep_data(dates):
    """Generate variable human-like sleep data"""
    all_sleep = []
    sleep_infos = {}
    
    for i, date in enumerate(dates[1:], 1):
        sleep_vars = generate_sleep_schedule(date, i)
        
        log_id = 51000000000 + i * 1000000 + random.randint(0, 999999)
        
        sleep_entry = {
            "logId": log_id,
            "dateOfSleep": date.strftime("%Y-%m-%d"),
            "startTime": sleep_vars["start_time"].strftime("%Y-%m-%dT%H:%M:%S.000"),
            "endTime": sleep_vars["end_time"].strftime("%Y-%m-%dT%H:%M:%S.000"),
            "duration": sleep_vars["duration_ms"],
            "minutesToFallAsleep": random.randint(3, 20),
            "minutesAsleep": sleep_vars["minutes_asleep"],
            "minutesAwake": sleep_vars["minutes_awake"],
            "minutesAfterWakeup": 0,
            "timeInBed": sleep_vars["minutes_in_bed"],
            "efficiency": sleep_vars["efficiency"],
            "type": "stages",
            "infoCode": 0,
            "logType": "auto_detected",
            "mainSleep": True,
            "levels": {
                "summary": {
                    "deep": {"count": random.randint(2, 5), "minutes": sleep_vars["deep_minutes"], "thirtyDayAvgMinutes": 75},
                    "light": {"count": random.randint(12, 25), "minutes": sleep_vars["light_minutes"], "thirtyDayAvgMinutes": 200},
                    "rem": {"count": random.randint(4, 9), "minutes": sleep_vars["rem_minutes"], "thirtyDayAvgMinutes": 95},
                    "wake": {"count": random.randint(10, 30), "minutes": sleep_vars["wake_minutes"], "thirtyDayAvgMinutes": 40}
                },
                "data": [],
                "shortData": []
            }
        }
        all_sleep.append(sleep_entry)
        sleep_infos[date] = sleep_vars
        
        # Occasional nap
        if date.weekday() >= 5 and random.random() < 0.15:
            nap_start = datetime(date.year, date.month, date.day, 14, random.randint(0, 30), 0)
            nap_duration = random.randint(30, 90)
            nap_end = nap_start + timedelta(minutes=nap_duration)
            
            nap_entry = {
                "logId": log_id + 500000,
                "dateOfSleep": date.strftime("%Y-%m-%d"),
                "startTime": nap_start.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "endTime": nap_end.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "duration": nap_duration * 60 * 1000,
                "minutesToFallAsleep": 3,
                "minutesAsleep": nap_duration - 5,
                "minutesAwake": 5,
                "minutesAfterWakeup": 0,
                "timeInBed": nap_duration,
                "efficiency": random.randint(88, 95),
                "type": "stages",
                "infoCode": 0,
                "logType": "auto_detected",
                "mainSleep": False,
                "levels": {
                    "summary": {
                        "deep": {"count": random.randint(0, 2), "minutes": random.randint(5, 25), "thirtyDayAvgMinutes": 15},
                        "light": {"count": random.randint(2, 6), "minutes": random.randint(20, 50), "thirtyDayAvgMinutes": 35},
                        "rem": {"count": random.randint(1, 3), "minutes": random.randint(5, 20), "thirtyDayAvgMinutes": 10},
                        "wake": {"count": random.randint(2, 5), "minutes": 5, "thirtyDayAvgMinutes": 5}
                    },
                    "data": [],
                    "shortData": []
                }
            }
            all_sleep.append(nap_entry)
    
    return all_sleep, sleep_infos


def generate_resting_hr_data(dates):
    """Generate variable resting HR"""
    data = []
    
    for date in dates:
        base_rhr = random.choice([
            random.randint(55, 58),
            random.randint(59, 63),
            random.randint(64, 68),
        ])
        
        data.append({
            "dateTime": (date + timedelta(days=1)).strftime("%m/%d/%y %H:%M:%S"),
            "value": {
                "date": date.strftime("%m/%d/%y"),
                "value": float(base_rhr),
                "error": random.uniform(7, 13)
            }
        })
    
    return data


def generate_hrv_csv(dates):
    """Generate variable HRV data"""
    rows = []
    
    for date in dates:
        rmssd = round(random.choice([
            random.uniform(38, 48),
            random.uniform(48, 58),
            random.uniform(58, 68),
            random.uniform(68, 80),
        ]), 3)
        
        nremhr = random.randint(52, 62)
        entropy = round(random.uniform(1.1, 1.7), 3)
        
        rows.append({
            "timestamp": date.strftime("%Y-%m-%dT%H:%M:%S"),
            "rmssd": rmssd,
            "nremhr": nremhr,
            "entropy": entropy
        })
    
    return rows


def generate_spo2_csv(dates):
    """Generate realistic SpO2 data"""
    rows = []
    
    for date in dates:
        avg = round(random.choice([
            random.uniform(96.0, 97.0),
            random.uniform(97.0, 98.0),
            random.uniform(98.0, 98.8),
            random.uniform(98.8, 99.5),
        ]), 1)
        
        lower = round(avg - random.uniform(0.8, 2.0), 1)
        upper = min(100, round(avg + random.uniform(0.5, 1.5), 1))
        
        rows.append({
            "timestamp": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "average_value": avg,
            "lower_bound": lower,
            "upper_bound": upper
        })
    
    return rows


def generate_stress_csv(dates):
    """Generate variable stress scores"""
    rows = []
    base_score = 75
    
    for i, date in enumerate(dates):
        variation = random.choice([
            random.randint(-15, -8),
            random.randint(-5, -2),
            random.randint(-2, 2),
            random.randint(2, 8),
        ])
        
        stress = max(50, min(92, base_score + variation))
        
        sleep_pts = random.randint(20, 30)
        resp_pts = random.randint(22, 30)
        exertion_pts = random.randint(26, 38)
        
        rows.append({
            "DATE": date.strftime("%Y-%m-%dT%H:%M:%S"),
            "UPDATED_AT": (date + timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S.000"),
            "STRESS_SCORE": stress,
            "SLEEP_POINTS": sleep_pts,
            "MAX_SLEEP_POINTS": 30,
            "RESPONSIVENESS_POINTS": resp_pts,
            "MAX_RESPONSIVENESS_POINTS": 30,
            "EXERTION_POINTS": exertion_pts,
            "MAX_EXERTION_POINTS": 40,
            "STATUS": "READY",
            "CALCULATION_FAILED": "false"
        })
    
    return rows


def generate_sleep_score_csv(sleep_data):
    """Generate variable sleep scores"""
    rows = []
    
    for sleep in sleep_data:
        if not sleep.get("mainSleep", True):
            continue
        
        date_str = sleep["dateOfSleep"]
        date = datetime.strptime(date_str, "%Y-%m-%d")
        
        efficiency = sleep["efficiency"]
        deep = sleep["levels"]["summary"]["deep"]["minutes"]
        duration_hours = sleep["minutesAsleep"] / 60
        
        base_score = efficiency - 5
        
        if deep > 70:
            base_score += random.randint(3, 8)
        elif deep < 40:
            base_score -= random.randint(5, 12)
        
        if duration_hours >= 7.5:
            base_score += random.randint(2, 5)
        elif duration_hours < 6:
            base_score -= random.randint(3, 8)
        
        overall = min(95, max(55, base_score + random.randint(-3, 3)))
        
        composition = min(25, max(15, int(deep / 4) + random.randint(-2, 3)))
        revitalization = random.randint(18, 24)
        duration_score = min(45, max(20, int(duration_hours * 5.5) + random.randint(-3, 3)))
        
        rows.append({
            "sleep_log_entry_id": sleep["logId"],
            "timestamp": sleep["endTime"],
            "overall_score": overall,
            "composition_score": composition,
            "revitalization_score": revitalization,
            "duration_score": duration_score,
            "deep_sleep_in_minutes": deep,
            "resting_heart_rate": random.randint(55, 66),
            "restlessness": round(random.uniform(0.04, 0.09), 2)
        })
    
    return rows


def generate_heart_rate_zones(dates):
    """Generate variable HR zones data"""
    zones_data = []
    
    for date in dates:
        activity = random.choice([
            {"fat": random.randint(35, 55), "cardio": random.randint(20, 40), "peak": random.randint(8, 20)},
            {"fat": random.randint(20, 35), "cardio": random.randint(10, 25), "peak": random.randint(3, 12)},
            {"fat": random.randint(10, 25), "cardio": random.randint(5, 15), "peak": random.randint(0, 8)},
            {"fat": random.randint(5, 15), "cardio": random.randint(0, 8), "peak": 0},
        ])
        
        fat_burn = activity["fat"]
        cardio = activity["cardio"]
        peak = activity["peak"]
        out_of_zone = 1440 - fat_burn - cardio - peak
        
        zones_data.append({
            "dateTime": date.strftime("%m/%d/%y %H:%M:%S"),
            "value": {
                "valuesInZones": {
                    "IN_DEFAULT_ZONE_1": fat_burn,
                    "IN_DEFAULT_ZONE_2": cardio,
                    "IN_DEFAULT_ZONE_3": peak,
                    "BELOW_DEFAULT_ZONE_1": out_of_zone
                }
            }
        })
    
    return zones_data


def generate_profile():
    """Generate profile CSV"""
    return {
        "id": "DEMO001",
        "full_name": DEMO_NAME,
        "first_name": "Demo",
        "last_name": "User",
        "display_name_setting": "name",
        "display_name": DEMO_NAME,
        "username": "null",
        "email_address": "demo@example.com",
        "date_of_birth": "1996-03-15",
        "child": "false",
        "country": "null",
        "state": "null",
        "city": "null",
        "timezone": "Europe/London",
        "locale": "en_US",
        "member_since": "2024-01-15",
        "about_me": "null",
        "start_of_week": "MONDAY",
        "sleep_tracking": "Normal",
        "time_display_format": "24hour",
        "gender": DEMO_GENDER,
        "height": float(DEMO_HEIGHT_CM),
        "weight": float(DEMO_WEIGHT_KG),
        "stride_length_walking": 75.0,
        "stride_length_running": 115.0,
        "weight_unit": "METRIC",
        "distance_unit": "METRIC",
        "height_unit": "METRIC",
        "water_unit": "en_US",
        "glucose_unit": "en_US",
        "swim_unit": "METRIC"
    }


def main():
    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]
    
    # Generate sleep data FIRST
    sleep_entries, sleep_infos = generate_sleep_data(dates)
    
    # Generate individual heart rate files
    for date in dates:
        sleep_info = sleep_infos.get(date, {
            "start_time": datetime(date.year, date.month, date.day, 23, 0, 0),
            "end_time": datetime(date.year, date.month, date.day, 6, 30, 0) + timedelta(days=1)
        })
        hr_data = generate_heart_rate_for_day(date, sleep_info)
        filename = f"heart_rate-{date.strftime('%Y-%m-%d')}.json"
        with open(os.path.join(EXPORT_DIR, filename), 'w') as f:
            json.dump(hr_data, f, indent=2)
    print(f"Generated {DAYS} heart rate files")
    
    # Generate cumulative steps and calories
    steps_data, calories_data, daily_steps = generate_steps_calories_data(dates, sleep_infos)
    
    with open(os.path.join(EXPORT_DIR, "steps-2026-01-20.json"), 'w') as f:
        json.dump(steps_data, f, indent=2)
    print(f"Generated steps data")
    
    with open(os.path.join(EXPORT_DIR, "calories-2026-01-20.json"), 'w') as f:
        json.dump(calories_data, f, indent=2)
    
    # Write sleep data
    with open(os.path.join(EXPORT_DIR, "sleep-2026-01-20.json"), 'w') as f:
        json.dump(sleep_entries, f, indent=2)
    main_sleep_count = len([s for s in sleep_entries if s.get("mainSleep", True)])
    print(f"Generated {len(sleep_entries)} sleep entries ({main_sleep_count} main, {len(sleep_entries)-main_sleep_count} naps)")
    
    # Generate resting HR
    resting_hr = generate_resting_hr_data(dates)
    with open(os.path.join(EXPORT_DIR, "resting_heart_rate-2026-01-20.json"), 'w') as f:
        json.dump(resting_hr, f, indent=2)
    avg_rhr = sum(r['value']['value'] for r in resting_hr) / len(resting_hr)
    print(f"Generated resting HR (avg: {avg_rhr:.1f} bpm)")
    
    # Generate HR zones
    hr_zones = generate_heart_rate_zones(dates)
    for i, date in enumerate(dates):
        filename = f"time_in_heart_rate_zones-{date.strftime('%Y-%m-%d')}.json"
        with open(os.path.join(EXPORT_DIR, filename), 'w') as f:
            json.dump([hr_zones[i]], f, indent=2)
    
    # Generate HRV
    hrv_data = generate_hrv_csv(dates)
    with open(os.path.join(HRV_DIR, "Daily Heart Rate Variability Summary - 2026-01-20.csv"), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "rmssd", "nremhr", "entropy"])
        writer.writeheader()
        writer.writerows(hrv_data)
    avg_rmssd = sum(r['rmssd'] for r in hrv_data) / len(hrv_data)
    print(f"Generated HRV (avg RMSSD: {avg_rmssd:.1f} ms)")
    
    # Generate SpO2
    spo2_data = generate_spo2_csv(dates)
    with open(os.path.join(SPO2_DIR, "Daily SpO2 - 2026-01-20-2026-02-02.csv"), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "average_value", "lower_bound", "upper_bound"])
        writer.writeheader()
        writer.writerows(spo2_data)
    avg_spo2 = sum(s['average_value'] for s in spo2_data) / len(spo2_data)
    print(f"Generated SpO2 (avg: {avg_spo2:.1f}%)")
    
    # Generate stress
    stress_data = generate_stress_csv(dates)
    with open(os.path.join(STRESS_DIR, "Stress Score.csv"), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["DATE", "UPDATED_AT", "STRESS_SCORE", "SLEEP_POINTS", 
                                               "MAX_SLEEP_POINTS", "RESPONSIVENESS_POINTS", 
                                               "MAX_RESPONSIVENESS_POINTS", "EXERTION_POINTS", 
                                               "MAX_EXERTION_POINTS", "STATUS", "CALCULATION_FAILED"])
        writer.writeheader()
        writer.writerows(stress_data)
    scores = [s['STRESS_SCORE'] for s in stress_data]
    print(f"Generated stress scores (range: {min(scores)}-{max(scores)})")
    
    # Generate sleep scores
    sleep_score_data = generate_sleep_score_csv(sleep_entries)
    with open(os.path.join(SLEEP_SCORE_DIR, "sleep_score.csv"), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["sleep_log_entry_id", "timestamp", "overall_score",
                                               "composition_score", "revitalization_score", "duration_score",
                                               "deep_sleep_in_minutes", "resting_heart_rate", "restlessness"])
        writer.writeheader()
        writer.writerows(sleep_score_data)
    sleep_scores = [s['overall_score'] for s in sleep_score_data]
    print(f"Generated sleep scores (range: {min(sleep_scores)}-{max(sleep_scores)})")
    
    # Generate profile
    profile = generate_profile()
    with open(os.path.join(PROFILE_DIR, "Profile.csv"), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=profile.keys())
        writer.writeheader()
        writer.writerow(profile)
    
    # Verify HR fluidity
    print("\n" + "="*60)
    print("Verifying HR fluidity (sample changes):")
    sample_file = os.path.join(EXPORT_DIR, "heart_rate-2026-01-22.json")
    with open(sample_file) as f:
        hr_data = json.load(f)
    
    changes = []
    for i in range(1, min(200, len(hr_data))):
        diff = abs(hr_data[i]['value']['bpm'] - hr_data[i-1]['value']['bpm'])
        changes.append(diff)
    
    from collections import Counter
    c = Counter(changes)
    print(f"  0 bpm change: {c[0]} times ({c[0]/len(changes)*100:.1f}%)")
    print(f"  1 bpm change: {c[1]} times ({c[1]/len(changes)*100:.1f}%)")
    print(f"  2 bpm change: {c[2]} times ({c[2]/len(changes)*100:.1f}%)")
    print(f"  3+ bpm change: {sum(v for k,v in c.items() if k>=3)} times")
    print(f"  Average change: {sum(changes)/len(changes):.2f} bpm")
    print("="*60)


if __name__ == "__main__":
    main()
