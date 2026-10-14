# Case 02 — investigation report

## 1. Executive summary

The service-door camera shows an orange-coated figure with a case matching the prototype at displayed 18:19. Its documented +5-minute offset places the frame at 18:14, inside the 18:00–18:18 disappearance window and aligned with Eli’s service-door credential entry. The most likely account is that Eli, or someone using his coat and credential, was involved in moving the prototype through or near the service route. Eli is the leading suspect, but the image does not show the removal and the badge direction is ENTRY, so an outbound theft sequence cannot be asserted. [V01, V02, V04, V05, V09, V10, D01, D03]

## 2. Evidence inventory

All 10 images were visually inspected, and all three document exhibits plus the case brief were read. Exhibit IDs are local to this case. The brief supplies the five coat assignments; these are not biometric identification.

### V01 — Floor plan

- Source: `images/V01.png`.
- Timestamp: No event timestamp supplied.
- Direct observation: The schematic connects the lab through the east corridor to the east exit. A second link joins the lab and service corridor, labelled UNMONITORED LINK TO LAB. A cafeteria is drawn separately.
- Interpretation: Both the east route and service link provide possible approaches to the lab.
- Uncertainty: No scale, travel times, door permissions, or complete loading-bay/reception connections are given. The drawing does not establish that anyone used either route.

### V02 — Prototype last visible

- Source: `images/V02.png`.
- Timestamp: 18:00.
- Direct observation: The LAB frame labelled CAMERA 18:00 shows a gray rectangular case/object with a black triangular marking on the brown bench.
- Interpretation: With the case brief and V09, this is the prototype reference appearance and last confirmed presence.
- Uncertainty: The schematic shows exterior appearance, not a serial number or contents.

### V03 — East corridor

- Source: `images/V03.png`.
- Timestamp: 18:10.
- Direct observation: The EAST CORRIDOR frame labelled CAMERA 18:10 shows one teal-coated figure, with no carried object drawn.
- Interpretation: Appearance is consistent with Nora’s assigned coat; D01 records Nora’s credential entering this corridor at the same minute.
- Uncertainty: Coat and badge correspondence is not biometric identification. One still does not show the figure’s subsequent route or hidden possessions.

### V04 — Service-door object

- Source: `images/V04.png`.
- Timestamp: 18:19 displayed; 18:14 corrected.
- Direct observation: The SERVICE DOOR frame labelled CAMERA 18:19 shows an orange-coated figure beside a gray rectangular case with a black triangle, positioned as a carried object.
- Interpretation: V10 and D03 report a +5-minute service-camera offset: assuming camera time = common time + 5 minutes, this frame corresponds to 18:14. It aligns with Eli’s service-door credential entry, and the object matches V02/V09.
- Uncertainty: A still gives no movement direction; D01 records ENTRY, not EXIT. Identity, actual lab entry/removal, object uniqueness, and subsequent destination remain unproven.

### V05 — Prototype missing

- Source: `images/V05.png`.
- Timestamp: 18:18.
- Direct observation: The LAB frame labelled CAMERA 18:18 shows the bench without the gray triangle-marked object seen in V02.
- Interpretation: The prototype is absent from its shown location by 18:18, consistent with the brief.
- Uncertainty: The image does not show the removal or exclude relocation elsewhere in the lab.

### V06 — Cafeteria

- Source: `images/V06.png`.
- Timestamp: 18:12.
- Direct observation: The CAFETERIA frame labelled CAMERA 18:12 shows one blue-coated figure and no carried object drawn.
- Interpretation: Consistent with Theo’s assigned coat and the cafeteria entry under Theo’s credential in D01.
- Uncertainty: It corroborates one moment, not Theo’s claim of remaining there continuously.

### V07 — Reception

- Source: `images/V07.png`.
- Timestamp: 18:13.
- Direct observation: The RECEPTION frame labelled CAMERA 18:13 shows one red-coated figure and no carried object drawn.
- Interpretation: Consistent with Ada’s assigned coat and the reception entry under Ada’s credential in D01.
- Uncertainty: A still and entry record cannot establish Ada’s location throughout the 18-minute window.

### V08 — Loading bay box

- Source: `images/V08.png`.
- Timestamp: 18:11.
- Direct observation: The LOADING BAY frame labelled CAMERA 18:11 shows one purple-coated figure beside a plain brown rectangular box. No triangle marking is drawn on the box.
- Interpretation: Consistent with Maya carrying a cardboard supply box as stated in D02 and with the consumables-box request in D03. The visible object differs from V02/V09.
- Uncertainty: Material and contents cannot be established from a schematic; the box could conceal something, but no supplied evidence shows that it does. Coat colour does not prove identity.

### V09 — Object reference

