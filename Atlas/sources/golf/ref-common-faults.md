---
categories:
  - sources
type: reference
created: 2026-04-13
updated: 2026-06-11
status: active
confidence: high
tags:
  - topic/swing-faults
  - topic/diagnosis
  - topic/drills
aliases: [common-faults, swing-faults, fault-diagnosis]
related: ["[[ref-biomechanics]]", "[[golf-moc]]"]
---

# Reference: Common Swing Fault Diagnosis and Correction Protocols

**Last Updated:** April 13, 2026
**Sources:** TPI research database, TrackMan official data (2024), Adam Young Golf, HackMotion research, EJS Golf biomechanics, Golf Smart Academy, peer-reviewed motor learning studies (Nature Scientific Reports 2024), SAM PuttLab data
**Refresh Cadence:** Every 6 months or when the user's primary swing faults change
**Built by:** Claude deep research (12+ source searches)

**Purpose:** Unified fault diagnosis reference connecting biomechanical cause chains to TrackMan signatures, TPI physical screens, corrective drills, and realistic correction timelines. Loaded by `/golf` before every practice plan and swing analysis session.

---

## Key Takeaways

1. **Early extension is the master fault.** It cascades into shanks, fat/thin shots, blocks, hooks, inconsistent low point, and elevated spin. Fixing early extension resolves or reduces multiple downstream faults simultaneously. Approximately 70% of amateur golfers exhibit early extension.

2. **Face angle controls 75-85% of start direction; face-to-path controls curvature.** Every directional fault reduces to these two numbers. Fix face first, then path -- never the reverse.

3. **Physical limitations cause swing faults, not the other way around.** Limited hip IR (<30 deg) forces early extension. Limited T-spine rotation forces OTT. Limited ankle dorsiflexion degrades GRF production and posture. The TPI screen identifies the root; the drill addresses the symptom.

4. **Grip and swing must change together.** Moving from weak to strong grip without path adjustment converts a slice into a hook. The grip sets the face angle baseline; the swing determines path. Changing one without the other creates a two-way miss.

5. **Shanks are strike faults, not face/path faults.** TrackMan path data can look normal on a shank. The diagnostic is impact location (hosel) caused by the club being pushed outward when early extension removes the space for a proper hand path.

6. **Low point is the most underrated skill differentiator.** Tour players' low point is 3-4 inches after the ball with irons. Mid-handicappers vary by 4-6 inches swing to swing. Weight shift and wrist flexion are the two biggest low point influences.

7. **Correction timelines are real.** Simple setup changes take 1-2 weeks. Grip changes take 3-4 weeks to feel natural. Movement pattern changes (early extension, OTT, casting) take 6-12 weeks of focused practice. Deep-rooted faults in experienced players take 3-6 months.

8. **Fault cascades flow downhill.** Physical limitation --> primary fault (early extension, poor rotation) --> secondary faults (casting, OTT, shank) --> ball flight symptoms (slice, hook, fat/thin). Fix upstream, not downstream.

9. **Random/interleaved practice produces 25-40% better retention than block practice** despite worse performance during the session. Structure corrective practice as interleaved drill circuits, not repetitive block work.

10. **Every fault has a TrackMan signature.** If you have launch monitor access, diagnosis is objective. Without it, impact tape and ball flight provide 80% of the diagnostic information needed.

---

## Fault Cascade Map

This map shows how physical limitations cascade through primary faults into secondary faults and finally into ball flight symptoms. Fix upstream -- treating symptoms downstream produces temporary relief that reverts under pressure.

```
PHYSICAL LIMITATIONS (Root Causes)
|
+-- Limited Hip IR (<30 deg)
|   +-- EARLY EXTENSION (Primary Fault)
|   |   +-- Shank (hosel pushed into ball path)
|   |   +-- Fat/thin (inconsistent low point)
|   |   +-- Block right (arms get stuck behind body)
|   |   +-- Hook left (compensatory flip to save the shot)
|   |   +-- Loss of posture (stand-up through impact)
|   |   +-- Casting (arms forced to compensate for lost rotation)
|   +-- Sway / Slide (lateral replaces rotational)
|
+-- Limited T-Spine Rotation (<45 deg each way)
|   +-- OVER-THE-TOP (Primary Fault)
|   |   +-- Pull (face square to path, path left)
|   |   +-- Slice (face open to leftward path)
|   |   +-- Steep divots / low point behind ball
|   +-- Reverse Spine Angle (injury risk)
|   +-- Flat Shoulder Plane
|
+-- Limited Trail Shoulder External Rotation (<90 deg)
|   +-- Over-the-top (can't shallow the club)
|   +-- Flat shoulder plane
|
+-- Limited Ankle Dorsiflexion (<15 deg)
|   +-- Early extension (can't maintain posture)
|   +-- Poor GRF production (speed loss)
|   +-- Loss of balance
|
+-- Limited Wrist Extension (<60 deg)
|   +-- Compensatory grip adjustments
|   +-- Casting (can't maintain lag)
|
+-- Weak Glutes / Core
|   +-- Early extension (can't stabilize pelvis)
|   +-- Sway (lateral hip movement in backswing)
|   +-- Slide (lateral hip movement in downswing)
|
+-- Poor Proprioception / Motor Control
    +-- Inconsistent low point
    +-- Variable face control (+/-4 deg vs tour's +/-1 deg)
    +-- Chipping yips (neuromuscular disconnect)

GRIP ISSUES (Setup Root Cause)
|
+-- Too Weak (<2 knuckles visible)
|   +-- Open face at impact
|   +-- Slice / push-fade
|
+-- Too Strong (>3 knuckles visible)
|   +-- Closed face at impact
|   +-- Hook / pull-draw
|
+-- Grip Change Without Path Adjustment
    +-- Overcorrection (slice to hook or hook to slice)
```

---

## 1. Slice

### Biomechanical Cause Chain

The slice results from the clubface being open relative to the club path at impact, creating a positive face-to-path differential that tilts the spin axis rightward (for a right-handed golfer). Two distinct mechanisms produce slices:

**Path-dominant slice (most common):** The downswing is initiated by the upper body rather than the lower body, throwing the club outward (over the top). This produces a negative club path (out-to-in, typically -3 to -8 degrees). Even a relatively square face produces a large face-to-path gap because the path is so far left. The upper body fires first because the lower body lacks the mobility or the motor pattern to lead the sequence.

**Face-dominant slice (less common but more persistent):** The path may be acceptable (near zero or slightly positive), but the face is open at impact. Root causes include a weak grip (<2 knuckles visible on lead hand), insufficient forearm rotation through impact, or a cupped (extended) lead wrist at impact. The wrist sits almost flat at address with a weak grip, giving excessive range of motion to open the face during the swing.

### TrackMan Diagnostic Signature

