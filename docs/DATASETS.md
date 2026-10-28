# Dataset registry and limitations

The registry uses published wrapper names in Garmin's official client. The table describes requested data, not a guarantee that Garmin returns it for a given account.

| Category | Wrapper | Parameters |
|---|---|---|
| stress | get_daily_stress | start, end |
| steps | get_daily_steps | start, end |
| hydration | get_daily_hydration | start, end |
| weight_goals | get_effective_weight_goals | start, end |
| weight | get_weight_measurements | start, end |
| sleep_summaries | get_daily_sleep_summaries | start, end |
| body_battery | get_daily_body_battery | start, end |
| daily_summaries | get_daily_summaries | start, end |
| hrv_summaries | get_daily_hrv_summaries | start, end |
| wellness_activity | get_wellness_activity_summaries | start, end |
| food | get_daily_food_logs | date |
| sleep | get_daily_sleep | date |
| heart_rate | get_daily_heart_rate | date |
| hrv | get_daily_hrv | date |
| menstrual_summary | get_menstrual_cycle_summary | date |
| menstrual_day | get_menstrual_cycle_day_view | date, today date |
| fitness_age | get_fitness_age | date |
| spo2 | get_daily_spo2 | date |
| profile | get_user_profile_settings | none |
| heart_rate_zones | get_heart_rate_zones | none |
| activities | search_activities, get_activity, get_activity_workouts, download_activity | date range, offset; activity ID |

Original fields are not selectively removed from API results; JSON is reserialized and is not a byte-for-byte copy of the HTTP body. Requests for naps, respiration, recovery, training, or other unspecified endpoints were not independently verified. Some fields may appear within the above results. Coverage of Garmin Swagger remains unknown. Data availability and range limits need live testing.
