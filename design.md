# UI/UX Guidelines and Visual Design System

## 1. UI/UX Principles

### Core Principles

- **Clean and intuitive interface:** Security dashboards are often used under stress during active incidents. Important information must be immediately visible.
- **Consistent user experience:** Shared components such as event cards, status badges, and buttons must look and behave consistently across Live View, History, and Settings.
- **Mobile-first design:** Security personnel may need to review alerts away from a desk. The dashboard must be fully usable on small screens.
- **Accessible navigation:** Use a clear visual hierarchy, keyboard navigation, and WCAG AA minimum color contrast. Alert states must remain distinguishable for colorblind users and cannot rely on color alone.
- **Component reuse:** Build a shared component library instead of one-off implementations for each page.

### Product-Specific UX Requirements

- Live feeds must load quickly and clearly indicate `connected`, `reconnecting`, or `offline` status. A silent live-feed failure is unacceptable for a security tool.
- Alerts should be visually distinct by severity and type, using icons and labels in addition to color.
- Incident screenshots must be viewable at full resolution.
- History search and filtering must be fast and default to a sensible recent time range rather than loading all-time history.

## 2. Color and Theme

### Primary, Secondary, and Accent Colors

| Role | Color | Hex | Usage |
| --- | --- | --- | --- |
| Primary | Deep blue | `#1E3A8A` | Navigation, primary buttons, headers |
| Secondary | Slate gray | `#475569` | Secondary text, borders, inactive states |
| Accent | Cyan | `#06B6D4` | Interactive highlights, active navigation, links |

### Background and Surface Colors

| Role | Light mode | Dark mode |
| --- | --- | --- |
| Background | `#F8FAFC` | `#0F172A` |
| Surface/cards | `#FFFFFF` | `#1E293B` |
| Surface hover | `#F1F5F9` | `#334155` |

### Text Colors

| Role | Light mode | Dark mode |
| --- | --- | --- |
| Primary text | `#0F172A` | `#F1F5F9` |
| Secondary text | `#64748B` | `#94A3B8` |
| Disabled text | `#CBD5E1` | `#475569` |

### Semantic Colors

| State | Color | Hex | Usage |
| --- | --- | --- | --- |
| Success | Green | `#16A34A` | Healthy system, reviewed or resolved event |
| Warning | Amber | `#F59E0B` | Degraded state, such as Telegram unreachable or low-confidence detection |
| Error/Critical | Red | `#DC2626` | Active threat, system failure, or high-confidence incident |
| Info | Blue | `#2563EB` | Neutral notifications and informational banners |

### Threat-Type Colors

These colors may be used for dashboard bounding boxes and event badges, but each state must also include a text label or icon.

| Threat type | Hex |
| --- | --- |
| Fire | `#F97316` |
| Smoke | `#6B7280` |
| Weapon | `#DC2626` |
| Violence | `#991B1B` |
| Accident | `#EA580C` |

### Theme Support

- Both light and dark themes are required.
- Follow the operating system preference by default using `prefers-color-scheme`.
- Provide a manual theme override.
- Persist the selected theme according to the preference-storage rules in Section 5.

## 3. Fonts and Typography

### Primary Font Family

Use **Inter**, with the following fallback stack:

```css
font-family: Inter, -apple-system, "Segoe UI", Roboto, sans-serif;
```

### Heading Styles

| Element | Size | Weight | Line height |
| --- | ---: | --- | ---: |
| H1 | 28px | Bold (700) | 1.3 |
| H2 | 22px | SemiBold (600) | 1.35 |
| H3 | 18px | SemiBold (600) | 1.4 |
| H4 | 16px | Medium (500) | 1.4 |

### Body Text Styles

| Element | Size | Weight | Line height |
| --- | ---: | --- | ---: |
| Body/default | 14px | Regular (400) | 1.5 |
| Body small/meta | 12px | Regular (400) | 1.5 |
| Body emphasized | 14px | Medium (500) | 1.5 |

### Type Scale

```css
12px / 1.5  /* captions, timestamps, metadata */
14px / 1.5  /* body text, form labels */
16px / 1.4  /* default UI text, buttons */
18px / 1.4  /* H3, card titles */
22px / 1.35 /* H2, section headers */
28px / 1.3  /* H1, page titles */
```

### Font Weights

- **Regular (400):** Body copy.
- **Medium (500):** Emphasized text, active navigation items, and buttons.
- **SemiBold (600):** Subheadings and card titles.
- **Bold (700):** Page titles and critical alert text.

## 4. Shared Components

The UI should use reusable components for:

- Event cards.
- Stat cards.
- Confidence badges.
- Threat-type badges.
- Connection-status indicators.
- Video players and MJPEG feed containers.
- Alert banners.
- Search and filter controls.
- Full-resolution screenshot viewers.
- Responsive navigation and sidebar layouts.

## 5. Persisted UI Preferences

The following preferences must persist across sessions:

- Theme mode: light, dark, or system.
- Language preference, if multi-language support is added.
- Sidebar and layout state: collapsed or expanded.
- Default History filters, such as the last viewed date range and event type.
- Dashboard camera layout, including pinned or visible feeds when multiple sources exist.
- Notification preferences, including which event types trigger Telegram alerts.

### Storage Rules

- After Phase 7 authentication exists, persist preferences server-side per authenticated user in the backend database.
- Before authentication exists, in-memory or session-based state is acceptable for prototyping only.
- Do not use browser `localStorage` or `sessionStorage` for preferences in React or artifact-based UI components, as prohibited by `Rules.md`.