- Source: `images/V09.png`.
- Timestamp: No event timestamp supplied.
- Direct observation: The OBJECT DETAIL / CAMERA REFERENCE image shows a gray rectangular case/object with a black triangle on the bench; no event time is given.
- Interpretation: The distinctive exterior supports comparing the prototype in V02 with a visually matching object elsewhere.
- Uncertainty: A matching exterior is not unique identification or proof of contents.

### V10 — Service-camera clock notice

- Source: `images/V10.png`.
- Timestamp: No event timestamp supplied.
- Direct observation: The SERVICE CAMERA / CAMERA MAINTENANCE exhibit reads CLOCK OFFSET +5 MINUTES.
- Interpretation: Together with D03 this supports subtracting five minutes from the service-door frame’s displayed 18:19 to obtain 18:14.
- Uncertainty: No measurement history or error bound is supplied. Apply the correction only to the service camera; the service corridor’s unmonitored lab link in V01 still leaves a coverage gap.

### D01 — Access records

- Source: `documents/D01_access.csv`.
- Timestamp: 18:10–18:14.
- Direct observation: Four rows: 18:10 Nora Vale / EAST_CORRIDOR / ENTRY; 18:12 Theo Park / CAFETERIA / ENTRY; 18:13 Ada Finch / RECEPTION / ENTRY; 18:14 Eli Stone / SERVICE_DOOR / ENTRY.
- Interpretation: The Eli service-door record aligns with corrected V04; the other records align with the corresponding coat-colour frames.
- Uncertainty: ENTRY does not document taking an object out of the building. Credentials are not biometric identities; no Nora exit record or continuous movement history is supplied.

### D02 — Witness statements

- Source: `documents/D02_witnesses.md`.
- Timestamp: No event timestamp supplied.
- Direct observation: Five explicitly unverified statements: Nora says she only visited the east corridor and left; Eli says he did not approach the lab after 18:00; Maya says she carried a cardboard supply box at 18:11; Theo says he remained in the cafeteria from 18:12; Ada says she staffed reception.
- Interpretation: Statements supply claims to test against the images and access records, rather than established alibis.
- Uncertainty: No interview times, independent identity authentication, full movement accounts, or corroboration of continuous presence are supplied.

### D03 — Internal messages

- Source: `documents/D03_messages.md`.
- Timestamp: 17:00; 17:10; 17:20.
- Direct observation: 17:00 Eli says his project needs the prototype tomorrow. 17:10 Maya requests moving the cardboard consumables box to the loading bay. 17:20 Security says coat descriptions come from shift assignments and doors log badge credentials, not biometric identity. Service camera has a +5 minute clock offset.
- Interpretation: Eli’s message establishes a stated need, not theft. Maya’s request supports a routine-box explanation. Security limits identity attribution and clarifies coverage or timing.
- Uncertainty: Messages do not prove intent, compliance with the box request, custody of badges/coats, or the actual removal sequence.

## 3. Timeline

“Confirmed record” describes what the exhibit records, not authenticated personal identity.

| Time | Status | Event and sources |
|---|---|---|
| 17:00 | confirmed record | Eli’s message states a need for the prototype tomorrow. This is a recorded statement, not proof of intent. [D03] |
| 17:10 | confirmed record | Maya requests moving the cardboard consumables box to the loading bay. [D03] |
| 17:20 | confirmed record | Security records the coat/badge identity limitations and service-camera +5-minute offset. [D03] |
| 18:00 | confirmed record | Gray triangle-marked prototype/case is visible on the lab bench. [V02, V09] |
| 18:10 | confirmed record | A teal-coated figure is in the east corridor; Nora’s credential logs ENTRY there. [V03, D01, D03] |
| 18:11 | confirmed record | A purple-coated figure is with a plain brown box at the loading bay, consistent with Maya’s account and the box request. [V08, D02, D03] |
| 18:12 | confirmed record | A blue-coated figure is at the cafeteria; Theo’s credential logs ENTRY. Continued presence is unconfirmed. [V06, D01, D02] |
| 18:13 | confirmed record | A red-coated figure is at reception; Ada’s credential logs ENTRY. The full interval is unaccounted for. [V07, D01, D02] |
| 18:14 | corrected record | Service-door image shows an orange-coated figure with a gray triangle-marked case. Eli’s credential logs ENTRY. Camera display 18:19 minus documented five-minute offset gives 18:14. [V04, V09, V10, D01, D03] |
| 18:18 | confirmed record | The lab bench lacks the prototype visible at 18:00; the case brief reports it discovered missing. [V02, V05] |

### Assumptions

