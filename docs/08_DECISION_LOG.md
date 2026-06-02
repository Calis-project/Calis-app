# 08 — Decision Log

Use this file to track important product and technical decisions.

## Decision 001 — Build Rule-Based MVP First

### Status

Accepted

### Context

The product may include AI in the future, but the first goal is to validate the habit system.

### Decision

Build the MVP without AI.

The MVP will use:

- exercise database
- rule-based filtering
- workout templates
- Comeback Mode
- Return Chain
- progress tracking

### Reason

This keeps the first version simple, testable, and safer.

AI can be added later as an optional layer.

## Decision 002 — Keep AI Future-Compatible

### Status

Accepted

### Context

The app may later include AI workout adaptation and comeback coaching.

### Decision

The data model may include small AI-ready fields such as:

- `ai_enabled`
- `ai_allowed`
- `generated_by`
- `ai_assisted`
- `risk_level`

### Reason

These fields make future AI integration easier without requiring AI now.

## Decision 003 — Comeback Mode Is Core

### Status

Accepted

### Context

Many users stop fitness routines after missing days.

### Decision

Comeback Mode is a core MVP feature.

### Reason

The product should be differentiated by helping users return, not only by giving workouts.

## Decision 004 — Return Chain Instead of Strict Streak

### Status

Accepted

### Context

Traditional streaks can create guilt when broken.

### Decision

Use Return Chain to reward coming back after missed days.

### Reason

This better supports the product philosophy of realistic consistency.

## Decision 005 — AI Should Select from Approved Exercises

### Status

Future accepted

### Context

Future AI-generated workouts could create safety risks.

### Decision

AI should not freely invent exercises.

Future AI should select or adapt from the approved exercise database.

### Reason

This keeps AI suggestions safer and easier to validate.
