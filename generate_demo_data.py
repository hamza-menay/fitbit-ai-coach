"""
Generate realistic demo health data for Fitbit Analytics (fitbit_ai_coach)
Based on real Fitbit Takeout structure - with HUMAN variation, FLUID HR, and EXERCISES
"""

import json
import csv
import random
import os
import zipfile
from datetime import datetime, timedelta
from collections import Counter

# Demo person: Alex Dubois, 35yo male — active but realistic
DEMO_FIRST     = "Alex"
DEMO_LAST      = "Dubois"
DEMO_NAME      = "Alex Dubois"
DEMO_GENDER    = "MALE"
DEMO_HEIGHT_CM = 180.0
DEMO_WEIGHT_KG = 76.0
DEMO_DOB       = "1990-06-05"   # ~35 years old
DEMO_MEMBER    = "2023-03-12"

# Base paths
BASE_DIR       = "/Users/stableunit-hamza/Desktop/fitbit_ai_coach/Demo_data/Fitbit"
EXPORT_DIR     = os.path.join(BASE_DIR, "Global Export Data")
HRV_DIR        = os.path.join(BASE_DIR, "Heart Rate Variability")
SPO2_DIR       = os.path.join(BASE_DIR, "Oxygen Saturation (SpO2)")
STRESS_DIR     = os.path.join(BASE_DIR, "Stress Score")
SLEEP_SCORE_DIR= os.path.join(BASE_DIR, "Sleep Score")
PROFILE_DIR    = os.path.join(BASE_DIR, "Your Profile")
EXERCISES_DIR  = os.path.join(BASE_DIR, "Health Fitness Data_GoogleData")

# Generate 14 days of data
START_DATE = datetime(2026, 1, 20)   # Tuesday
DAYS = 14


# ── Scheduled exercises (realistic 10-day training week) ─────────────────────
# Jan 20 = day 0 (Tue), Feb 2 = day 13 (Mon)
# Format: (day_offset, activity_name, activityTypeId, start_h, start_m, duration_min,
#          avg_hr, peak_hr, distance_km, steps, calories_per_min)
EXERCISE_SCHEDULE = [
    # Tue Jan 20 — morning run
    (0,  "Run",            90009, 7, 15, 38,  152, 174,  5.2, 4400,  10.5),
    # Wed Jan 21 — evening walk (post-work)
    (1,  "Walk",           90013, 18, 30, 55,  101, 118,  4.1, 5300,   5.2),
    # Fri Jan 23 — HIIT session
    (3,  "HIIT Training",  57145, 17, 0,  26,  162, 188,  0.0,    0,  11.8),
    # Sat Jan 24 — long outdoor cycling
    (4,  "Cycling",        90001, 9, 45,  72,  137, 163, 23.4,    0,   8.1),
    # Sun Jan 25 — yoga recovery
    (5,  "Yoga",           52001, 10, 0,  45,   82,  98,  0.0,    0,   3.0),
    # Mon Jan 26 — evening run
    (6,  "Run",            90009, 19, 0,  44,  148, 169,  6.1, 5100,  10.2),
    # Tue Jan 27 — lunch walk
    (7,  "Walk",           90013, 12, 15, 42,   97, 114,  3.0, 3900,   5.0),
    # Thu Jan 29 — swim (lunchtime)
    (9,  "Swimming",       82001, 12, 30, 40,  132, 152,  1.2,    0,   9.0),
    # Fri Jan 30 — run (harder, mid-morning)
    (10, "Run",            90009, 8, 30,  48,  158, 181,  6.8, 5800,  10.8),
    # Sat Jan 31 — long walk + hills
    (11, "Walk",           90013, 9, 0,   78,  108, 131,  5.8, 7600,   5.4),
    # Sun Feb 01 — yoga
    (12, "Yoga",           52001, 9, 30,  38,   78,  94,  0.0,    0,   2.9),
    # Mon Feb 02 — quick HIIT (start of new week)
    (13, "HIIT Training",  57145, 6, 45,  24,  166, 191,  0.0,    0,  12.1),
]


def get_next_hr(current_hr, target_hr, activity_type="resting"):
    """
    Generate next HR value with realistic fluid movement.
    Real Fitbit data: ~66% of readings stay same or change by 1 bpm, avg change ~1.8 bpm.
    """
    diff = target_hr - current_hr

    if activity_type == "sleeping":
        change_weights = [
            (0, 0.50), (1, 0.30), (-1, 0.15), (2, 0.03), (-2, 0.02),
        ]
    elif activity_type == "resting":
        change_weights = [
            (0, 0.30), (1, 0.25), (-1, 0.20), (2, 0.12),
            (-2, 0.08), (3, 0.03), (-3, 0.02),
        ]
    else:  # active
        change_weights = [
            (0, 0.15), (1, 0.22), (-1, 0.18), (2, 0.18),
            (-2, 0.14), (3, 0.08), (-3, 0.04), (4, 0.01),
        ]

    changes, weights = zip(*change_weights)
    change = random.choices(changes, weights=weights)[0]
    new_hr = current_hr + change

    # Gentle pull toward target
    if abs(diff) > 5 and random.random() < 0.3:
        new_hr += (1 if diff > 0 else -1)

    return new_hr