| Parameter | Path-Dominant Slice | Face-Dominant Slice |
|---|---|---|
| Club Path | -3 to -8 deg (out-to-in) | -1 to +2 deg (near neutral) |
| Face Angle | -1 to +2 deg (may look "ok") | +3 to +6 deg (clearly open) |
| Face-to-Path | +4 to +10 deg | +3 to +6 deg |
| Spin Axis | +8 to +20 deg right | +5 to +12 deg right |
| Attack Angle | Steep, often -6 to -10 deg (irons) | Near normal |
| Dynamic Loft | Elevated (spin loft high) | Elevated |

**Key diagnostic rule:** If path is worse than -3 deg, fix path first. If path is near zero and face-to-path still >+3 deg, fix face.

### TPI Physical Screen

- Limited T-spine rotation (<45 deg each way) -- forces upper body to dominate transition
- Limited trail shoulder external rotation (<90 deg) -- can't shallow the club in transition
- Poor lower body disassociation -- pelvis and torso fire simultaneously

### Corrective Drills

**Drill 1: Headcover Gate (path fix)**
Setup: Place a headcover or water bottle 6 inches outside and 2 inches behind the ball on the target line. Swing without hitting it on the downswing. This externally constrains the out-to-in path by forcing an inside approach. Start with half swings, progress to 75%, then full. Use a 7-iron initially.

**Drill 2: Trail Foot Back (path fix)**
Setup: Drop your trail foot back 4-6 inches from its normal position (closed stance). This tilts the swing plane to promote an in-to-out path. Hit 20 shots per session. Your body learns the feeling of swinging "to right field." Gradually return the trail foot to neutral while maintaining the path feel.

**Drill 3: Motorcycle/Wrist Flexion (face fix)**
Setup: At the top of the backswing, twist the lead hand as if revving a motorcycle throttle -- this moves the lead wrist from extension (cupped) into flexion (bowed). The face rotates from open toward square/closed. Practice in slow motion with mirror feedback. A bowed lead wrist at impact delivers a square or slightly closed face. HackMotion sensor provides real-time wrist angle biofeedback if available.

### Correction Timeline

- **Grip adjustment (weak to neutral):** 2-3 weeks to feel natural, immediate ball flight improvement
- **Path correction (OTT to neutral):** 4-8 weeks with focused practice 3x/week
- **Combined fix:** 6-12 weeks for on-course transfer; expect worse performance in weeks 2-4 before improvement

### Related Faults

- OTT is the upstream cause of most path-dominant slices
- Weak grip is the upstream cause of most face-dominant slices
- A slice with a strong grip likely indicates extreme OTT path compensating for closed face
- Heel strikes amplify slice via gear effect

---

## 2. Hook

### Biomechanical Cause Chain

The hook is the mirror image of the slice: the clubface is closed relative to the club path, creating a negative face-to-path differential that tilts the spin axis leftward. Two mechanisms:

**Path-dominant hook:** The club approaches excessively from the inside (path +4 to +8 degrees in-to-out). Even with a face angle near zero, the large gap between face and path generates heavy draw/hook spin. Common in golfers who overcorrected a slice by strengthening their grip and training an inside path, but went too far. The trail hand dominates the downswing, closing the face further.

**Face-dominant hook (snap hook/duck hook):** The path may be moderate, but the face slams shut through impact. Causes include an excessively strong grip (3+ knuckles, trail hand wrapped under), overpronation of forearms through impact, or an early "flip" where the trail wrist overtakes the lead wrist before impact. When the path is zero or negative, face closure accelerates faster than when the path is 1-2 degrees positive.

### TrackMan Diagnostic Signature

| Parameter | Path-Dominant Hook | Face-Dominant Hook |
|---|---|---|
| Club Path | +4 to +8 deg (in-to-out) | 0 to +2 deg |
| Face Angle | -1 to +1 deg | -3 to -6 deg (slammed shut) |
| Face-to-Path | -4 to -8 deg | -3 to -7 deg |
| Spin Axis | -8 to -18 deg left | -6 to -14 deg left |
| Attack Angle | Often shallow or positive (driver) | Variable |
| Dynamic Loft | Often reduced (delofted) | Reduced (face turning down) |

**Key diagnostic rule:** If path >+4 deg, the path is the problem. If face-to-path <-3 deg with a neutral path, the face is the problem. Target face-to-path between -1 and -3 degrees for a controlled draw.

### TPI Physical Screen

- Excessive hip slide toward target (lateral instead of rotational)
- Limited lead hip IR (trail arm gets "stuck" behind body)
- Poor core stabilization (pelvis outruns the upper body)

### Corrective Drills

**Drill 1: Lead-Hand-Only Swings (face control)**
Setup: Remove the trail hand from the club. Using a short iron (8 or 9), make smooth half swings with only the lead hand. Focus on keeping the lead shoulder turning open through the ball and finishing with the chest facing the target. This removes the trail hand's tendency to overpower and close the face. Hit 15-20 balls per session.

**Drill 2: Alignment Stick Gate (path fix)**
Setup: Place two alignment sticks on the ground creating a "corridor" aligned at the target. The sticks should be shoulder-width apart. Swing so the club exits through the corridor, not excessively to the right. This constrains the overly inside-out path. If the divot points well right of target, the path is too in-to-out.

**Drill 3: Weaken Grip Incrementally**
Setup: Rotate both hands 1/4 turn toward the target (counterclockwise for right-handers). You should see 2-2.5 knuckles on the lead hand instead of 3+. Hit 20 balls per session with the new grip, watching TrackMan face angle. Goal: face angle within +/-1 degree of target for 5 consecutive shots. Do not change path simultaneously -- let the new grip stabilize before adjusting path.

### Correction Timeline

- **Grip weakening:** 2-4 weeks for comfort; face angle improves immediately
- **Path adjustment (in-to-out to neutral):** 4-6 weeks
- **Overcorrection recovery (slice-grip to hook back to controlled draw):** 6-10 weeks -- the hardest fix because two variables must change simultaneously

### Related Faults

- Early extension can cause a compensatory hook (flip the hands to save the shot)
- A hook with poor contact (fat/thin) points to early extension as the shared root cause
- Strong grip + inside path + early release = snap hook under pressure
- Toe strikes amplify hook via gear effect

---

## 3. Shank

### Biomechanical Cause Chain

The shank is impact between the ball and the hosel of the club. It is a strike fault, not a face/path fault -- TrackMan path data can look entirely normal on a shank. The core mechanism: the club's center of mass is presented significantly further from the golfer's center of rotation at impact than it was at address.

**Primary cause -- Early Extension (the "Goat Hump"):** The pelvis thrusts forward and upward toward the ball during the downswing, eliminating the space between the body and the intended hand path. The CNS makes an instantaneous subconscious correction: it forces the arms and club outward, away from the body, into the only available space. This outward rerouting shoves the hosel directly into the ball path.

