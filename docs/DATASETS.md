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

Original fields are not selectively removed from API results; JSON is reserialized and is not a byte-for-byte copy of the HTTP body. Requests for naps, respiration, recovery, training, or other unspecified endpoints were not independently verified. Some fields may appear within the above results. The Swagger index additionally lists GET /usersummary-service/usersummary/daily and GET /weight-service/weight/all/{startDate}/{endDate}; they are not yet implemented because parameter and response details remain unverified. Data availability and range limits need live testing.

Contract source: [Garmin client 1.0.0](https://github.com/garmin/connect-personal-api-python/blob/main/src/garmin_personal_api/client.py). Its wrappers return arbitrary JSON (or null for an empty body), except activity download returns ZIP bytes; only daily summaries explicitly documents an object with a data array. Range endpoints are inclusive; the client does not specify maximum range sizes or activity page caps. Activity search accepts start, limit, startDate, endDate and optional activityType. The exporter requests unfiltered activities. The generic GET method supports query parameters, but does not itself establish an undocumented endpoint's contract.

The [Swagger page](https://developer.garmin.com/gc-developer-program/personal/swagger-docs/) returned only a page shell in the web reader; direct retrieval from this environment failed DNS resolution. Its OpenAPI document and the parameters and response shapes of the two additional routes above remain unverified. This registry is therefore a wrapper inventory, not a complete OpenAPI endpoint inventory.