def generate_sleep_schedule(date, day_index):
    """Generate realistic variable sleep patterns (humans are NOT periodic)."""
    is_weekend = date.weekday() >= 5
    has_morning_exercise = any(
        (d == day_index and h < 9)
        for d, _, _, h, _, dur, *_ in EXERCISE_SCHEDULE
    )

    # Weekend → later bedtime; early workout → earlier bedtime night before
    if is_weekend and random.random() < 0.55:
        bed_hour   = random.randint(0, 1)
        bed_minute = random.randint(0, 59)
    elif has_morning_exercise and random.random() < 0.7:
        bed_hour   = random.randint(22, 22)
        bed_minute = random.randint(0, 45)
    else:
        bed_hour   = random.choice([22, 22, 23, 23, 0])
        bed_minute = random.randint(0, 59)

    # Duration: humans vary 5–9h; weekend allows longer
    buckets = [
        random.uniform(4.5, 5.5),   # short night
        random.uniform(5.8, 6.8),   # normal weeknight
        random.uniform(6.8, 7.8),   # good night
        random.uniform(7.8, 9.0),   # long/weekend
    ]
    weights = [0.12, 0.38, 0.35, 0.15] if not is_weekend else [0.08, 0.28, 0.38, 0.26]
    sleep_duration_hours = random.choices(buckets, weights=weights)[0]

    sleep_date = date - timedelta(days=1)
    if bed_hour >= 22:
        start_time = datetime(sleep_date.year, sleep_date.month, sleep_date.day, bed_hour, bed_minute, 0)
    else:
        start_time = datetime(date.year, date.month, date.day, bed_hour, bed_minute, 0)

    end_time     = start_time + timedelta(hours=sleep_duration_hours)
    duration_ms  = int((end_time - start_time).total_seconds() * 1000)
    minutes_in_bed = int(sleep_duration_hours * 60)

    efficiency     = random.randint(84, 95)
    minutes_asleep = int(minutes_in_bed * efficiency / 100)
    minutes_awake  = minutes_in_bed - minutes_asleep

    if sleep_duration_hours < 5.5:
        deep_minutes = random.randint(18, 45)
    elif random.random() < 0.12:
        deep_minutes = random.randint(10, 32)
    else:
        deep_minutes = random.randint(52, 92)

    # Post-exercise nights tend to have more deep sleep
    if has_morning_exercise or random.random() < 0.2:
        deep_minutes = min(110, deep_minutes + random.randint(8, 18))

    rem_minutes   = random.randint(65, 108)
    light_minutes = max(0, minutes_asleep - deep_minutes - rem_minutes)
    wake_minutes  = minutes_awake

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
        "wake_minutes": wake_minutes,
    }


def generate_heart_rate_for_day(date, sleep_info, day_index):
    """
    Generate realistic HR with FLUID, GRADUAL changes.
    Exercise sessions are reflected in the HR trace.
    """
    data      = []
    base_time = datetime(date.year, date.month, date.day, 0, 0, 0)

    sleep_start = sleep_info["start_time"]
    sleep_end   = sleep_info["end_time"]

    # Pull scheduled exercises for this day
    day_exercises = [
        (h, m, dur, avg_hr)
        for d, _, _, h, m, dur, avg_hr, *_ in EXERCISE_SCHEDULE
        if d == day_index
    ]

    # Add natural background activity bursts (commute, errands)
    background_activity = []
    if random.random() < 0.55:
        for _ in range(random.randint(1, 2)):
            bh  = random.randint(8, 19)
            bm  = random.randint(0, 59)
            bdr = random.randint(8, 25)
            bhr = random.randint(85, 108)
            background_activity.append((bh, bm, bdr, bhr))

    all_active = day_exercises + background_activity

    current    = base_time
    current_hr = random.randint(51, 57)

    while current < base_time + timedelta(days=1):
        is_sleeping = (
            (current >= sleep_start and current < sleep_end)
            or (sleep_start.date() < sleep_end.date()
                and (current >= sleep_start or current < sleep_end))
        )

        if is_sleeping:
            # Dip to deep sleep HR in first third, small elevation in REM
            elapsed_sleep = (current - sleep_start).total_seconds() / 3600
            if elapsed_sleep < sleep_info["duration_ms"] / 3_600_000 * 0.33:
                target_hr  = random.randint(51, 58)
            elif elapsed_sleep < sleep_info["duration_ms"] / 3_600_000 * 0.66:
                target_hr  = random.randint(53, 62)
            else:
                target_hr  = random.randint(55, 65)
            activity_type = "sleeping"
        else:
            target_hr     = random.randint(62, 78)
            activity_type = "resting"

            for (start_h, start_m, duration_mins, period_target) in all_active:
                period_start = datetime(current.year, current.month, current.day, start_h, start_m, 0)
                period_end   = period_start + timedelta(minutes=duration_mins)
                if period_start <= current < period_end:
                    activity_type = "active"
                    progress = (current - period_start).total_seconds() / (duration_mins * 60)
                    if progress < 0.12:
                        target_hr = random.randint(78, 95)
                    elif progress > 0.88:
                        target_hr = random.randint(75, 92)
                    else:
                        jitter    = random.randint(-6, 6)
                        target_hr = max(85, min(195, period_target + jitter))
                    break

        current_hr = get_next_hr(current_hr, target_hr, activity_type)
        current_hr = max(46, min(198, current_hr))

        data.append({
            "dateTime": current.strftime("%m/%d/%y %H:%M:%S"),
            "value": {
                "bpm": current_hr,
                "confidence": random.choices([1, 2, 3], weights=[0.55, 0.30, 0.15])[0],
            }
        })

        current += timedelta(seconds=random.randint(4, 7))

    return data