- All times are same-day local clock labels; no date or timezone is supplied. Unspecified cameras and the badge log are provisionally treated as sharing a clock, without an independent synchronisation audit. [V02, V03, V05, V06, V07, V08, D01]
- Confirmed record means the supplied exhibit contains the observation; it does not authenticate a human identity, prove a statement true, or certify record completeness. [D01, D02, D03]
- The assignment’s coat-to-name mapping is a contextual association only. Badge entries identify credentials rather than their human users. [D03]
- The +5-minute notice means the service camera runs five minutes ahead: 18:19 − 00:05 = 18:14. No correction is applied to any other camera. [V04, V10, D03]

### Missing intervals and probable movements

- No image shows the removal itself. The directly established absence window is after the 18:00 presence and by the 18:18 absence. [V02, V05]
- The east-corridor visit is only a snapshot; movement between that location and the lab is not continuously observed. [V01, V03]
- The service link to the lab is unmonitored, so unrecorded or unauthenticated movement remains possible. [V01, V10, D03]
- The cafeteria and reception snapshots do not cover the full incident window; there is no supplied travel-time model or continuous alibi. [V01, V06, V07, D01, D02]
- If the matching case in V04 is the same prototype from V02, it was displaced from the bench by 18:14; this narrower bound is conditional on object identity. Its route before and after V04 is not shown. [V02, V04, V09]

## 4. Suspect analysis

### Nora Vale

**Possible opportunity, but no direct prototype-possession evidence.** [V01, V03, D01, D02, D03]

- **Opportunity:** East corridor connects to the lab and is observed at 18:10.
- **Access:** Nora’s credential logs east-corridor ENTRY at 18:10; no subsequent exit is logged in the supplied rows.
- **Timeline consistency:** The 18:10 observation is consistent with visiting the corridor. Her claimed departure and subsequent whereabouts are unverified.
- **Supporting evidence:** Proximity to the lab via the east corridor creates opportunity.
- **Exculpatory evidence:** No object is drawn with the teal figure at 18:10; no image shows Nora entering the lab or removing the prototype.
- **Uncertainty:** Proximity alone does not establish removal. A sparse log cannot prove absence from the lab.

### Eli Stone

**Leading suspect; probable attribution, not definitive.** [V01, V04, V09, V10, D01, D02, D03]

- **Opportunity:** The service corridor links to the lab; an orange-coated figure is with a matching case at the service door at corrected 18:14.
- **Access:** Eli’s credential logs service-door ENTRY at 18:14.
- **Timeline consistency:** The credential event near the lab challenges his denial, conditional on credential use and what he means by “approach.” The corrected orange-coat/object image strengthens that challenge.
- **Supporting evidence:** Stated need for the prototype tomorrow; orange appearance, matching case, and corrected badge-time alignment.
- **Exculpatory evidence:** No direct lab-removal image exists. The access direction is ENTRY, so an exit/removal trajectory is not established.
- **Uncertainty:** Need is not proof of misconduct; badge sharing and coat reassignment remain possible. Actual direction, authorisation, and object custody before/after the frame are unknown.

### Maya Reed

**Routine-box explanation better supported than prototype removal.** [V08, V09, D02, D03]

- **Opportunity:** At 18:11 a purple figure is at the loading bay; later movements are not shown.
- **Access:** No Maya badge event is supplied. The loading-bay image is appearance evidence only.
- **Timeline consistency:** The brown-box image and request support her 18:11 statement. Her whereabouts after that frame are not established.
- **Supporting evidence:** She is associated with a carried box, but no observation identifies it as the prototype.
- **Exculpatory evidence:** The brown box lacks the prototype’s visible gray exterior and triangle. The consumables request provides a coherent innocent explanation.
- **Uncertainty:** Contents of the brown box are unknown. Concealment is possible in principle but unsupported by a visible transfer or other specific evidence.

### Theo Park

**Limited implication; partial corroboration, not a complete alibi.** [V01, V06, D01, D02, D03]

- **Opportunity:** The full period before 18:12 and movements after the single cafeteria frame remain unobserved.
- **Access:** Theo’s credential logs cafeteria ENTRY at 18:12; no lab entry is supplied.
- **Timeline consistency:** The blue figure and badge event support being at the cafeteria at 18:12, but not remaining there continuously.
- **Supporting evidence:** No specific evidence links Theo to the prototype or its removal.
- **Exculpatory evidence:** Cafeteria appearance and credential align with the start of his account.
- **Uncertainty:** Identity and continuous presence are unverified. Incomplete records cannot exclude later access.

### Ada Finch

**Limited implication; partial corroboration, not a complete alibi.** [V07, D01, D02, D03]

