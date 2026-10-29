"""Methods published in Garmin's official client README, grouped by parameter shape."""

RANGES = {
    "stress": "get_daily_stress",
    "steps": "get_daily_steps",
    "hydration": "get_daily_hydration",
    "weight_goals": "get_effective_weight_goals",
    "weight": "get_weight_measurements",
    "sleep_summaries": "get_daily_sleep_summaries",
    "body_battery": "get_daily_body_battery",
    "daily_summaries": "get_daily_summaries",
    "hrv_summaries": "get_daily_hrv_summaries",
    "wellness_activity": "get_wellness_activity_summaries",
}
DAYS = {
    "food": "get_daily_food_logs",
    "sleep": "get_daily_sleep",
    "heart_rate": "get_daily_heart_rate",
    "hrv": "get_daily_hrv",
    "menstrual_summary": "get_menstrual_cycle_summary",
    "fitness_age": "get_fitness_age",
    "spo2": "get_daily_spo2",
}
ACCOUNT = {
    "profile": "get_user_profile_settings",
    "heart_rate_zones": "get_heart_rate_zones",
}