def generate_steps_calories_data(dates, sleep_infos):
    """Generate variable steps and calories (exercise days naturally have more steps)."""
    steps_data   = []
    calories_data = []
    daily_steps  = {}

    base_time = dates[0]
    end_time  = dates[-1] + timedelta(days=1)
    current   = base_time

    # Pre-assign daily targets (include exercise boosts)
    day_targets = {}
    for i, d in enumerate(dates):
        day_ex = [(steps,) for off, _, _, _, _, _, _, _, _, steps, _ in EXERCISE_SCHEDULE if off == i]
        ex_steps = sum(s[0] for s in day_ex)
        if ex_steps > 5000:
            base_target = random.randint(9000, 15000)
        elif ex_steps > 0:
            base_target = random.randint(6000, 10000)
        else:
            base_target = random.randint(3000, 8000)
        day_targets[d.date()] = base_target

    while current < end_time:
        date_key = current.date()
        if date_key not in daily_steps:
            daily_steps[date_key] = 0

        target_today = day_targets.get(date_key, 5000)
        hour = current.hour

        if 7 <= hour < 22:
            # More steps if we haven't hit today's target yet and it's afternoon
            remaining = target_today - daily_steps[date_key]
            prob = 0.35 if remaining > 2000 else 0.20
            if random.random() < prob:
                steps = random.randint(
                    25 if target_today < 6000 else 30,
                    80 if target_today < 6000 else 110
                )
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
            cal = round(random.uniform(3.2, 6.5), 2)
        elif steps > 0:
            cal = round(random.uniform(1.6, 3.2), 2)
        elif hour < 6 or hour >= 23:
            cal = round(random.uniform(0.85, 1.15), 2)
        else:
            cal = round(random.uniform(1.1, 1.65), 2)

        calories_data.append({
            "dateTime": current.strftime("%m/%d/%y %H:%M:%S"),
            "value": str(cal)
        })

        current += timedelta(minutes=1)

    return steps_data, calories_data, daily_steps


def generate_sleep_data(dates):
    """Generate variable human-like sleep data."""
    all_sleep   = []
    sleep_infos = {}

    for i, date in enumerate(dates[1:], 1):
        sleep_vars = generate_sleep_schedule(date, i)

        log_id = 51000000000 + i * 1000000 + random.randint(0, 999999)

        sleep_entry = {
            "logId": log_id,
            "dateOfSleep": date.strftime("%Y-%m-%d"),
            "startTime":   sleep_vars["start_time"].strftime("%Y-%m-%dT%H:%M:%S.000"),
            "endTime":     sleep_vars["end_time"].strftime("%Y-%m-%dT%H:%M:%S.000"),
            "duration":    sleep_vars["duration_ms"],
            "minutesToFallAsleep": random.randint(4, 22),
            "minutesAsleep":  sleep_vars["minutes_asleep"],
            "minutesAwake":   sleep_vars["minutes_awake"],
            "minutesAfterWakeup": 0,
            "timeInBed":  sleep_vars["minutes_in_bed"],
            "efficiency": sleep_vars["efficiency"],
            "type":       "stages",
            "infoCode":   0,
            "logType":    "auto_detected",
            "mainSleep":  True,
            "levels": {
                "summary": {
                    "deep":  {"count": random.randint(2, 5), "minutes": sleep_vars["deep_minutes"],  "thirtyDayAvgMinutes": 78},
                    "light": {"count": random.randint(12, 26), "minutes": sleep_vars["light_minutes"], "thirtyDayAvgMinutes": 198},
                    "rem":   {"count": random.randint(4, 9),  "minutes": sleep_vars["rem_minutes"],   "thirtyDayAvgMinutes": 92},
                    "wake":  {"count": random.randint(10, 30), "minutes": sleep_vars["wake_minutes"],  "thirtyDayAvgMinutes": 38},
                },
                "data":      [],
                "shortData": [],
            }
        }
        all_sleep.append(sleep_entry)
        sleep_infos[date] = sleep_vars

        # Occasional weekend nap
        if date.weekday() >= 5 and random.random() < 0.18:
            nap_start    = datetime(date.year, date.month, date.day, 14, random.randint(0, 30), 0)
            nap_duration = random.randint(25, 75)
            nap_end      = nap_start + timedelta(minutes=nap_duration)
            nap_entry    = {
                "logId": log_id + 500000,
                "dateOfSleep": date.strftime("%Y-%m-%d"),
                "startTime":   nap_start.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "endTime":     nap_end.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "duration":    nap_duration * 60 * 1000,
                "minutesToFallAsleep": 4,
                "minutesAsleep":  nap_duration - 6,
                "minutesAwake":   6,
                "minutesAfterWakeup": 0,
                "timeInBed":  nap_duration,
                "efficiency": random.randint(87, 94),
                "type":       "stages",
                "infoCode":   0,
                "logType":    "auto_detected",
                "mainSleep":  False,
                "levels": {
                    "summary": {
                        "deep":  {"count": random.randint(0, 2), "minutes": random.randint(4, 22),  "thirtyDayAvgMinutes": 14},
                        "light": {"count": random.randint(2, 6), "minutes": random.randint(18, 48), "thirtyDayAvgMinutes": 34},
                        "rem":   {"count": random.randint(1, 3), "minutes": random.randint(4, 18),  "thirtyDayAvgMinutes": 10},
                        "wake":  {"count": random.randint(2, 5), "minutes": 6,                      "thirtyDayAvgMinutes": 5},
                    },
                    "data":      [],
                    "shortData": [],
                }
            }
            all_sleep.append(nap_entry)

    return all_sleep, sleep_infos


