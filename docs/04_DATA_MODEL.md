# 04 — Data Model

## Data Model Principle

The MVP should use a simple rule-based data model.

The data model can include small AI-ready fields, but the app must work without AI.

## Core Entities

| Entity | Purpose | MVP |
|---|---|---|
| UserProfile | Stores user preferences and constraints | Yes |
| Exercise | Stores exercises and alternatives | Yes |
| WorkoutTemplate | Stores reusable workout structures | Yes |
| WorkoutSession | Stores selected/generated workout | Yes |
| WorkoutCompletion | Stores completed workouts | Yes |
| FeedbackEntry | Stores post-workout feedback | Yes |
| AISettings | Future optional AI settings | No |
| AIRequestLog | Future AI request log | No |

## UserProfile

```json
{
  "id": "user_001",
  "fitness_level": "beginner",
  "main_goal": "build_habit",
  "minimum_time_minutes": 3,
  "available_space": "yoga_mat",
  "quiet_workouts_required": true,
  "equipment": ["yoga_mat"],
  "sensitive_areas": ["knees"],
  "ai_enabled": false,
  "created_at": "2026-06-02T10:00:00Z",
  "updated_at": "2026-06-02T10:00:00Z"
}
```

## Exercise

```json
{
  "id": "ex_wall_pushup",
  "name": "Wall Push-up",
  "description": "A beginner-friendly push-up variation using a wall.",
  "instructions": [
    "Stand facing a wall.",
    "Place your hands on the wall at chest height.",
    "Bend your elbows slowly.",
    "Push back gently."
  ],
  "difficulty": "beginner",
  "target_areas": ["chest", "arms", "core"],
  "movement_type": "strength",
  "equipment_required": [],
  "space_required": "yoga_mat",
  "noise_level": "quiet",
  "impact_level": "low",
  "default_duration_seconds": 45,
  "default_reps": null,
  "easier_alternative_id": null,
  "harder_alternative_id": "ex_incline_pushup",
  "avoid_if_sensitive_areas": ["wrists", "shoulders"],
  "safety_notes": [
    "Stop if you feel wrist or shoulder pain."
  ],
  "tags": ["upper_body", "beginner", "quiet", "no_equipment"],
  "ai_allowed": true,
  "risk_level": "low"
}
```

## WorkoutTemplate

```json
{
  "id": "wt_minimum_full_body",
  "name": "Minimum Full Body",
  "workout_type": "minimum",
  "target_duration_minutes": 3,
  "difficulty": "very_easy",
  "required_blocks": ["warmup", "strength", "cooldown"],
  "quiet_required": true,
  "low_impact_required": true,
  "description": "A short workout for difficult days."
}
```

## WorkoutSession

```json
{
  "id": "ws_001",
  "user_id": "user_001",
  "template_id": "wt_minimum_full_body",
  "title": "3-Minute Gentle Session",
  "workout_type": "minimum",
  "estimated_duration_minutes": 3,
  "generated_by": "rule_based",
  "is_comeback_session": false,
  "exercises": [
    {
      "exercise_id": "ex_wall_pushup",
      "order": 1,
      "duration_seconds": 45,
      "reps": null,
      "rest_after_seconds": 15
    }
  ],
  "created_at": "2026-06-02T10:00:00Z"
}
```

## WorkoutCompletion

```json
{
  "id": "wc_001",
  "user_id": "user_001",
  "workout_session_id": "ws_001",
  "completed_at": "2026-06-02T10:15:00Z",
  "completed_duration_minutes": 3,
  "workout_type": "minimum",
  "is_comeback_session": false,
  "was_minimum_workout": true,
  "exercises_completed": 4,
  "exercises_skipped": 0,
  "alternatives_used": 1,
  "ai_assisted": false
}
```

## FeedbackEntry

```json
{
  "id": "fb_001",
  "user_id": "user_001",
  "workout_completion_id": "wc_001",
  "perceived_difficulty": "okay",
  "energy_before": "low",
  "energy_after": "better",
  "mood_after": "calm",
  "notes": null
}
```

## Enums

### fitness_level

```txt
beginner
some_experience
intermediate
```

### workout_type

```txt
minimum
standard
extended
comeback
mobility
recovery
```

### generated_by

```txt
rule_based
manual
ai_assisted
```

### difficulty

```txt
very_easy
beginner
easy
moderate
challenging
```

### movement_type

```txt
strength
mobility
cardio_low_impact
cardio_high_impact
balance
stretching
warmup
cooldown
```

### space_required

```txt
yoga_mat
small_room
large_room
```

### noise_level

```txt
quiet
moderate
noisy
```

### impact_level

```txt
low
medium
high
```

### risk_level

```txt
low
medium
high
```

## Rule-Based Workout Generation

Basic logic:

```txt
get user profile
filter exercises by equipment
filter exercises by space
filter exercises by noise level
filter exercises by sensitive areas
choose template based on user state
select exercises matching template blocks
include easier alternatives
return workout session
```

## AI Compatibility Notes

These fields are AI-ready but do not require AI now:

- `ai_enabled`
- `ai_allowed`
- `risk_level`
- `generated_by`
- `ai_assisted`

Future AI should only select from approved exercises where:

```txt
ai_allowed = true
risk_level != high
```

AI-generated workouts should later pass a rule-based safety validator before being shown.