**Secondary cause -- Standing too close at address:** If the setup distance is insufficient, even a reasonable swing can present the hosel. However, this is often a compensatory adjustment -- the golfer moved closer because early extension was pushing them onto their toes, and they instinctively backed away but not enough.

**Tertiary cause -- OTT path pushing club outward:** An over-the-top move shifts the entire swing arc outward. Combined with early extension, this doubles the outward displacement.

**The psychological cascade:** Shanks create a fear-tension-shank feedback loop. The golfer anticipates the shank, grips tighter, tenses forearms, restricts rotation, and ironically produces the exact conditions (restricted rotation --> early extension --> outward hand path) that cause another shank. Breaking this loop requires conscious relaxation protocols alongside mechanical fixes.

### TrackMan Diagnostic Signature

| Parameter | Shank Pattern |
|---|---|
| Club Path | Often looks NORMAL (0 to +2 deg) |
| Face Angle | Variable -- not diagnostic |
| Impact Location | Extreme heel/hosel (impact tape is essential) |
| Ball Speed | Dramatically reduced (smash factor <1.0) |
| Ball Flight | Low, hard right, minimal spin, no consistent pattern |
| Launch Angle | Very low (ball barely gets airborne) |

**Critical diagnostic note:** Do not chase path/face data when shanking. The problem is WHERE on the face the ball contacts, not the face angle or path. Impact tape or foot spray on the face is the primary diagnostic tool.

### TPI Physical Screen

- Limited hip IR (<30 deg) -- primary driver of early extension
- Weak glutes/core -- can't stabilize pelvis against rotational forces
- Limited ankle dorsiflexion (<15 deg) -- shifts weight toward toes
- Poor single-leg balance -- weight moves forward during downswing

### Corrective Drills

**Drill 1: Headcover Outside Ball (space constraint)**
Setup: Place a headcover or towel 1 inch outside the toe of the club at address, parallel to the target line. Swing without touching the headcover. If you shank, the club moved outward past the headcover position. This external constraint forces the hands to stay closer to the body through impact. Start with pitch shots (40 yards), progress to half swings, then 75%. Never go full speed until 20 consecutive clean contacts.

**Drill 2: Wall/Chair Drill (early extension fix)**
Setup: Place the back of a chair (or stand with glutes against a wall) touching your backside at address. Make practice swings maintaining contact through the impact zone. If your glutes lose contact with the wall/chair during the downswing, early extension is present. Practice 5-10 minutes daily -- slow-motion swings only. The goal is to feel the glutes stay back and the hips ROTATE rather than THRUST forward.

**Drill 3: Two-Tee Gate (strike centering)**
Setup: Push two tees into the ground creating a gate just wider than the clubhead -- one tee at the toe line, one at the heel line. Hit balls through the gate. If you hit the outside tee (heel side), the club moved outward. Start with 50% speed and a pitching wedge. The gate provides immediate binary feedback: clean pass or tee contact.

### Correction Timeline

- **Acute shanks (onset <1 week, no prior history):** Often a setup issue -- fixed in 1-2 sessions by checking distance from ball, ball position, and weight distribution
- **Chronic shanks (early extension root cause):** 4-8 weeks of focused practice to identify root causes; ongoing maintenance is required
- **Psychological recovery:** 2-4 additional weeks after mechanical fix before full on-course confidence returns
- **Relapse prevention:** Wall drill as pre-round warm-up check, 3x/week minimum during maintenance phase

### Related Faults

- **Early extension is the primary upstream cause** -- fixing early extension resolves most shank tendencies
- Loss of posture and hands moving away from body are symptoms of early extension, not independent faults
- OTT can compound the shank by pushing the arc outward
- Casting can trigger shanks by extending the arms prematurely

---

## 4. Fat/Thin Shots (Low Point Control)

### Biomechanical Cause Chain

Fat and thin shots are both low point failures. The swing arc's lowest point (low point) should be 3-4 inches AFTER the ball with irons, producing ball-first contact followed by a divot. When low point is before the ball, the club either hits the ground first (fat) or the golfer's CNS compensates by lifting (thin/top).

**Fat shot mechanism:** Low point is behind the ball. The clubhead reaches the ground before it reaches the ball. The leading edge digs into turf, decelerating the club and reducing ball speed by 20-50%. Root causes: weight staying on trail foot, casting (releasing wrist angles early), early extension (changes spine angle which changes arc radius), or simply having the ball too far forward in the stance.

**Thin shot mechanism:** The low point is still behind the ball, but the golfer unconsciously lifts or stands up to avoid hitting fat. The leading edge contacts the equator of the ball. Alternatively, early extension raises the entire arc, and the lowest point of the now-raised arc catches the ball thin. Fat and thin shots often alternate in the same session because they share a root cause (low point behind ball) with different compensatory responses.

**The weight shift connection:** Weight shift and wrist flexion are the two biggest low point influences. Forward weight transfer (70-80% on lead foot at impact) moves the low point forward. Maintaining wrist flexion (bowed lead wrist / forward shaft lean) prevents early release that raises the low point.

### TrackMan Diagnostic Signature

| Parameter | Fat Shot | Thin Shot |
|---|---|---|
| Low Point | Before ball ("B") | Before ball ("B") or at ball |
| Attack Angle | Often positive with irons (hitting up) | Shallow or positive |
| Ball Speed | 20-50% below normal | 10-30% below normal |
| Smash Factor | <1.20 (7-iron norm: 1.33) | <1.25 |
| Launch Angle | High and weak (added loft) | Very low (<8 deg with mid-iron) |
| Spin Rate | Reduced (ground contact before ball) | Reduced (equator contact) |
| Dynamic Loft | Elevated (flipping adds loft) | Low (leading edge presented) |

**Key diagnostic:** If fat and thin shots alternate, the root cause is the same -- inconsistent low point. Do NOT treat them as separate faults.

### TPI Physical Screen

- Limited hip IR --> early extension --> low point variance
- Weak core/glutes --> can't maintain posture --> arc radius changes
- Limited ankle dorsiflexion --> weight shifts to toes --> early extension
- Poor proprioception --> inconsistent weight shift patterns

### Corrective Drills

**Drill 1: Towel Behind Ball (low point training)**
Setup: Fold a golf towel and place it 4-6 inches behind the ball. Hit shots without touching the towel. If you contact the towel before the ball, low point is too far back. As you improve, move the towel progressively closer (to 3 inches, then 2 inches). When you can place it grip-length behind the ball and miss it consistently, low point control is dialed. Use a 7-iron, 20 reps per set.