def generate_resting_hr_data(dates):
    """Generate variable resting HR (lower on post-exercise days)."""
    data      = []
    base_rhr  = random.randint(56, 60)   # Alex's typical RHR

    for i, date in enumerate(dates):
        # After an exercise day, RHR tends to be slightly lower or same
        prev_had_exercise = any(off == i - 1 for off, *_ in EXERCISE_SCHEDULE)
        today_had_exercise = any(off == i for off, *_ in EXERCISE_SCHEDULE)

        if prev_had_exercise and random.random() < 0.5:
            rhr = random.randint(base_rhr - 3, base_rhr)
        elif today_had_exercise:
            rhr = random.randint(base_rhr - 1, base_rhr + 2)
        else:
            rhr = random.randint(base_rhr - 2, base_rhr + 5)

        rhr = max(48, min(72, rhr))

        data.append({
            "dateTime": (date + timedelta(days=1)).strftime("%m/%d/%y %H:%M:%S"),
            "value": {
                "date":  date.strftime("%m/%d/%y"),
                "value": float(rhr),
                "error": round(random.uniform(7.5, 12.5), 2),
            }
        })

    return data


def generate_hrv_csv(dates):
    """Generate variable HRV (higher after good sleep + rest, lower after hard exercise)."""
    rows     = []
    base_rmssd = random.uniform(54, 62)   # Alex's typical HRV range

    for i, date in enumerate(dates):
        had_hard_exercise = any(
            off == i and act in ("Run", "HIIT Training", "Cycling")
            for off, act, *_ in EXERCISE_SCHEDULE
        )
        prev_hard = any(
            off == i - 1 and act in ("Run", "HIIT Training", "Cycling")
            for off, act, *_ in EXERCISE_SCHEDULE
        )

        if prev_hard:
            rmssd = base_rmssd * random.uniform(0.75, 0.90)
        elif had_hard_exercise:
            rmssd = base_rmssd * random.uniform(0.85, 1.05)
        else:
            rmssd = base_rmssd * random.uniform(0.92, 1.18)

        # Add natural day-to-day noise
        rmssd  = max(28, min(95, rmssd + random.gauss(0, 3.5)))
        nremhr = random.randint(50, 60)
        entropy = round(random.uniform(1.10, 1.72), 3)

        rows.append({
            "timestamp": date.strftime("%Y-%m-%dT%H:%M:%S"),
            "rmssd":     round(rmssd, 3),
            "nremhr":    nremhr,
            "entropy":   entropy,
        })

    return rows


def generate_spo2_csv(dates):
    """Generate realistic SpO2 (healthy adult, mild dip after very hard efforts)."""
    rows = []

    for i, date in enumerate(dates):
        had_hard = any(
            off == i and act in ("HIIT Training", "Run")
            for off, act, *_ in EXERCISE_SCHEDULE
        )

        if had_hard:
            avg = round(random.choice([
                random.uniform(96.2, 97.2),
                random.uniform(97.2, 97.8),
            ]), 1)
        else:
            avg = round(random.choice([
                random.uniform(97.2, 98.0),
                random.uniform(98.0, 98.8),
                random.uniform(98.8, 99.4),
            ]), 1)

        lower = round(max(93.0, avg - random.uniform(0.9, 2.1)), 1)
        upper = round(min(100.0, avg + random.uniform(0.4, 1.4)), 1)

        rows.append({
            "timestamp":     date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "average_value": avg,
            "lower_bound":   lower,
            "upper_bound":   upper,
        })

    return rows


def generate_stress_csv(dates):
    """
    Generate readiness/stress scores that correlate with exercise load and sleep.
    High score = well-recovered. After hard sessions score typically drops a bit.
    """
    rows       = []
    base_score = 76   # Alex's healthy baseline

    for i, date in enumerate(dates):
        prev_hard = any(
            off == i - 1 and act in ("Run", "HIIT Training", "Cycling")
            for off, act, *_ in EXERCISE_SCHEDULE
        )
        today_rest = not any(off == i for off, *_ in EXERCISE_SCHEDULE)

        if prev_hard:
            variation = random.randint(-12, -4)
        elif today_rest:
            variation = random.randint(-3, 9)
        else:
            variation = random.randint(-6, 5)

        stress    = max(48, min(94, base_score + variation + random.randint(-3, 3)))

        # Points: sleep 0-30, responsiveness 0-30, exertion 0-40
        sleep_pts  = random.randint(18, 30)
        resp_pts   = random.randint(20, 30)
        # Exertion reflects actual load
        if prev_hard:
            exert_pts = random.randint(30, 40)
        elif any(off == i - 1 for off, *_ in EXERCISE_SCHEDULE):
            exert_pts = random.randint(24, 36)
        else:
            exert_pts = random.randint(18, 30)

        rows.append({
            "DATE":                     date.strftime("%Y-%m-%dT%H:%M:%S"),
            "UPDATED_AT":               (date + timedelta(hours=random.randint(7, 10))).strftime("%Y-%m-%dT%H:%M:%S.000"),
            "STRESS_SCORE":             stress,
            "SLEEP_POINTS":             sleep_pts,
            "MAX_SLEEP_POINTS":         30,
            "RESPONSIVENESS_POINTS":    resp_pts,
            "MAX_RESPONSIVENESS_POINTS":30,
            "EXERTION_POINTS":          exert_pts,
            "MAX_EXERTION_POINTS":      40,
            "STATUS":                   "READY",
            "CALCULATION_FAILED":       "false",
        })

    return rows


