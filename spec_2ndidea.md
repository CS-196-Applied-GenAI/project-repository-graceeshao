# Porch — Product Specification

## Overview

**Porch** is a social events app that lets users share what they're doing and drop in on friends' activities, reducing social friction and making spontaneous hangouts effortless. Think of it as "office hours for your social life" — your friends broadcast their plans, and you can soft-RSVP to join without the awkwardness of formal invitations.

**Target audience:** Primarily young professionals and students, but designed for broad appeal.

**Platform:** Responsive web application (PWA) that works on both mobile and desktop browsers. No native app for v1.

**Monetization:** Free. No ads, no paid tiers for v1.

---

## Core Concepts

### Events

An event is a calendar block representing something a user is doing. Events contain:

- **Activity name** (e.g., "Pilates," "Coffee at Intelligentsia")
- **Location** (specific venue/address — static only, no live tracking)
- **Date and time**
- **Duration**
- **Attendance list** (visible to anyone who can see the event)
- **Auto-suggested category tag** (e.g., fitness, food & drinks, study, outdoors, nightlife) — creator can override

Events can be:

- **One-time** or **recurring** (supports the same recurrence patterns as Google Calendar: daily, weekly, custom)
- **Planned ahead** or **spontaneous** ("I'm here now")
- **Scoped to specific friend groups** or visible to all friends

### Users and Profiles

Profiles are minimal — inspired by Beli:

- Name
- Photo
- No bio, no stats, no public event history

### Social Graph

- **Mutual follow model**: User A sends a friend request, User B accepts. Both can now see each other's events.
- **Only mutual friends can see your profile and events.** No public visibility.
- Users can organize friends into **groups** (e.g., "gym crew," "work people," "college friends").
- A friend can belong to **multiple groups**.

### Groups as Access Control

Groups are the privacy layer for events:

- When creating an event, the user selects which groups can see it — or chooses "all friends."
- Only members of the allowed groups can see the event, view the guest list, and RSVP.
- If a user is not in an allowed group, the event is completely invisible to them.

---

## Key Features

### 1. Event Creation (Manual)

Users create events by entering:

- Activity name
- Location
- Date and time
- Duration
- Visibility (specific groups or all friends)

The app auto-suggests a category tag based on the activity name. The creator can accept or change it.

### 2. Soft RSVP

When viewing a friend's event, users can indicate:

- **Interested** — low-commitment signal, "I might come"
- **Going** — firmer commitment, "I'll be there"

This is the core mechanic for reducing social friction. No formal invitations, no pressure.

### 3. Calendar View

- Displays the user's own events and all visible friends' events in a standard calendar layout.
- **Color-coded by friend group** — each group gets its own color, so users can see at a glance which social circles are active.
- Tapping an event opens a detail view showing: activity, time, location, duration, who's interested/going, and the RSVP buttons.
- **Desktop layout:** Calendar on the left, feed on the right (side-by-side).
- **Mobile layout:** Tabbed navigation to switch between calendar view and feed view.

### 4. Google Calendar Suggestion Integration

- Users can connect their Google account in settings.
- The app reads their GCal events (read-only — no writing back to GCal in v1).
- Surfaces suggestions like: "You have 'Pilates at 5pm' — want to share this with friends?"
- Users can accept (creates a Porch event) or ignore the suggestion.

### 5. Friend System (Mutual Follow + Groups)

- Send and accept friend requests.
- Create and manage friend groups from a dedicated screen.
- Assign friends to one or more groups.
- Groups are used for per-event visibility control.

### 6. Feed View

- A scrollable list/card view of upcoming friends' events.
- **Sorting:** Chronological (soonest first) as the primary sort, with social relevance boosting — events with more friends attending are surfaced higher.
- Users can **filter the feed by category tags** (e.g., "show me only fitness events this week").

### 7. "I'm Here Now" Spontaneous Events

- A prominent "I'm here" button for quick posting.
- Auto-detects current location and pre-fills the venue.
- User types a quick activity name, picks visibility groups, and selects a duration.
- The event appears on the calendar as a block starting from the current time.
- Designed for speed — three taps and you're broadcasting.