**Drill 2: Line Drill (visual low point feedback)**
Setup: Spray paint a line on the range mat perpendicular to the target line (or use a chalk line). Place the ball on the line. After each swing, check where the divot starts relative to the line. Goal: divot starts ON or AFTER the line, never before. This drill provides immediate visual feedback on every rep. Hit 30 balls per session.

**Drill 3: Punch Shot Rehearsal (shaft lean and compression)**
Setup: Using a 7 or 8 iron, hit punch shots to 60% distance. Ball position center of stance, hands pressed forward so shaft lean is visible at address. Make a 3/4 backswing and focus on maintaining the shaft lean through impact -- feel the hands leading the clubhead. Low trajectory confirms proper compression. Hit 20 punch shots per set, alternating with full swings.

### Correction Timeline

- **Setup-related fat shots (ball position, weight distribution):** 1-2 weeks
- **Low point from casting/early release:** 4-6 weeks with dedicated drill work
- **Low point from early extension:** 6-12 weeks (must fix early extension first)
- **Tour-level low point consistency (+/-1 inch):** Ongoing -- this is a career-long pursuit

### Related Faults

- Early extension is the leading cause of fat shots in higher-handicap golfers
- Casting (early release) moves low point behind the ball by releasing wrist angles prematurely
- Fat/thin alternation is the hallmark of inconsistent low point -- treat as single fault
- Shanks and fat shots share the same root cause (early extension) in many golfers

---

## 5. Early Extension

### Biomechanical Cause Chain

Early extension is any forward thrust of the lower body (pelvis) toward the ball during the downswing. It is the most common swing fault in amateur golf (approximately 70% of recreational golfers exhibit it per TPI data) and is the root cause of the largest number of downstream faults.

**The mechanism in detail:**

1. At address, the golfer establishes spine angle and hip hinge, creating space between the posterior and an imaginary vertical line (the "tush line")
2. In a correct downswing, the pelvis rotates within this space -- the glutes may even move slightly AWAY from the ball as the hips clear
3. In early extension, the pelvis thrusts forward and upward. The glutes move toward the ball, crossing the tush line
4. This forward thrust eliminates the physical space the arms need to swing through on their intended path
5. The torso is forced to raise up (loss of posture) to make room for the arms
6. The arms either get "stuck" behind the body (producing blocks and compensatory hooks) or are pushed outward (producing shanks)
7. The wrist angles release early to compensate (casting), adding dynamic loft and moving the low point behind the ball
8. The result is a cascade of inconsistent contact, directional variance, elevated spin, and power loss

**Why it happens (physical roots):**

- **Limited hip internal rotation (<30 deg):** This is the #1 physical cause. If the pelvis cannot rotate around the lead hip due to joint or muscular restrictions, forward and lateral movements dominate the pattern. The golfer literally cannot rotate, so they thrust.
- **Weak glutes and core:** The gluteal and abdominal muscles control pelvis orientation during the downswing. If they lack the strength or activation patterns to resist the rotational forces, the pelvis defaults to its easiest movement -- forward.
- **Limited ankle dorsiflexion (<15 deg):** Cannot maintain squat-like posture through the swing. Weight shifts to toes, which pulls the pelvis forward.
- **Limited trunk-to-pelvis separation:** Caused by reduced spinal/rib cage mobility and shortened lats. The torso and pelvis move as a unit rather than sequentially.

### TrackMan Diagnostic Signature