def generate_sleep_score_csv(sleep_data):
    """Generate sleep scores correlated with actual sleep metrics."""
    rows = []

    for sleep in sleep_data:
        if not sleep.get("mainSleep", True):
            continue

        efficiency    = sleep["efficiency"]
        deep          = sleep["levels"]["summary"]["deep"]["minutes"]
        duration_hours = sleep["minutesAsleep"] / 60

        base_score = efficiency - 5

        if deep > 72:
            base_score += random.randint(4, 9)
        elif deep < 38:
            base_score -= random.randint(6, 13)

        if duration_hours >= 7.5:
            base_score += random.randint(2, 6)
        elif duration_hours < 5.8:
            base_score -= random.randint(4, 9)

        overall       = min(95, max(52, base_score + random.randint(-4, 4)))
        composition   = min(25, max(14, int(deep / 4) + random.randint(-2, 3)))
        revitalization = random.randint(17, 24)
        dur_score     = min(45, max(18, int(duration_hours * 5.5) + random.randint(-4, 4)))

        rows.append({
            "sleep_log_entry_id": sleep["logId"],
            "timestamp":          sleep["endTime"],
            "overall_score":      overall,
            "composition_score":  composition,
            "revitalization_score": revitalization,
            "duration_score":     dur_score,
            "deep_sleep_in_minutes": deep,
            "resting_heart_rate": random.randint(53, 64),
            "restlessness":       round(random.uniform(0.03, 0.10), 2),
        })

    return rows


def generate_heart_rate_zones(dates):
    """Generate HR zone distribution consistent with scheduled exercises."""
    zones_data = []

    for i, date in enumerate(dates):
        day_ex = [(act, dur, avg_hr) for off, act, _, _, _, dur, avg_hr, *_ in EXERCISE_SCHEDULE if off == i]

        if day_ex:
            act, dur, avg_hr = day_ex[0]
            if avg_hr >= 155:
                fat  = random.randint(18, 32)
                cardio = random.randint(28, 45)
                peak = random.randint(10, 22)
            elif avg_hr >= 130:
                fat  = random.randint(25, 45)
                cardio = random.randint(18, 32)
                peak = random.randint(4, 14)
            else:
                fat  = random.randint(30, 55)
                cardio = random.randint(10, 22)
                peak = random.randint(0, 8)
        else:
            fat  = random.randint(8, 22)
            cardio = random.randint(2, 12)
            peak = random.randint(0, 4)

        out_of_zone = 1440 - fat - cardio - peak

        zones_data.append({
            "dateTime": date.strftime("%m/%d/%y %H:%M:%S"),
            "value": {
                "valuesInZones": {
                    "IN_DEFAULT_ZONE_1": fat,
                    "IN_DEFAULT_ZONE_2": cardio,
                    "IN_DEFAULT_ZONE_3": peak,
                    "BELOW_DEFAULT_ZONE_1": out_of_zone,
                }
            }
        })

    return zones_data


def build_hr_zones_for_exercise(duration_min, avg_hr, peak_hr):
    """Compute realistic HR zone distribution for one exercise session."""
    total = duration_min

    if avg_hr >= 155:
        out_range = max(1, int(total * 0.08))
        fat_burn  = int(total * 0.18)
        cardio    = int(total * 0.44)
        peak      = total - out_range - fat_burn - cardio
    elif avg_hr >= 140:
        out_range = max(2, int(total * 0.12))
        fat_burn  = int(total * 0.30)
        cardio    = int(total * 0.42)
        peak      = total - out_range - fat_burn - cardio
    elif avg_hr >= 120:
        out_range = max(3, int(total * 0.18))
        fat_burn  = int(total * 0.52)
        cardio    = int(total * 0.22)
        peak      = total - out_range - fat_burn - cardio
    else:
        out_range = max(4, int(total * 0.28))
        fat_burn  = int(total * 0.55)
        cardio    = int(total * 0.14)
        peak      = max(0, total - out_range - fat_burn - cardio)

    peak = max(0, peak)
    calories_per_min = 9.0

    return [
        {"name": "Out of Range", "min": 30,       "max": 113,
         "minutes": out_range, "caloriesOut": round(out_range * 4.8, 2)},
        {"name": "Fat Burn",    "min": 113,       "max": 140,
         "minutes": fat_burn,  "caloriesOut": round(fat_burn  * 7.2, 2)},
        {"name": "Cardio",      "min": 140,       "max": 170,
         "minutes": cardio,    "caloriesOut": round(cardio    * 9.5, 2)},
        {"name": "Peak",        "min": 170,       "max": 220,
         "minutes": peak,      "caloriesOut": round(peak      * 11.8, 2)},
    ]