### 8. Recurring Events

- Same recurrence options as Google Calendar (daily, weekly, custom patterns).
- Set it once, and the event auto-posts on the schedule.
- Friends always know about your regular activities.

### 9. Event History & Smart Suggestions

- Past events are retained, not deleted.
- Users can look back on their history (e.g., "we went to that bar three times last month").
- Over time, the app can surface suggestions based on patterns (e.g., "you and Jake usually grab coffee on Fridays").

### 10. Auto-Tagging & Feed Filters

- Events are auto-tagged with a category based on the activity name (fitness, food & drinks, study, outdoors, nightlife, etc.).
- Creator can override the auto-suggested tag.
- Feed view supports filtering by these tags.

---

## Notifications

Only three notification types for v1 (intentionally minimal to avoid fatigue):

1. **Someone RSVPed to your event** — "Jake is interested in your Pilates class"
2. **Multiple friends going to the same event** — "3 friends are heading to happy hour at 6"
3. **Interest nudge** — Sent ~1 hour before an event to users who marked "interested": "Pilates is in 1 hour — still thinking about it?" Lets them upgrade to "going" or quietly drop off. Prevents signal degradation.

---

## Onboarding Flow

1. **Sign up with phone number.**
2. **Group-first invite flow (primary path):** Prompt the user to create their first group (e.g., "gym crew," "college friends") and generate a shareable invite link they can drop into an existing group chat (iMessage, WhatsApp, etc.). This gets multiple friends onboarded simultaneously, solving the cold start problem.
3. Upon first open, show any pending group invitations — "3 friends already invited you!" to deliver instant value.
4. **Connect Google Calendar** early in onboarding for event suggestions.
5. **Prompt to post a first event** — auto-suggest from GCal if connected, or nudge with low-key examples ("What are you up to this week?"). First event should take under 10 seconds.
6. Browse friends' events if any are already posted.

---

## Communication

There is **no in-app messaging**. When users want to coordinate, they are directed to existing channels (iMessage, texting). Porch focuses purely on discovery and intent signaling.

---

## Privacy & Safety (v1)

- **Mutual friends only:** No one can see your profile or events unless you've mutually accepted a friend request.
- **Static location only:** Events show the posted venue/address. No live location tracking.
- **Attendance visibility:** Anyone who can see an event can see who's interested/going. This is intentional — social proof is a core part of the value.
- **Group-based access control:** Events are invisible to anyone not in the allowed groups.
- Block, report, and mute features are **deferred to post-v1**.

---

## Desktop vs. Mobile Layout

| Aspect | Desktop | Mobile |
|--------|---------|--------|
| Main layout | Side-by-side: calendar (left) + feed (right) | Tabbed: switch between calendar and feed |
| Event creation | Same flow | Same flow, "I'm here" button prominent |
| Navigation | Top or side nav | Bottom tab bar |

---

## Adoption Risks & Mitigations

### 1. Cold Start Problem (Critical)

The app is worthless until your friends are on it. This is the existential risk.

**Mitigations:**

- **Group-first onboarding (primary strategy):** The main onboarding path should NOT be "sign up and invite friends one by one." Instead, the core flow is: create a group → drop a shareable invite link into an existing group chat (iMessage, WhatsApp, Discord) → the whole crew joins together. If 5–6 people from a friend group join at once, the app is instantly useful for all of them.
- **Pre-populated value in invite links:** When someone receives an invite link, the landing page should show the inviter's upcoming events before they even sign up — e.g., "Jake is at Intelligentsia right now, 2 others are going." Make the app feel alive before they commit to joining.
- **Immediate GCal prompt:** During onboarding, prompt for GCal connection early and auto-suggest events to share. The first posted event should take under 10 seconds.
- **Lower the bar for first event:** Nudge hard after sign-up — "What are you doing this week? Post one thing." The faster someone posts, the faster their friends see value.

### 2. "I Don't Do Enough Interesting Stuff"

Users will feel self-conscious posting mundane activities. There's a psychological barrier where people think their plans aren't worth sharing.

**Mitigations:**

