# Product Requirements Document (PRD)

## AI-Driven Intelligent Surveillance System with Real-Time Threat Detection and Telegram Alerts

## 1. What to Build

### Product Definition

A web-based security application that uses AI and computer vision to monitor live webcam feeds or uploaded video footage for potential threats, reducing the need for continuous human observation.

### Goal

Enable faster emergency response and reduce manual monitoring effort by:

- Continuously analyzing video streams for four critical threat categories.
- Instantly alerting authorized personnel via Telegram when a threat is confirmed.
- Maintaining a searchable, auditable log of every detected incident.

### Core Product Flow

The system ingests video from a webcam or uploaded file and analyzes it using AI detection models. When a threat crosses the configured confidence threshold, the system:

1. Draws a bounding box and confidence score on the frame where applicable.
2. Captures a screenshot of the incident.
3. Logs the event with its type, timestamp, confidence, and screenshot.
4. Sends an instant Telegram alert containing the image and event details to authorized recipients.

The product is scoped specifically to four physical-security threat categories: fire and smoke, weapons, violence, and accidents. It is not a general-purpose video analytics platform.

## 2. Target Users

### Primary Audience

- Facility security teams in schools, offices, warehouses, factories, hospitals, parking areas, and public spaces.
- Small-to-medium organizations without a dedicated 24/7 security operations center.
- Individual security operators responsible for monitoring multiple camera feeds.

### User Needs

| User need | How the product addresses it |
| --- | --- |
| Operators cannot watch every camera feed continuously. | Automated AI analysis runs continuously in the background. |
| Operators need immediate notification rather than post-event review. | Real-time Telegram alerts are sent when a threat is confirmed. |
| Organizations need evidence of what happened. | Every event includes a timestamped screenshot and detection metadata. |
| Operators need to investigate past incidents. | Detection history supports search and filtering. |
| Operators need confidence that the system will not generate constant false alarms. | Configurable confidence thresholds and debouncing reduce alert spam. |
| Organizations have limited technical and security staff. | The dashboard is designed to be simple and require minimal training. |

### Non-Users and Out-of-Scope Deployments for v1

- Enterprise-scale, multi-site deployments requiring centralized fleet management.
- Users requiring threat types beyond fire/smoke, weapons, violence, and accidents.
- Users requiring facial recognition or license plate reading.
- Users requiring on-premise operation without internet access, since Telegram alerts require connectivity.

## 3. Features

### Must-Have: Core MVP

1. **Live webcam surveillance** — real-time monitoring through a connected camera.
2. **Video upload and analysis** — analysis of pre-recorded footage.
3. **Fire and smoke detection** — single-frame YOLO-based detection.
4. **Weapon detection** — single-frame YOLO-based detection for guns and knives.
5. **Violence detection** — temporal or clip-based action recognition.
6. **Accident detection** — vehicle tracking with collision and sudden-stop heuristics.
7. **Instant Telegram alerts** — image, event type, timestamp, and confidence sent to authorized recipients.
8. **Detection history and event log** — persistent records for every confirmed incident.
9. **Dashboard** — live monitoring view plus history search and filtering.

### Should-Have: Near-Term

- Configurable alert cooldown and debouncing per threat type.
- Basic analytics, including detections per day, breakdown by type, and busiest camera.
- Multiple simultaneous camera sources.
- Manual event review and dismissal, including false-positive marking.

### Could-Have: Future

- Role-based access control, such as admin and viewer roles.
- Multi-channel alerts, including email and SMS in addition to Telegram.
- Mobile companion application.
- Edge deployment mode for offline environments.
- No-code custom threat-type training and model fine-tuning.

### Won't-Have: Explicitly Out of Scope for v1

- Facial recognition or biometric identification.
- License plate recognition.
- Audio-based threat detection, including gunshot sounds or screaming.
- Multi-tenant SaaS billing and subscription management.

## 4. Detection Scope

| Threat category | Detection approach | Expected output |
| --- | --- | --- |
| Fire and smoke | Single-frame YOLO detection | Class, confidence, and bounding box when detected |
| Weapons | Single-frame YOLO detection | Weapon class, confidence, and bounding box when detected |
| Violence | Temporal or clip-based action recognition | Violence event, confidence, and incident frame or clip context |
| Accidents | Vehicle tracking plus collision and sudden-stop heuristics | Accident type, confidence, and involved vehicle region |

All detection modules must respect the configured confidence threshold. Alerting should apply cooldown or debouncing logic where necessary to avoid repeated notifications for the same ongoing event.

## 5. Core User Flow

1. An authorized operator opens the surveillance dashboard.
2. The operator starts a webcam session or uploads a video.
3. The system processes frames through the applicable detection modules.
4. A detector identifies a threat above the configured confidence threshold.
5. The system annotates the frame and captures incident evidence.
6. The event is persisted in the detection history.
7. Telegram sends the alert and incident image to authorized recipients.
8. The operator reviews the live alert or historical event and may mark it as a false positive when supported.

## 6. Non-Functional Requirements

- **Detection latency:** Live-feed detections should trigger Telegram alerts in under five seconds from the threat appearing on camera.
- **Alert reliability:** Confirmed events should be delivered to Telegram whenever the system and network are available.
- **Auditability:** Every confirmed detection must retain event type, timestamp, confidence, source, and incident evidence.
- **Usability:** A security operator should be able to start monitoring and review an incident without specialized AI training.
- **Operational resilience:** Temporary Telegram or model errors should be surfaced clearly and should not silently discard detection events.
- **Privacy and security:** Access to live feeds, uploaded footage, event history, and Telegram configuration must be restricted to authorized users.

## 7. Success Metrics

- **Detection latency:** Time from a threat appearing on camera to Telegram alert receipt; target is under five seconds for live feeds.
- **False-positive rate:** Percentage of alerts marked as false positives during review.
- **Uptime:** Availability of the system during live surveillance sessions.
- **Alert delivery reliability:** Percentage of confirmed events successfully delivered to Telegram.
- **Incident traceability:** Percentage of confirmed events with complete metadata and screenshot evidence.

## 8. MVP Acceptance Criteria

- Operators can start a live webcam monitoring session.
- Operators can upload and analyze a video file.
- The system supports fire/smoke, weapon, violence, and accident detection flows.
- A confirmed detection produces annotated evidence where supported, a persisted event, and a Telegram alert.
- Operators can search and filter historical detections.
- The system applies confidence thresholds and avoids repeated alerts for the same ongoing event through debouncing or cooldown logic.
- Detection failures and Telegram delivery failures are visible to the operator or recorded for follow-up.