def generate_exercises(dates):
    """
    Generate exercise-0.json with realistic exercise sessions.
    startTime must be ISO format (YYYY-MM-DDTHH:MM:SS.000) so the dashboard can parse it.
    """
    exercises = []
    log_id_base = 74800000000

    for idx, (day_off, act, type_id, start_h, start_m, dur_min,
               avg_hr, peak_hr, dist_km, steps, cal_per_min) in enumerate(EXERCISE_SCHEDULE):

        date      = dates[day_off]
        start_dt  = datetime(date.year, date.month, date.day, start_h, start_m, 0)
        end_dt    = start_dt + timedelta(minutes=dur_min)
        dur_ms    = dur_min * 60 * 1000

        # Natural variation in metrics
        actual_avg_hr  = avg_hr  + random.randint(-4, 4)
        actual_peak_hr = peak_hr + random.randint(-3, 5)
        actual_calories= int(dur_min * cal_per_min * random.uniform(0.92, 1.08))
        actual_dist    = round(dist_km * random.uniform(0.96, 1.04), 3) if dist_km > 0 else 0.0
        actual_steps   = int(steps * random.uniform(0.95, 1.05)) if steps > 0 else 0

        hr_zones = build_hr_zones_for_exercise(dur_min, actual_avg_hr, actual_peak_hr)

        # Activity levels (sedentary = transition, rest are active phases)
        sedentary_mins = max(1, int(dur_min * 0.08))
        lightly_mins   = max(1, int(dur_min * 0.12))
        fairly_mins    = int(dur_min * 0.35)
        very_mins      = dur_min - sedentary_mins - lightly_mins - fairly_mins

        entry = {
            "logId":            log_id_base + idx * 10000 + random.randint(0, 9999),
            "activityName":     act,
            "activityTypeId":   type_id,
            "logType":          "tracker",
            "startTime":        start_dt.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "originalStartTime":start_dt.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "endTime":          end_dt.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "duration":         dur_ms,
            "activeDuration":   int(dur_ms * 0.95),
            "lastModified":     start_dt.strftime("%m/%d/%y %H:%M:%S"),
            "calories":         actual_calories,
            "steps":            actual_steps,
            "distance":         actual_dist,
            "distanceUnit":     "Kilometer",
            "averageHeartRate": actual_avg_hr,
            "speed":            round(actual_dist / (dur_min / 60), 2) if actual_dist > 0 else 0.0,
            "pace":             int((dur_min * 60 / actual_dist) * 1000) if actual_dist > 0 else 0,
            "elevationGain":    round(random.uniform(0, 45), 1) if act in ("Run", "Walk", "Cycling") else 0.0,
            "hasGps":           act in ("Run", "Walk", "Cycling"),
            "shouldFetchDetails": False,
            "hasActiveZoneMinutes": True,
            "activityLevel": [
                {"minutes": sedentary_mins, "name": "sedentary"},
                {"minutes": lightly_mins,   "name": "lightly"},
                {"minutes": fairly_mins,    "name": "fairly"},
                {"minutes": very_mins,      "name": "very"},
            ],
            "heartRateZones": hr_zones,
            "activeZoneMinutes": {
                "totalMinutes": hr_zones[1]["minutes"] + hr_zones[2]["minutes"] * 2 + hr_zones[3]["minutes"] * 2,
                "minutesInHeartRateZones": [
                    {"minutes": hr_zones[1]["minutes"], "zoneName": "Fat Burn",  "order": 1, "type": "FAT_BURN",  "minuteMultiplier": 1},
                    {"minutes": hr_zones[2]["minutes"], "zoneName": "Cardio",    "order": 2, "type": "CARDIO",    "minuteMultiplier": 2},
                    {"minutes": hr_zones[3]["minutes"], "zoneName": "Peak",      "order": 3, "type": "PEAK",      "minuteMultiplier": 2},
                ]
            },
            "source": {
                "type":   "tracker",
                "name":   "Charge 6",
                "id":     "344403481",
                "url":    "https://www.fitbit.com/",
                "trackerFeatures": ["GPS", "VO2_MAX", "PACE", "DISTANCE", "STEPS", "CALORIES", "HEARTRATE"],
            },
            "manualValuesSpecified": {
                "calories": False,
                "distance": False,
                "steps":    False,
            }
        }

        # Remove speed/pace for non-distance activities
        if actual_dist == 0.0:
            entry.pop("speed", None)
            entry.pop("pace", None)
            entry.pop("elevationGain", None)

        exercises.append(entry)

    return exercises


def generate_user_exercises_csv(exercises):
    """
    Generate UserExercises_2026-01-20.csv in the new Google Takeout format.
    Dashboard reads: exercise_start, exercise_end, activity_name,
                     tracker_total_calories, tracker_total_steps,
                     tracker_total_distance_mm, tracker_avg_heart_rate,
                     tracker_peak_heart_rate
    """
    rows = []
    base_id = 9900000000

    for i, ex in enumerate(exercises):
        start_raw  = ex["startTime"]
        end_raw    = ex["endTime"]
        # Convert "YYYY-MM-DDTHH:MM:SS.000" → "YYYY-MM-DD HH:MM:SS+0000"
        start_iso  = start_raw.replace("T", " ").replace(".000", "") + "+0000"
        end_iso    = end_raw.replace("T", " ").replace(".000", "") + "+0000"
        created_iso = start_iso

        dist_mm    = int(ex.get("distance", 0) * 1_000_000)  # km → mm

        rows.append({
            "exercise_id":              base_id + i,
            "exercise_start":           start_iso,
            "exercise_end":             end_iso,
            "utc_offset":               "+01:00",
            "exercise_created":         created_iso,
            "exercise_last_updated":    created_iso,
            "activity_name":            ex["activityName"],
            "log_type":                 "TRACKER",
            "distance_units":           "METRIC",
            "tracker_total_calories":   ex["calories"],
            "tracker_total_steps":      ex["steps"],
            "tracker_total_distance_mm":dist_mm,
            "tracker_total_altitude_mm":"",
            "tracker_avg_heart_rate":   ex["averageHeartRate"],
            "tracker_peak_heart_rate":  ex["averageHeartRate"] + random.randint(15, 30),
            "tracker_avg_pace_mm_per_second":   "",
            "tracker_avg_speed_mm_per_second":  "",
            "tracker_peak_speed_mm_per_second": "",
            "tracker_auto_stride_run_mm":  "",
            "tracker_auto_stride_walk_mm": "",
            "tracker_swim_lengths":     "",
            "tracker_pool_length":      "",
            "tracker_pool_length_unit": "",
            "tracker_cardio_load":      "",
            "manually_logged_total_calories":  "",
            "manually_logged_total_steps":     "",
            "manually_logged_total_distance_mm": "",
            "manually_logged_pool_length":     "",
            "manually_logged_pool_length_unit":"",
            "pool_length":       "",
            "pool_length_unit":  "",
            "intervals":         "",
            "events":            "",
            "activity_type_probabilities": "",
            "deletion_reason":   "",
            "activity_label":    "",
            "reconciliation_status": "",
        })

    return rows