- **Brand tone should normalize the mundane.** The whole point is "I'm just on my porch, come hang." It's about being available, not impressive.
- **Onboarding examples should be deliberately low-key:** "studying at the library," "walking the dog," "grabbing a coffee," "working from Starbucks." Not "rooftop party" or "VIP dinner."
- **Consider framing events as "open doors" in copy and UX** — you're not hosting an event, you're just leaving the door open in case someone wants to swing by.

### 3. "This Feels Like Surveillance"

Sharing your schedule and location with friends regularly can feel like social monitoring — "why didn't you come to my thing?" or "I see you went out without me."

**Mitigations:**

- **No guilt mechanics.** No streaks, no "you haven't posted in 3 days" nudges, no activity scores. Silence is perfectly fine.
- **Emphasize opt-in sharing.** The app reads GCal but only suggests — it never auto-posts. Users share only what they explicitly choose to share.
- **Group scoping reduces exposure.** You're not broadcasting to everyone, just your gym crew or your close friends. This makes sharing feel targeted rather than public.

### 4. "I Already Have Group Chats for This"

Most friend groups already coordinate through iMessage or WhatsApp. "Anyone want to grab dinner?" works fine in a group chat.

**Mitigations:**

- **Position Porch as passive discovery, not active coordination.** Group chats require someone to initiate. Porch is ambient — it's always there, no one has to be the person who texts the group again.
- **Cross-circle visibility is the killer feature.** Your gym friends and your work friends aren't in the same group chat, but on Porch you might discover both groups are heading to the same neighborhood on Friday night. Group chats can't do that.
- **Use this messaging in marketing and onboarding** — "see plans you'd never hear about in the group chat."

### 5. App Fatigue ("Another App to Check")

People don't want another app to maintain and check daily.

**Mitigations:**

- **Notifications do the heavy lifting.** The two notification types (RSVP on your event, multiple friends going somewhere) should be compelling enough to pull people back without requiring daily check-ins.
- **Desktop web app helps.** Users can keep a Porch tab open alongside GCal at work — no extra app to download or switch to.
- **Future GCal write-back (post-v1)** will let users see friends' events in their existing calendar, removing the need to open Porch at all for consumption.

### 6. Commitment Anxiety / Signal Degradation

Soft RSVPs reduce pressure, but if everyone is always "interested" and no one ever commits to "going," the signal becomes meaningless and people stop trusting it.

**Mitigations:**

- **Gentle nudge to convert:** As an event approaches (e.g., 1 hour before), send a lightweight prompt to "interested" users: "Pilates is in 1 hour — still thinking about it?" Let them upgrade to "going" or quietly drop off.
- **Show both counts clearly.** "3 interested, 1 going" tells a different story than "4 interested." Make the distinction visible and meaningful.

---

## Future Considerations (Post-v1)

- **Native iOS / Android apps** (or wrapping the PWA)
- **GCal write-back** — add friends' events you RSVP to into your own Google Calendar
- **Block, report, and mute functionality**
- **Enhanced smart suggestions** powered by event history
- **Map view** — see what friends are doing nearby
- **Deeper notification controls**

---

## Feature Priority (v1 Roadmap)

Ordered by priority — if scope must be cut, work top-down:

1. **Event creation (manual)** — core mechanic
2. **Soft RSVP (interested/going)** — core interaction
3. **Calendar view** — primary way to see events
4. **GCal suggestion integration** — smart assist for event creation
5. **Friend system (mutual follow + groups)** — social graph and privacy
6. **Feed view** — secondary browsing experience
7. **"I'm here now" spontaneous events** — real-time broadcasting
8. **Recurring events** — convenience feature
9. **Event history & smart suggestions** — long-term engagement
10. **Auto-tagging & feed filters** — polish and discoverability

---

## Technical Notes

- **Responsive web app (PWA)** — single codebase for mobile and desktop
- **Push notifications** via web push API (supported on iOS Safari)
- **Google Calendar integration** — OAuth2, read-only access to user's calendar via Google Calendar API
- **Location services** — browser geolocation API for "I'm here now" feature
- **Tech stack:** Left to developer discretion (recommended: React or Next.js frontend, with a backend/API layer and database of choice)