- **Opportunity:** Her location before and after the 18:13 reception frame is not continuously documented.
- **Access:** Ada’s credential logs reception ENTRY at 18:13; no lab entry is supplied.
- **Timeline consistency:** The red figure and badge event support reception presence at one moment, consistent with her broad statement.
- **Supporting evidence:** No specific evidence links Ada to the prototype or its removal.
- **Exculpatory evidence:** Reception appearance and credential corroborate part of her account.
- **Uncertainty:** The statement supplies no shift interval. Identity and full-window whereabouts are not established.

## 5. Key deductions

- Subtract the documented offset, rather than treating the service frame as one minute after discovery: 18:19 − 5 minutes = 18:14. This independently aligns with the service-door access record. [V04, V10, D01, D03]
- Corrected timing, orange appearance, the triangle-marked object, and Eli’s badge event jointly outweigh his motive statement alone and the other suspects’ incidental locations. [V04, V09, V10, D01, D03]
- The service link supplies a plausible lab approach, but ENTRY at the service door and a directionless still do not establish an exit, a pickup order, or a complete route. [V01, V04, D01]
- Maya’s box has a different visible exterior and a routine consumables explanation. [V08, V09, D02, D03]

## 6. Contradictions

- The displayed 18:19 service time seems later than the 18:18 discovery only before clock correction; V10/D03 resolve that apparent conflict to 18:14. [V04, V05, V10, D03]
- Eli’s denial of approaching the lab is in tension with the service-door credential and orange figure carrying a matching case, conditional on personal identity and the meaning of “approach.” [V01, V04, D01, D02, D03]
- The access event is ENTRY. Calling it an exit or treating V04 as proof of an outbound removal would contradict the record’s direction and overread a still. [V04, D01]
- V01 labels the lab link unmonitored while V04 images the service door. These can coexist: door coverage does not establish corridor/lab coverage. [V01, V04]

## 7. Final conclusion

The service-door camera shows an orange-coated figure with a case matching the prototype at displayed 18:19. Its documented +5-minute offset places the frame at 18:14, inside the 18:00–18:18 disappearance window and aligned with Eli’s service-door credential entry. The most likely account is that Eli, or someone using his coat and credential, was involved in moving the prototype through or near the service route. Eli is the leading suspect, but the image does not show the removal and the badge direction is ENTRY, so an outbound theft sequence cannot be asserted. [V01, V02, V04, V05, V09, V10, D01, D03]

**No responsible individual is definitively identified.**

### Plausible alternatives

- A different person could be using Eli’s coat and badge, or the matching case could be a different object; no serial identifier is shown. [V04, V09, D01, D03]
- The person could be entering with or legitimately relocating the object. The ENTRY event and lack of movement footage leave transfer direction and authorisation unresolved. [V04, D01]
- An independent removal by another person through the unmonitored link or east approach remains possible if the apparent object/identity match is misleading. [V01, V03, V04, V09]

## 8. Confidence and limitations

- **Overall:** Moderate for Eli’s involvement in moving the prototype; not definitive.
- **Observed change:** High: object present at 18:00 and absent from the bench at 18:18.
- **Time correction:** High conditional on the documented +5-minute offset applying to V04 and meaning camera clock ahead.
- **Route and possession:** Moderate to high for an orange figure with a matching case at corrected 18:14; low for a specific outbound route.
- **Individual identity:** Moderate: coat, badge, and corrected time align but are not biometric identification.
- **Intent or authorisation:** Undetermined; possession or movement does not by itself prove unauthorised theft.

- Synthetic schematics simplify persons, objects, and locations. They support only visible features, not faces, fingerprints, serial numbers, precise distances, or hidden contents. [V01, V02, V03, V04, V05, V06, V07, V08, V09]
- Badge credentials and coat assignments are identity proxies; sharing, misuse, or reassignment is not ruled out or positively demonstrated. [D01, D03]
- No uninterrupted removal footage, complete access history, authorisation record, recovery evidence, or full-window alibi is supplied. [V01, V02, V05, V10, D01, D02]
- Confidence labels are qualitative judgments, not calibrated probabilities or findings of legal guilt. [V02, V04, V05, D01, D03]

## 9. Recommended next investigative steps

- Confirm the offset sign, camera identity, stability, and time reference against maintenance records and raw footage; preserve both original and corrected timestamps. [V04, V10, D03]
- Obtain continuous service-door and lab footage plus reader configuration to resolve ENTRY direction, pickup order, and destination. [V01, V02, V04, V05, D01]
- Authenticate Eli’s badge and coat use; interview him about the matching case and denial, and verify the prototype’s identity and any authorised transfer. [V04, V09, D01, D02, D03]
- Extend the other suspects’ movement records and inspect the supply-box contents if recoverable, without treating a box or project need as proof. [V03, V06, V07, V08, D01, D02, D03]