def generate_profile():
    """Generate Profile.csv for Alex Dubois."""
    return {
        "id":                    "DEMO001",
        "full_name":             DEMO_NAME,
        "first_name":            DEMO_FIRST,
        "last_name":             DEMO_LAST,
        "display_name_setting":  "name",
        "display_name":          DEMO_NAME,
        "username":              "null",
        "email_address":         "alex.dubois@demo.example",
        "date_of_birth":         DEMO_DOB,
        "child":                 "false",
        "country":               "null",
        "state":                 "null",
        "city":                  "null",
        "timezone":              "Europe/London",
        "locale":                "en_US",
        "member_since":          DEMO_MEMBER,
        "about_me":              "null",
        "start_of_week":         "MONDAY",
        "sleep_tracking":        "Normal",
        "time_display_format":   "24hour",
        "gender":                DEMO_GENDER,
        "height":                DEMO_HEIGHT_CM,
        "weight":                DEMO_WEIGHT_KG,
        "stride_length_walking": 78.0,
        "stride_length_running": 118.0,
        "weight_unit":           "METRIC",
        "distance_unit":         "METRIC",
        "height_unit":           "METRIC",
        "water_unit":            "en_US",
        "glucose_unit":          "en_US",
        "swim_unit":             "METRIC",
    }


