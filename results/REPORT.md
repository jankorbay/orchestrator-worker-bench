# Opus brain + fast workers — results

Boss in all arms: `opus` @ high. arm A: opus @ medium workers; arm B: haiku @ xhigh workers; arm C: haiku @ high workers; arm D: haiku @ medium workers; arm E: sonnet @ high workers. Runs: a-1, a-2, a-3, b-1, b-2, b-3, c-1, c-2, c-3, d-1, d-2, d-3, e-1, e-2, e-3.

## Verdict (each arm vs baseline A)

- **B: supported**: same accuracy (within 2 points) and B was cheaper; accuracy +0.0 points, wall time +42%, cost -55% (B vs A). Based on 3 vs 3 runs.
- **C: supported**: same accuracy (within 2 points) and C was cheaper; accuracy -0.1 points, wall time +23%, cost -58% (C vs A). Based on 3 vs 3 runs.
- **D: supported**: same accuracy (within 2 points) and D was cheaper; accuracy -0.1 points, wall time +9%, cost -57% (D vs A). Based on 3 vs 3 runs.
- **E: supported**: same accuracy (within 2 points) and E was cheaper; accuracy -0.1 points, wall time +12%, cost -17% (E vs A). Based on 3 vs 3 runs.

Check the min–max ranges below: if they overlap a lot, the difference may be noise.

## Summary (mean, min–max over runs)

| Arm | Runs | Accuracy | Wall time (min) | Slowest task (min) | Cost, API-equivalent ($) | Output tokens (k) | Send-backs per run |
|---|---|---|---|---|---|---|---|
| A: opus @ medium workers | 3 | 100.0 (100.0–100.0)% | 6.0 (5.6–6.4) | 2.9 (2.3–3.7) | 6.29 (5.60–6.94) | 154 (142–167) | 0.7 (0.0–1.0) |
| B: haiku @ xhigh workers | 3 | 100.0 (100.0–100.0)% | 8.5 (7.8–9.4) | 5.9 (5.1–6.8) | 2.86 (2.58–3.18) | 687 (676–696) | 0.3 (0.0–1.0) |
| C: haiku @ high workers | 3 | 99.9 (99.7–100.0)% | 7.3 (6.8–7.6) | 3.9 (3.4–4.3) | 2.66 (2.35–3.07) | 441 (430–458) | 1.0 (0.0–2.0) |
| D: haiku @ medium workers | 3 | 99.9 (99.7–100.0)% | 6.5 (6.5–6.6) | 2.9 (2.3–3.7) | 2.71 (2.46–2.93) | 294 (287–308) | 2.3 (1.0–3.0) |
| E: sonnet @ high workers | 3 | 99.9 (99.7–100.0)% | 6.7 (6.3–6.9) | 2.3 (2.2–2.5) | 5.20 (4.84–5.62) | 196 (189–208) | 2.0 (2.0–2.0) |

Workers run in parallel, so wall time ≈ slowest task + the boss's own planning and review. A send-back is the boss rejecting a worker's result and spawning a new attempt.

## Per task (mean over runs)

| Task | Do-nothing score | A: opus @ medium workers: accuracy | B: haiku @ xhigh workers: accuracy | C: haiku @ high workers: accuracy | D: haiku @ medium workers: accuracy | E: sonnet @ high workers: accuracy | A: attempts | B: attempts | C: attempts | D: attempts | E: attempts | A: worker time (s) | B: worker time (s) | C: worker time (s) | D: worker time (s) | E: worker time (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01-bugfix | 54% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 28 (26–29) | 53 (52–55) | 29 (28–31) | 20 (18–23) | 18 (17–19) |
| 02-write-tests | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 68 (50–102) | 273 (219–306) | 170 (163–175) | 91 (62–108) | 78 (58–100) |
| 03-refactor | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 43 (40–46) | 111 (96–119) | 60 (49–69) | 35 (30–42) | 31 (28–37) |
| 04-feature | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 49 (43–55) | 112 (91–136) | 64 (62–66) | 28 (27–31) | 31 (27–34) |
| 05-cron | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 82 (76–93) | 246 (236–256) | 166 (137–189) | 86 (73–98) | 81 (58–121) |
| 06-security-review | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 22 (20–24) | 34 (29–42) | 14 (12–16) | 10 (10–11) | 16 (14–19) |
| 07-root-cause | 29% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 91 (71–101) | 210 (184–244) | 132 (126–136) | 89 (77–103) | 65 (58–73) |
| 08-concurrency | 33% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.7 (1.0–2.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.3 (1.0–2.0) | 1.0 (1.0–1.0) | 171 (137–223) | 323 (219–411) | 166 (139–179) | 89 (52–113) | 96 (86–107) |
| 09-api-migration | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 2.0 (1.0–3.0) | 2.0 (2.0–2.0) | 98 (95–102) | 219 (195–242) | 151 (143–162) | 127 (116–148) | 110 (98–119) |
| 10-datetime-migration | 43% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.3 (1.0–2.0) | 1.0 (1.0–1.0) | 1.7 (1.0–2.0) | 93 (86–100) | 277 (209–327) | 160 (124–195) | 83 (77–87) | 105 (89–128) |
| 11-envfile | 21% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.7 (1.0–2.0) | 1.0 (1.0–1.0) | 91 (85–100) | 277 (248–298) | 196 (176–226) | 171 (136–224) | 108 (94–130) |
| 12-stock-drift | 9% | 100 (100–100)% | 100 (100–100)% | 98 (96–100)% | 98 (96–100)% | 98 (96–100)% | 1.0 (1.0–1.0) | 1.3 (1.0–2.0) | 1.7 (1.0–2.0) | 1.3 (1.0–2.0) | 1.3 (1.0–2.0) | 103 (94–109) | 324 (289–392) | 224 (168–261) | 104 (88–112) | 119 (93–135) |
| 13-config-v2 | 0% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 100 (100–100)% | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 1.0 (1.0–1.0) | 122 (109–141) | 248 (241–254) | 181 (163–204) | 126 (116–145) | 135 (125–150) |

## Cost by model (mean $ per run)

| Arm | haiku-5-5 | opus-5-5 | sonnet-5-5 |
|---|---|---|---|
| A: opus @ medium workers | 0.00 | 6.29 | 0.00 |
| B: haiku @ xhigh workers | 0.55 | 2.31 | 0.00 |
| C: haiku @ high workers | 0.33 | 2.33 | 0.00 |
| D: haiku @ medium workers | 0.22 | 2.49 | 0.00 |
| E: sonnet @ high workers | 0.00 | 2.34 | 2.85 |

## Run problems

- a-2: 1 blocked shell commands
- d-1: 2 blocked shell commands
- d-2: 3 blocked shell commands
- e-1: 4 blocked shell commands
- e-3: 4 blocked shell commands