| Parameter | Early Extension Pattern |
|---|---|
| Dynamic Loft | Elevated (3-8 deg above expected for club) |
| Spin Rate | Elevated (15-30% above optimal) |
| Attack Angle | Inconsistent (+/-3 deg variance shot to shot) |
| Low Point | Variable and often before ball |
| Face Angle | Inconsistent (+/-4 deg vs tour's +/-1 deg) |
| Club Path | May appear normal OR push right |
| Smash Factor | Below potential (poor compression) |
| Ball Speed Variance | High (5-10 mph SD vs tour's 1-2 mph) |

**Key diagnostic:** Early extension creates VARIANCE more than it creates a consistent miss. If consistency metrics are poor across multiple parameters simultaneously, early extension is the likely root cause.

### TPI Physical Screen

The following screens directly assess early extension risk:

| Screen | Pass Threshold | Fail Implication |
|---|---|---|
| Lead Hip IR | >30 deg | Primary early extension driver |
| Trail Hip IR | >30 deg | Contributes to backswing compensation |
| Overhead Deep Squat | Full depth, heels down | Core stability, ankle mobility |
| Single Leg Balance | 15+ sec eyes closed | Proprioception deficit |
| Pelvic Tilt Test | Anterior/posterior control | Can't stabilize pelvis dynamically |
| Toe Touch | Fingers reach floor | Hamstring/hip hinge flexibility |
| Bridge with Leg Extension | 10 reps, pelvis stable | Glute weakness |

### Corrective Drills

**Drill 1: Wall/Chair Glute Contact (proprioceptive feedback)**
Setup: Stand with your backside touching a wall or the back of a chair at address position. Make slow-motion swings (no ball initially), maintaining glute contact with the wall through the entire downswing and impact zone. If you lose contact, early extension is occurring. Progress: (1) Slow motion, no ball, 20 reps; (2) Slow motion with ball, 20 reps; (3) Half speed, 20 reps; (4) 75% speed. Practice 10 minutes daily. This is the single most important drill for early extension and should be a permanent warm-up check.

**Drill 2: Alignment Stick in Belt Loops (rotation training)**
Setup: Thread an alignment stick through your front two belt loops so it extends past your lead hip. During the downswing, the stick should rotate behind you (the lead-hip end points away from the ball). If the stick moves toward the ball, you are thrusting rather than rotating. Practice with half swings, focusing on the feeling of the hips TURNING rather than PUSHING. 15-20 reps per set.

**Drill 3: Split Squat Swings (lower body engagement)**
Setup: Take your address position but place your trail foot back in a split stance (lunge position) with only the toe on the ground. This prevents early extension because you physically cannot thrust forward from this base. Hit 15-20 balls with a 7 or 8 iron at 60% effort. Focus on the feeling of rotating around a stable lead leg. Return to normal stance and try to replicate the rotational feel.

**Supplementary Exercise: Hip Internal Rotation Stretching**
Setup: Figure-4 stretch (seated, ankle on opposite knee, lean forward), 30-second holds, 3 sets each side. Hip Windshield Wipers (seated, knees bent 90 degrees, rotate knees side to side), 15 reps each direction. Perform daily, ideally pre-practice. The goal is to achieve >30 deg hip IR in each direction. This is a prerequisite for the mechanical drills to be effective.

### Correction Timeline

- **With physical limitation present (hip IR <30 deg):** Address mobility FIRST. Expect 4-6 weeks of daily stretching before sufficient hip IR for rotational mechanics. Then 6-8 weeks of swing pattern retraining.
- **Without physical limitation (motor pattern only):** 6-8 weeks of focused practice 3x/week
- **Total timeline (mobility + motor pattern):** 10-14 weeks for most golfers
- **On-course transfer:** Add 2-4 weeks beyond practice green competence. Early extension returns first under pressure -- expect setbacks on the course during the transition period.
- **Maintenance:** Wall drill as permanent pre-round check; hip IR stretching as permanent warm-up element

### Related Faults

Early extension is the UPSTREAM cause of:
- Shanks (hands pushed outward)
- Fat/thin shots (inconsistent low point)
- Casting (arms compensate for lost rotation)
- Block right (arms stuck behind body)
- Compensatory hook (flip to save the shot)
- Loss of posture (stand-up move through impact)
- Elevated spin rate (increased dynamic loft from scooping)

**Fixing early extension will partially or fully resolve all of the above.**

---

## 6. Casting / Early Release

### Biomechanical Cause Chain

Casting is the premature uncocking of the wrists during the downswing, releasing stored energy before impact. In a proper downswing, the wrist cock angle maintained from the top of the backswing reaches maximum lag when the lead arm is approximately 30 degrees below horizontal (per MacKenzie's forward dynamics models). Casting releases this angle at or near the top of the backswing.

**What physically goes wrong:**

1. At the top, the golfer initiates the downswing with the arms and hands rather than the lower body
2. The wrists uncock immediately, steepening the shaft and the plane
3. The clubhead reaches maximum speed BEFORE impact rather than AT impact
4. At impact, the shaft leans backward (away from target) rather than forward
5. This adds dynamic loft (3-10 degrees beyond intended), reduces compression, increases spin rate, and moves the low point behind the ball
6. The ball launches higher, shorter, and with more spin than optimal

**Why it happens:**

- **Instinct to hit the ball:** The most natural movement when holding a stick and trying to hit something is to swing the arms. The lower-body-first sequence is counterintuitive.
- **Early extension upstream:** When the pelvis thrusts forward, the arms have no room to drop. They fire outward and release early to recover the swing arc.
- **Limited wrist extension (<60 deg):** Cannot physically maintain the lag angle
- **Poor lower body engagement:** If the hips don't rotate, the torso doesn't rotate, and the arms have nothing to lag behind

### TrackMan Diagnostic Signature

| Parameter | Casting Pattern |
|---|---|
| Dynamic Loft | 3-10 deg above optimal for club |
| Shaft Lean | Backward (negative) -- hands behind ball at impact |
| Spin Loft | >30 deg (should be 20-25 for mid-irons) |
| Smash Factor | <1.35 with 7-iron (tour: 1.33 but with proper speed) |
| Ball Speed | Below expected for club speed |
| Spin Rate | 15-30% elevated |
| Launch Angle | High (weak trajectory, no penetration) |
| Attack Angle | Often shallow or positive with irons |
| Carry Distance | 10-20% below potential |

**Key diagnostic:** Elevated dynamic loft is the smoking gun. If the stamped loft is 34 degrees (7-iron) and dynamic loft is 28+ degrees at impact, casting is confirmed. Tour average dynamic loft for a 7-iron is approximately 23-26 degrees.

### TPI Physical Screen

- Wrist extension test (<60 deg indicates risk)
- Overhead deep squat (core stability for lower body initiation)
- Pelvic rotation test (can the lower body lead?)
- Lower body stability screens (single leg balance, bridge)

### Corrective Drills

**Drill 1: Pump Drill (lag retention)**
Setup: Make a normal backswing. Instead of swinging through, "pump" the club down to waist height while keeping the wrists cocked, then return to the top. Pump twice, then on the third repetition, complete the swing. The feel: shift weight to the lead foot and let the hands drop while maintaining the wrist angle. Hips initiate, hands follow. 15 reps per set, 7-iron.

**Drill 2: Motorcycle Drill (wrist flexion)**
Setup: At the top of the backswing, actively twist the lead hand as if turning a motorcycle throttle toward you. This moves the lead wrist into flexion (bowed position), keeping the clubface square and the shaft angle retained. Practice the motion in slow motion in front of a mirror, then with half-speed swings. The feel is "pushing the handle down" rather than "throwing the clubhead at the ball."

**Drill 3: Half-Speed Impact Bag Strikes (forward shaft lean)**
Setup: Place an impact bag (or heavy duffle bag) at the ball position. Make slow swings focusing on contacting the bag with the hands AHEAD of the clubhead. The shaft should lean forward at contact. If the clubhead reaches the bag before the hands, casting is present. 20 reps, focus on feel rather than speed. The goal: hands lead, then the club catches up THROUGH the bag, not before it.

### Correction Timeline

- **New golfer with casting tendency:** 3-5 weeks with focused drill work
- **Experienced golfer with ingrained casting pattern:** 6-12 weeks
- **Casting caused by early extension:** Fix early extension FIRST (6-12 weeks), then the casting often self-corrects
- **Long-term maintenance:** Pump drill as warm-up check; periodic dynamic loft monitoring

### Related Faults

- Early extension is the most common upstream cause of casting
- Casting causes elevated dynamic loft --> high weak shots
- Casting moves low point behind the ball --> fat/thin
- Casting reduces smash factor --> distance loss at every club
- Casting and OTT often co-occur (upper body dominates entire downswing)

---

## 7. Over-the-Top (OTT)

### Biomechanical Cause Chain

The over-the-top move is an outward throwing of the club during the transition from backswing to downswing, resulting in the club approaching the ball from outside the intended swing plane. The clubhead path tracks out-to-in (negative club path on TrackMan).

**What physically goes wrong:**

1. At the top of the backswing, the lead wrist is in extension (cupped), making it structurally difficult to shallow the club
2. The downswing is initiated by the upper body (shoulders, arms) rather than the lower body (hips, weight shift)
3. The shoulders rotate toward the target before the hips have cleared, "throwing" the club over the top of the intended plane
4. The club approaches on a steep, outside path, cutting across the ball
5. If the face is square to the target (but open to the leftward path), the ball slices
6. If the face is square to the path, the ball pulls left
7. The steep approach produces deep divots pointing left of target

**Why it happens:**

- **Poor sequencing:** The golfer lacks the motor pattern for lower-body-first transition. The instinct is to start the downswing with whatever feels "strongest" -- the arms and shoulders.
- **Limited T-spine rotation:** If the thoracic spine cannot rotate sufficiently, the golfer compensates by using arm strength, which throws the club outside the plane.
- **Limited trail shoulder external rotation:** Cannot physically get the trail elbow in front of the hip in transition (the "slot"), so the arms go up and over.
- **Ball position too far forward:** Forces the swing arc to extend outward to reach the ball.
- **Alignment aimed left:** If the body is open to the target, the swing follows the body line.

### TrackMan Diagnostic Signature

| Parameter | OTT Pattern |
|---|---|
| Club Path | -3 to -10 deg (out-to-in) |
| Swing Direction | More negative than club path |
| Face Angle | Variable (determines pull vs slice) |
| Attack Angle | Steep: -5 to -10 deg with irons, negative with driver |
| Divot Direction | Points left of target |
| Spin Rate | Elevated (steep spin loft) |
| Launch Angle | Lower than expected (steep AoA compresses launch) |
| Dynamic Loft | Can vary; often elevated from compensation |

**Key diagnostic:** Club path consistently below -3 degrees across multiple clubs confirms OTT. If path is -5 or worse, it is a significant OTT pattern.

### TPI Physical Screen

- T-spine rotation (<45 deg each direction)
- Trail shoulder external rotation (<90 deg)
- Lower body disassociation test (can pelvis rotate independently of torso?)
- Overhead deep squat (overall mobility screen)

### Corrective Drills

**Drill 1: Towel/Headcover Outside Ball (path constraint)**
Setup: Place a towel or headcover just outside the toe of the club at address, about 2 inches past the ball on the far side. Swing without hitting the towel. If OTT is present, the club will contact the towel on the downswing. This provides immediate external feedback on the swing plane. Start with half swings, progress to 75%. Use a 7-iron.

**Drill 2: Trail Elbow Drill (slot the club)**
Setup: Make a normal backswing. Start the downswing by focusing on driving the trail elbow DOWN toward the trail hip pocket. The feel is the elbow dropping into the "slot" in front of the hip, rather than the club being thrown forward. This automatically shallows the shaft and promotes an inside approach. Practice in slow motion with a mirror, then progress to half-speed hits. 15-20 reps per set.

**Drill 3: Step Drill (lower body sequencing)**
Setup: Address the ball normally. During the backswing, lift the lead foot slightly off the ground. As you begin the downswing, step the lead foot back down and shift weight into it BEFORE the arms swing forward. This forces the lower body to initiate the downswing. The arms will automatically drop into a better slot because the lower body is already rotating ahead of them. Hit 20 balls per session. Use a 7 or 8 iron at 70% effort.

### Correction Timeline

- **With dedicated practice (3x/week) and launch monitor feedback:** 4-8 weeks
- **Without biometric feedback (feel-based only):** 8-16 weeks
- **With T-spine mobility limitation:** Address mobility first (4-6 weeks), then swing pattern (6-8 weeks). Total: 10-14 weeks.
- **On-course transfer:** OTT tends to return under pressure (speed increase triggers old pattern). Add 3-4 weeks of on-course practice at controlled tempo before the new pattern holds.

### Related Faults

- OTT is the primary cause of the path-dominant slice
- OTT + casting frequently co-occur (upper body dominates entire swing)
- OTT + early extension = compounded outward club displacement (shank risk)
- Steep AoA from OTT robs driver distance (hitting down -5 deg vs up +5 deg = 24-36 yard difference at same speed)
- OTT divots point left; if divots point straight with an OTT feel, the path may be improving before the feel catches up (feel is not real)

---

## 8. Chipping Inconsistency / Yips

### Biomechanical Cause Chain

Chipping inconsistency in amateurs stems from two interrelated failures: mechanical breakdown of the chipping motion and neuromuscular interference (yips) from overthinking and fear-based tension.

**Mechanical failures:**

1. **Weight shifts backward:** At impact, weight moves to the trail foot instead of staying on the lead foot (55-65% minimum). This moves the low point behind the ball, producing fat or thin chips.
2. **Wrist flipping:** The trail wrist overtakes the lead wrist before impact, adding loft and scooping the ball. The leading edge lifts, catching the ball thin or skulling it. The golfer is trying to "help" the ball into the air rather than trusting the loft.
3. **Deceleration:** Fear of hitting too far causes the golfer to slow down approaching impact. Deceleration destroys low point consistency and produces unpredictable contact.
4. **Pivot stops moving:** The most common mechanical issue. The body stops rotating, and the hands take over. When the body stalls, the hands flip. When the hands flip, the low point becomes inconsistent.
5. **Improper bounce usage:** The golfer presents the leading edge rather than the bounce (the flange on the sole). The leading edge digs into turf; the bounce glides through it. Opening the face slightly at address exposes the bounce for cleaner contact.

**Neuromuscular yips:**

The chipping yips are a neurological phenomenon where the brain overthinks and micromanages the stroke, causing involuntary muscle contractions (typically in the forearms and wrists). The result is jerky, spasmodic movements that destroy rhythm and contact. The yips cycle: poor chip --> anxiety about next chip --> tension --> worse chip --> deeper anxiety. Breaking this cycle requires both mechanical simplification and psychological intervention.

### Diagnostic Indicators

Chipping does not typically use TrackMan data for diagnosis. Instead, the diagnostic is observational:

| Indicator | Implication |
|---|---|
| Fat/thin chips alternate | Low point behind ball, weight back |
| Skulled shots (ball shoots across green) | Wrist flip, leading edge contact |
| Distance control poor (same club, vastly different results) | Deceleration or inconsistent stroke length |
| Involuntary wrist movement at impact | Yips (neuromuscular) |
| Tension visible in forearms/grip at address | Anxiety-driven grip pressure |
| Body stops moving, hands take over | Pivot stall --> flip |

### TPI Physical Screen

- Wrist extension/flexion ROM -- limited ROM reduces control
- Core stability -- needed for pivot-driven chipping
- Single-leg balance -- base stability for compact motion

### Corrective Drills

**Drill 1: Lead-Hand-Low Grip (anti-flip)**
Setup: Grip the club with the lead hand below the trail hand (cross-handed / left-hand-low for right-handed golfers). This grip structurally prevents the trail wrist from flipping through impact. The lead arm and shaft form a continuous line. Hit 20 chips from 10-15 yards. Focus on the feeling of the lead wrist staying flat (not breaking down) through the strike. This is a training grip -- return to normal grip once the anti-flip feel is ingrained.

**Drill 2: Coin/Tee Under the Ball (trust the loft)**
Setup: Place a coin or pushed-in tee directly under the ball on the practice green. Focus on striking the coin/tee, not the ball. This trains a slightly descending strike and eliminates the scooping instinct. The ball pops up off the loft naturally. Hit 20 chips. If the ball launches too low or too high, adjust the amount of shaft lean.

**Drill 3: Continuous Motion Drill (anti-deceleration)**
Setup: Use a 56-degree wedge. Before each chip, make 3 continuous practice swings back and through without stopping -- like a pendulum. Then immediately step up and hit the ball with the same rhythm. The goal is to eliminate the "stop and think" moment that triggers deceleration and yips. Count "1-2-3-hit" where the hit is just the next swing in the rhythm sequence. Hit 20 chips, varying target distances each time (interleaved practice).

**Supplementary: Pre-Shot Routine for Yips Management**
1. Pick the landing spot (not the hole)
2. Make 2 practice swings looking at the landing spot, matching the required swing length
3. Address the ball, one look at the landing spot, execute within 3 seconds
4. Do NOT look at the ball flight until after the club has finished its arc

The key is reducing the time between address and execution. The longer a yips-affected golfer stands over the ball, the more the CNS interferes.

### Correction Timeline

- **Mechanical chipping inconsistency:** 2-4 weeks with 3x/week short game practice
- **Deceleration habit:** 3-5 weeks of continuous motion drill integration
- **Yips (neuromuscular):** 4-8 weeks minimum; may require professional guidance (sports psychologist) for severe cases. Grip change (lead-hand-low permanently) provides immediate partial relief.
- **Full confidence recovery on course:** 6-12 weeks after mechanical competence is achieved

### Related Faults

- Early extension degrades chipping by changing the low point unpredictably
- Casting (wrist flip) is the primary mechanical cause of skulled chips
- Chipping yips are often psychologically linked to shanking yips -- solving one can unlock the other
- Poor chipping does not cascade into full swing faults, but full swing early extension DOES cascade into poor chipping

---

## User-Specific Notes

This section personalizes the fault diagnosis and correction protocols to the user's swing profile: 87-92 mph driver speed, stiff flex shafts, mid-handicapper.

### Active Fault Priority Stack

1. **Early Extension (ROOT CAUSE) -- Status: Active, Primary Focus**
   - This is the upstream cause of the user's shank history and low point inconsistency
   - Physical root: likely limited hip IR (needs TPI screen confirmation) and/or glute/core activation patterns
   - Protocol: Daily wall drill (5-10 min), hip IR stretching (Figure-4, Windshield Wipers), glute activation pre-practice
   - Target: Maintain tush line contact through impact for 20 consecutive swings at 75% speed before progressing

2. **Shank -- Status: 4-week protocol completed, Maintenance Phase**
   - Root causes identified: early extension, loss of posture, hands away from body
   - All three root causes trace back to early extension
   - Maintenance protocol: Headcover outside ball drill as warm-up check (10 balls), wall drill pre-round
   - Relapse triggers: fatigue, pressure, speed increase. Monitor during back 9 and competitive rounds.
   - Psychological recovery: if a shank occurs on course, immediately take 2 practice swings with the headcover feel, then play the next shot at 80% effort

3. **Low Point Control -- Status: Active, Secondary Focus**
   - Working on forward shaft lean -- this is the correct approach
   - Two interventions needed: (1) fix early extension (moves low point forward automatically), (2) maintain wrist flexion through impact (prevents casting that raises low point)
   - Drill priority: Towel behind ball (20 reps), Line drill (30 reps), Punch shot rehearsal (20 reps)
   - Target: Divot consistently starts at or after ball position for 15/20 shots

4. **Driver Slice to Hook Overcorrection -- Status: Active, Needs Attention**
   - Sequence of events: slice --> strengthened grip --> hook
   - The grip change closed the face but the path was not adjusted
   - Current situation: strong grip + existing path = closed face-to-path = hook
   - Fix: Do NOT weaken the grip back to where it was. Instead, adjust PATH to match the new grip. With a strong grip delivering a closed face, the path needs to be slightly more out-to-in (yes, toward the old slice path) to neutralize face-to-path. Target: face-to-path between -1 and -3 degrees for a controlled draw.
   - Alternative: slightly weaken the grip (rotate 1/8 turn, not 1/4) while keeping path stable. Let TrackMan face angle data guide the adjustment incrementally.
   - At 87-92 mph driver speed with stiff shafts: optimal attack angle is +3 to +5 degrees, launch 13-16 degrees, spin 2,200-2,800 rpm. Hitting UP eliminates the need for path manipulation to avoid a slice.

5. **Chipping Inconsistency -- Status: Active, Tertiary Focus**
   - Likely related to early extension (same low point issues as full swing)
   - Start with lead-hand-low drill (20 chips per session) and continuous motion drill
   - Weight must stay 60%+ on lead foot throughout the entire chipping motion
   - Use 56-degree wedge as primary chipper (highest consistent spin rate, better compression than 60-degree)

### Speed-Specific Considerations

At 87-92 mph driver speed:
- Optimal driver loft: 10.5-12 degrees
- Target attack angle: +3 to +5 degrees (currently likely negative based on shank/early extension history)
- Potential distance gain from AoA optimization alone: 15-25 yards (from -3 to +3 degrees at 90 mph)
- Stiff flex shafts are appropriate for this speed range
- Dynamic loft variance is the key metric to monitor -- if it varies by >3 degrees shot to shot, early extension is still active

### Interconnection Map (Active Faults)

```
EARLY EXTENSION (fix this first)
|
+-- Shank (4-week protocol done, maintenance)
+-- Low point inconsistency (active work)
|   +-- Fat irons
|   +-- Thin irons
+-- Chipping inconsistency (downstream)
+-- Contributing to driver hook (early extension --> flip --> closed face)

GRIP CHANGE (separate issue)
+-- Driver hook (face closed to path)
    +-- Fix: adjust path OR slightly weaken grip
```

### Practice Session Template

Pre-practice warm-up (10 min):
1. Hip IR stretching: Figure-4 stretch, 30 sec each side x 3
2. Hip Windshield Wipers: 15 reps each direction
3. Wall drill: 20 slow-motion swings maintaining glute contact
4. Glute bridges: 10 reps with 2-second hold at top

Drill block (30 min, interleaved):
1. Headcover outside ball -- 10 shots, 7-iron, 75% speed (shank maintenance)
2. Towel behind ball -- 10 shots, 7-iron, 80% speed (low point)
3. Punch shots -- 10 shots, 8-iron, focusing on shaft lean (compression)
4. Lead-hand-low chips -- 10 chips, 56-degree, 10-15 yards (chipping)
5. Rotate back to drill 1, different club (interleaved)

Scoring practice (20 min, random):
1. Pick random targets at different distances
2. Alternate between full shots, pitch shots, and chips
3. Play "up and down" games -- chip and putt, track conversion rate
4. Vary clubs for similar distances (bump-and-run 8-iron vs lofted 56-degree)

Cool-down check (5 min):
1. 5 full swings with wall drill feel -- confirm early extension is not creeping back
2. Note any fatigue patterns (fatigue degrades path consistency, then face control)

---

## Practice Protocol: Structuring Corrective Work

### The Contextual Interference Principle

Research (Nature Scientific Reports 2024 meta-analysis) conclusively demonstrates that random/interleaved practice produces superior long-term retention and transfer compared to block practice, despite performing WORSE during the practice session itself.

**What this means for fault correction:**

- **Block practice** (hitting 50 balls with the same drill): Produces rapid apparent improvement during the session. The golfer feels good, but the improvement does not transfer to the course. The motor pattern is not encoded deeply enough for retention.
- **Interleaved practice** (rotating between 3-4 drills, never repeating the same one twice in a row): Feels harder and more frustrating during the session. Performance metrics look worse. But retention tests (performance 24-72 hours later) show 25-40% better results. The brain builds more robust motor patterns because it must reconstruct the movement each time rather than simply repeating it.

### How to Structure a Corrective Practice Session

**Phase 1: Warm-up and Activation (10 min)**
- Dynamic stretching targeting the physical limitation being addressed
- Constraint drill at slow speed (wall drill, split stance, etc.)
- Goal: activate the correct movement pattern before hitting balls

**Phase 2: Focused Drill Work (25-35 min)**
- Select 3-4 drills addressing different faults or different aspects of the same fault
- Rotate between drills every 5-10 balls (interleaved, not block)
- Vary the club with each rotation (7-iron, PW, 8-iron -- never the same club twice in a row)
- After each set, take a 30-second break and rate contact quality 1-10
- When contact quality drops below 6/10, the session is producing diminishing returns. Stop drilling and move to the scoring phase.

**Phase 3: Scoring/Transfer Practice (15-20 min)**
- Simulate on-course conditions: vary targets, clubs, shot shapes, lies
- Play games with consequences (e.g., "must up-and-down from 5 different positions")
- This is where the drills transfer to performance
- No mechanical thoughts -- commit to a target and swing
- Track success rate: what percentage of shots achieve the intended outcome?

**Phase 4: Cool-down Assessment (5 min)**
- 5 full swings with the primary constraint drill (e.g., wall drill feel)
- Compare to warm-up: is early extension still controlled? Is contact improving?
- Note fatigue level: if speed or contact has degraded, the session ran too long
- Log session quality and any breakthroughs/regressions in daily note

### Frequency and Volume Guidelines

| Fault Severity | Practice Frequency | Duration per Session | Time to Competence |
|---|---|---|---|
| Setup issue (grip, alignment, ball position) | 3x/week | 20 min | 1-3 weeks |
| Motor pattern change (path, face control) | 3-4x/week | 45-60 min | 4-8 weeks |
| Deep-rooted movement fault (early extension, OTT) | 4-5x/week | 45-60 min | 8-16 weeks |
| Physical limitation requiring mobility work | Daily (stretching), 3x/week (practice) | 10 min mobility + 45 min practice | 10-16 weeks |

### The Three Stages of Motor Learning Applied to Fault Correction

1. **Cognitive stage (weeks 1-3):** The golfer must actively think about the new movement. Performance during practice may worsen. Conscious control is required. Block practice is acceptable in this stage to establish the movement pattern.

2. **Associative stage (weeks 3-8):** The movement begins to feel more natural with less conscious thought. Errors become smaller and less frequent. Switch to interleaved practice. The golfer can execute the new pattern when focused but reverts under pressure or fatigue.

3. **Autonomous stage (weeks 8+):** The movement is automatic. The golfer can execute under pressure, in competition, and while fatigued. Full on-course transfer is achieved. This stage requires extensive random/game-based practice, not drills.

**Critical insight:** Most golfers who report that a lesson "worked" are in stage 2. The fault returns under pressure because they never reached stage 3. Full correction requires months of deliberate, interleaved practice. Patience is the hardest part of swing change.

### Session Quality Metrics

Track these to ensure practice is productive:

- **Contact quality trend:** Are clean contacts increasing across the session? If they plateau or decline early, fatigue or frustration is degrading quality. Stop.
- **Drill transfer rate:** After rotating away from a drill and back, is performance maintained? If it resets each time, the motor pattern is not encoding.
- **On-course transfer:** Track the percentage of rounds where the corrected fault does NOT reappear. Goal: 80%+ of rounds without reversion before declaring the fault "fixed."
- **Variance reduction:** Monitor shot-to-shot variance in face angle, path, and low point. Reducing variance matters more than changing the average.

---

## Quick Reference: Fault to Root Cause to Priority Drill

| Fault | Most Likely Root Cause | First Drill to Try | TPI Screen |
|---|---|---|---|
| Slice (path) | OTT from upper body initiation | Headcover gate outside ball | T-spine rotation, lower body disassociation |
| Slice (face) | Weak grip / cupped lead wrist | Motorcycle drill for wrist flexion | Wrist extension ROM |
| Hook (path) | Excessive in-to-out path | Alignment stick gate | Hip slide test, single-leg balance |
| Hook (face) | Strong grip / overpronation | Lead-hand-only swings | Forearm rotation ROM |
| Shank | Early extension pushing hands outward | Headcover outside ball + wall drill | Hip IR, glute strength, ankle DF |
| Fat shot | Low point behind ball (weight back, casting) | Towel behind ball | Core stability, hip IR |
| Thin shot | Same root as fat (compensatory lift) | Line drill | Same as fat shot |
| Early extension | Limited hip IR / weak glutes | Wall/chair glute contact | Hip IR (<30 deg is critical threshold) |
| Casting | Upper body initiates downswing | Pump drill | Wrist extension, lower body disassociation |
| OTT | Poor transition sequencing | Trail elbow to hip pocket | T-spine rotation, trail shoulder ER |
| Chipping yips | Pivot stall plus wrist flip plus anxiety | Lead-hand-low grip | Wrist ROM, core stability |
| Driver distance loss | Negative attack angle | Tee high + ball forward + upward feel | Same as early extension |

---

## Appendix: TPI Screen Quick Reference

The 5 most golf-relevant screens with pass/fail thresholds and fault implications:

| Screen | How to Test | Pass | Fail Causes |
|---|---|---|---|
| Hip Internal Rotation | Seated, knee at 90 deg, rotate foot outward, measure angle from vertical | >30 deg each side | Early extension, sway, slide, shank |
| Thoracic Rotation | Seated on bench (locks pelvis), rotate torso, measure vs vertical | >45 deg each way | OTT, reverse spine angle, flat shoulder plane |
| Overhead Deep Squat | Arms overhead, squat to full depth | Heels stay down, arms stay up | Early extension, poor GRF, balance issues |
| Single Leg Balance | Stand on one foot, eyes closed | >15 sec each side | Inconsistent weight shift, low point variance |
| Pelvic Tilt | Standing, alternate between anterior and posterior tilt | Full control both directions | Cannot stabilize pelvis, early extension |

---

*This document complements [[ref-biomechanics]], which covers the physics and data benchmarks. This document covers what goes wrong and how to fix it. Load both before swing analysis or practice planning.*