def repack_zip():
    """Repack Demo_data/Fitbit into Demo_data/Fitbit.zip"""
    zip_path = os.path.join(os.path.dirname(BASE_DIR), "Fitbit.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BASE_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                arcname   = os.path.relpath(full_path, os.path.dirname(BASE_DIR))
                zf.write(full_path, arcname)
    print(f"Repacked ZIP: {zip_path}  ({os.path.getsize(zip_path) // 1024} KB)")


def main():
    # Ensure directories exist
    for d in [EXPORT_DIR, HRV_DIR, SPO2_DIR, STRESS_DIR, SLEEP_SCORE_DIR, PROFILE_DIR, EXERCISES_DIR]:
        os.makedirs(d, exist_ok=True)

    dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

    # 1. Sleep data (needed first so HR generation can reference sleep windows)
    sleep_entries, sleep_infos = generate_sleep_data(dates)
    print(f"Sleep: {len(sleep_entries)} entries ({sum(1 for s in sleep_entries if s['mainSleep'])} main, "
          f"{sum(1 for s in sleep_entries if not s['mainSleep'])} naps)")

    # 2. Per-day heart rate files (fluid + exercise-aware)
    for i, date in enumerate(dates):
        sleep_info = sleep_infos.get(date, {
            "start_time": datetime(date.year, date.month, date.day, 23, 0, 0),
            "end_time":   datetime(date.year, date.month, date.day, 6, 30, 0) + timedelta(days=1),
            "duration_ms": 7.5 * 3600 * 1000,
        })
        hr_data  = generate_heart_rate_for_day(date, sleep_info, i)
        filename = f"heart_rate-{date.strftime('%Y-%m-%d')}.json"
        with open(os.path.join(EXPORT_DIR, filename), "w") as f:
            json.dump(hr_data, f, indent=2)
    print(f"Heart rate: {DAYS} daily files")

    # 3. Steps + calories
    steps_data, calories_data, daily_steps = generate_steps_calories_data(dates, sleep_infos)
    with open(os.path.join(EXPORT_DIR, "steps-2026-01-20.json"), "w") as f:
        json.dump(steps_data, f, indent=2)
    with open(os.path.join(EXPORT_DIR, "calories-2026-01-20.json"), "w") as f:
        json.dump(calories_data, f, indent=2)
    avg_steps = sum(daily_steps.values()) / DAYS
    print(f"Steps/calories: avg {avg_steps:.0f} steps/day")

    # 4. Sleep JSON
    with open(os.path.join(EXPORT_DIR, "sleep-2026-01-20.json"), "w") as f:
        json.dump(sleep_entries, f, indent=2)

    # 5. Resting HR
    resting_hr = generate_resting_hr_data(dates)
    with open(os.path.join(EXPORT_DIR, "resting_heart_rate-2026-01-20.json"), "w") as f:
        json.dump(resting_hr, f, indent=2)
    avg_rhr = sum(r["value"]["value"] for r in resting_hr) / len(resting_hr)
    print(f"Resting HR: avg {avg_rhr:.1f} bpm")

    # 6. HR zones (per-day files)
    hr_zones = generate_heart_rate_zones(dates)
    for i, date in enumerate(dates):
        filename = f"time_in_heart_rate_zones-{date.strftime('%Y-%m-%d')}.json"
        with open(os.path.join(EXPORT_DIR, filename), "w") as f:
            json.dump([hr_zones[i]], f, indent=2)

    # 7. HRV CSV
    hrv_data = generate_hrv_csv(dates)
    with open(os.path.join(HRV_DIR, "Daily Heart Rate Variability Summary - 2026-01-20.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "rmssd", "nremhr", "entropy"])
        writer.writeheader()
        writer.writerows(hrv_data)
    avg_rmssd = sum(r["rmssd"] for r in hrv_data) / len(hrv_data)
    print(f"HRV: avg RMSSD {avg_rmssd:.1f} ms")

    # 8. SpO2 CSV
    spo2_data = generate_spo2_csv(dates)
    with open(os.path.join(SPO2_DIR, "Daily SpO2 - 2026-01-20-2026-02-02.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "average_value", "lower_bound", "upper_bound"])
        writer.writeheader()
        writer.writerows(spo2_data)
    avg_spo2 = sum(s["average_value"] for s in spo2_data) / len(spo2_data)
    print(f"SpO2: avg {avg_spo2:.1f}%")

    # 9. Stress CSV
    stress_data = generate_stress_csv(dates)
    with open(os.path.join(STRESS_DIR, "Stress Score.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "DATE", "UPDATED_AT", "STRESS_SCORE",
            "SLEEP_POINTS", "MAX_SLEEP_POINTS",
            "RESPONSIVENESS_POINTS", "MAX_RESPONSIVENESS_POINTS",
            "EXERTION_POINTS", "MAX_EXERTION_POINTS",
            "STATUS", "CALCULATION_FAILED",
        ])
        writer.writeheader()
        writer.writerows(stress_data)
    scores = [s["STRESS_SCORE"] for s in stress_data]
    print(f"Stress/readiness: range {min(scores)}-{max(scores)}")

    # 10. Sleep scores CSV
    sleep_score_data = generate_sleep_score_csv(sleep_entries)
    with open(os.path.join(SLEEP_SCORE_DIR, "sleep_score.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sleep_log_entry_id", "timestamp", "overall_score",
            "composition_score", "revitalization_score", "duration_score",
            "deep_sleep_in_minutes", "resting_heart_rate", "restlessness",
        ])
        writer.writeheader()
        writer.writerows(sleep_score_data)
    s_scores = [s["overall_score"] for s in sleep_score_data]
    print(f"Sleep scores: range {min(s_scores)}-{max(s_scores)}")

    # 11. Profile CSV
    profile = generate_profile()
    with open(os.path.join(PROFILE_DIR, "Profile.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(profile.keys()))
        writer.writeheader()
        writer.writerow(profile)

    # 12. Exercises — JSON (exercise-0.json)
    exercises = generate_exercises(dates)
    with open(os.path.join(EXPORT_DIR, "exercise-0.json"), "w") as f:
        json.dump(exercises, f, indent=2)
    print(f"\nExercises: {len(exercises)} sessions")
    for ex in exercises:
        print(f"  {ex['startTime'][:10]}  {ex['activityName']:<16}  {ex['duration']//60000:>3}min  "
              f"avg HR {ex['averageHeartRate']} bpm  {ex.get('distance', 0):.1f}km  "
              f"{ex['calories']} kcal")

    # 13. UserExercises CSV
    ue_rows = generate_user_exercises_csv(exercises)
    ue_fields = [
        "exercise_id", "exercise_start", "exercise_end", "utc_offset",
        "exercise_created", "exercise_last_updated", "activity_name",
        "log_type", "distance_units",
        "tracker_total_calories", "tracker_total_steps", "tracker_total_distance_mm",
        "tracker_total_altitude_mm", "tracker_avg_heart_rate", "tracker_peak_heart_rate",
        "tracker_avg_pace_mm_per_second", "tracker_avg_speed_mm_per_second",
        "tracker_peak_speed_mm_per_second", "tracker_auto_stride_run_mm",
        "tracker_auto_stride_walk_mm", "tracker_swim_lengths", "tracker_pool_length",
        "tracker_pool_length_unit", "tracker_cardio_load",
        "manually_logged_total_calories", "manually_logged_total_steps",
        "manually_logged_total_distance_mm", "manually_logged_pool_length",
        "manually_logged_pool_length_unit", "pool_length", "pool_length_unit",
        "intervals", "events", "activity_type_probabilities",
        "deletion_reason", "activity_label", "reconciliation_status",
    ]
    with open(os.path.join(EXERCISES_DIR, "UserExercises_2026-01-20.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ue_fields)
        writer.writeheader()
        writer.writerows(ue_rows)
    print(f"UserExercises CSV: {len(ue_rows)} rows")

    # 14. HR fluidity sanity check
    print("\n" + "=" * 55)
    print("HR fluidity check (heart_rate-2026-01-22.json):")
    sample = os.path.join(EXPORT_DIR, "heart_rate-2026-01-22.json")
    with open(sample) as f:
        hr_data = json.load(f)
    changes = [abs(hr_data[i]["value"]["bpm"] - hr_data[i-1]["value"]["bpm"]) for i in range(1, min(200, len(hr_data)))]
    c = Counter(changes)
    total = len(changes)
    print(f"  0 bpm: {c[0]} ({c[0]/total*100:.0f}%)")
    print(f"  1 bpm: {c[1]} ({c[1]/total*100:.0f}%)")
    print(f"  2 bpm: {c[2]} ({c[2]/total*100:.0f}%)")
    print(f"  3+ bpm: {sum(v for k,v in c.items() if k >= 3)}")
    print(f"  avg change: {sum(changes)/total:.2f} bpm")
    print("=" * 55)

    # 15. Repack ZIP
    repack_zip()
    print("\nDone. Upload Demo_data/Fitbit.zip to test the dashboard.")


if __name__ == "__main__":
    main()
