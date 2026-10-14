# INVESTIGATION REPORT: Missing Laboratory Prototype (Case_01)

## 1. Executive Summary

This investigation examined the disappearance of a laboratory prototype between 18:00 and 18:18. Visual evidence from camera feeds, access logs, witness statements, internal messages, and building schematics were analyzed.

**Key Finding:** Visual evidence shows a person in a teal coat entering the east corridor at 18:10 (V03) and exiting the east exit at 18:14 carrying an object matching the prototype description (V04). By 18:18, the prototype was confirmed missing from the lab (V05).

**Critical Limitations:**
- Badge credentials establish credential use, not biometric identity
- Coat color is appearance evidence only, not conclusive identification
- Location snapshots are point-in-time observations, not continuous tracking
- Service corridor blind spot (V10) does NOT prove nobody used it during the incident window
- Witness statements are unverified and may be incomplete

**Conclusion:** Based on available visual evidence, a person matching Nora Vale's coat description (teal) is associated with taking the prototype. However, without biometric confirmation or continuous tracking, a definitive identification cannot be made with high confidence.

**Confidence Level:** 65% - Moderate confidence based on visual evidence correlation, but limited by blind spots and lack of biometric verification.

---

## 2. Evidence Inventory

### Visual Exhibits (V01-V10)
| Exhibit ID | Type | Timestamp | Location | Key Observation |
|------------|------|-----------|----------|------------------|
| V01 | Schematic | N/A | Building layout | Shows LAB, EAST CORRIDOR, EAST EXIT, SERVICE CORRIDOR (unmonitored), CAFETERIA |
| V02 | Camera feed | 18:00 | LAB | Prototype visible on table |
| V03 | Camera feed | 18:10 | EAST CORRIDOR | Person in teal coat enters corridor |
| V04 | Camera feed | 18:14 | EAST EXIT | Person in teal coat exits with prototype |
| V05 | Camera feed | 18:18 | LAB | Lab empty, prototype missing |
| V06 | Camera feed | 18:12 | CAFETERIA | Person in blue coat present |
| V07 | Camera feed | 18:13 | RECEPTION | Person in red coat present |
| V08 | Camera feed | 18:11 | LOADING BAY | Person in purple coat with cardboard box |
| V09 | Reference | N/A | N/A | Prototype visual reference (grey rectangle with black triangle) |
| V10 | Reference | N/A | N/A | Service corridor blind spot noted |

### Documentary Evidence (D01-D03)
| Document ID | Type | Key Information |
|-------------|------|------------------|
| D01_access.csv | Access log | Badge credential entries/exits with timestamps |
| D02_witnesses.md | Witness statements | Unverified claims from all five staff members |
| D03_messages.md | Internal messages | Eli's request (17:00), Maya's box move request (17:10), security notes |

### Staff Identity Reference
| Name | Coat Color | Role |
|------|------------|------|
| Nora Vale | Teal | Laboratory staff |
| Eli Stone | Orange | Project staff |
| Maya Reed | Purple | Logistics staff |
| Theo Park | Blue | Cafeteria staff |
| Ada Finch | Red | Reception staff |

**Important Note:** Coat color is evidence of appearance, not biometric identity. Badge credentials establish credential use only.

---

## 3. Timeline

| Time | Event | Source | Person Involved | Confidence |
|------|-------|--------|------------------|------------|
| 17:00 | Eli Stone requests prototype for tomorrow | D03_messages.md | Eli Stone (appearance-based) | Confirmed |
| 17:10 | Maya Reed requests cardboard box move to loading bay | D03_messages.md | Maya Reed (appearance-based) | Confirmed |
| 18:00 | Prototype confirmed present in lab | V02 | N/A | Confirmed |
| 18:10 | Person in teal coat enters EAST_CORRIDOR via badge credential | D01_access.csv + V03 | Nora Vale (appearance-based) | Confirmed |
| 18:10-18:14 | Person in teal coat takes prototype from lab | V03 + V04 + D01 | Nora Vale (appearance-based) | Probable |
| 18:11 | Maya Reed at loading bay with cardboard box | V08 + D03 | Maya Reed (appearance-based) | Confirmed |
| 18:12 | Person in blue coat enters CAFETERIA via badge credential | D01_access.csv + V06 | Theo Park (appearance-based) | Confirmed |
| 18:12 | Person in blue coat claims remained in cafeteria from 18:12 | D02_witnesses.md + V06 | Theo Park (appearance-based) | Unverified |
| 18:13 | Person in red coat enters RECEPTION via badge credential | D01_access.csv + V07 | Ada Finch (appearance-based) | Confirmed |
| 18:13 | Person in red coat claims staffed reception | D02_witnesses.md + V07 | Ada Finch (appearance-based) | Unverified |
| 18:14 | Person in teal coat exits EAST_EXIT carrying prototype visible in camera | D01_access.csv + V04 | Nora Vale (appearance-based) | Confirmed |
| 18:14-18:18 | Prototype transported from east exit to unknown location by person in teal coat | V04 + V05 | Nora Vale (appearance-based) | Probable |
| 18:18 | Lab empty except for brown object (no prototype), prototype confirmed missing | V05 | N/A | Confirmed |
| 18:18 | Prototype discovered missing from lab | Case brief | N/A | Discovery |

**Assumptions Used:**
- Person in teal coat entered the LAB from EAST_CORRIDOR after entering at 18:10
- The prototype was taken during person in teal coat's visit between 18:10-18:14
- No one else entered the lab area via monitored routes during this timeframe based on access logs
- Service corridor blind spot (V10) does NOT prove absence of use - cannot rule out unauthorized entry via this route

**Missing Intervals:**
- 18:14-18:18: Time between person in teal coat exiting east exit with prototype and discovery of missing prototype in lab. Prototype was already out of lab by 18:14, so theft occurred before this time.
- Service corridor access: No camera coverage for service corridor (V10 blind spot). Cannot rule out unauthorized entry via service corridor without additional evidence.

**Contradictory Timestamps:**
- Nora Vale witness statement claims "only visited east corridor and left" but V04 shows person in teal coat exiting east exit at 18:14 carrying prototype. Visual evidence contradicts witness statement - person in teal coat did take the prototype.

---

## 4. Suspect Analysis

### Nora Vale (Teal Coat)
**Opportunity:** High - Entered lab area at 18:10, exited with prototype at 18:14
**Access:** Confirmed via badge credential (D01_access.csv)
**Timeline Consistency:** Visual evidence shows presence in east corridor and exit with prototype
**Contradictions:** Witness statement claims only visited east corridor, but visual evidence shows prototype removal
**Supporting Evidence:** V03, V04 show teal coat person entering and exiting with prototype
**Exculpatory Evidence:** None identified
**Uncertainty:** Appearance-based identification only; no biometric verification
**Assessment:** Most likely responsible based on visual evidence correlation

### Eli Stone (Orange Coat)
**Opportunity:** Low - No access logs show entry to lab area during incident window
**Access:** Not confirmed in access logs for 18:10-18:18 timeframe
**Timeline Consistency:** Claims no approach to lab after 18:00
**Contradictions:** None identified
**Supporting Evidence:** D03_messages shows prototype request at 17:00, but no access during incident window
**Exculpatory Evidence:** No access logs show entry; witness statement supports alibi
**Uncertainty:** Cannot rule out unauthorized entry via service corridor blind spot
**Assessment:** Unlikely responsible based on available evidence

### Maya Reed (Purple Coat)
**Opportunity:** Low - At loading bay at 18:11 with cardboard box
**Access:** Confirmed via badge credential for loading bay area
**Timeline Consistency:** Visual evidence shows presence at loading bay
**Contradictions:** None identified
**Supporting Evidence:** V08 shows purple coat person with cardboard box; D03_messages confirms box move request
**Exculpatory Evidence:** Location and activity consistent with legitimate work
**Uncertainty:** Appearance-based identification only
**Assessment:** Unlikely responsible based on available evidence

### Theo Park (Blue Coat)
**Opportunity:** Low - At cafeteria at 18:12
**Access:** Confirmed via badge credential for cafeteria area
**Timeline Consistency:** Visual evidence shows presence in cafeteria
**Contradictions:** Witness statement claims remained in cafeteria from 18:12
**Supporting Evidence:** V06 shows blue coat person in cafeteria
**Exculpatory Evidence:** Location consistent with alibi claim
**Uncertainty:** Appearance-based identification only; cannot rule out brief lab visit before/after 18:12
**Assessment:** Unlikely responsible based on available evidence

### Ada Finch (Red Coat)
**Opportunity:** Low - At reception at 18:13
**Access:** Confirmed via badge credential for reception area
**Timeline Consistency:** Visual evidence shows presence at reception
**Contradictions:** Witness statement claims staffed reception
**Supporting Evidence:** V07 shows red coat person at reception
**Exculpatory Evidence:** Location consistent with alibi claim
**Uncertainty:** Appearance-based identification only; cannot rule out brief lab visit before/after 18:13
**Assessment:** Unlikely responsible based on available evidence

---

## 5. Key Deductions

1. **Prototype removal occurred between 18:10-18:14**: Visual evidence shows person in teal coat entering east corridor at 18:10 (V03) and exiting with prototype at 18:14 (V04). Lab camera at 18:18 (V05) confirms prototype missing.

2. **Teal coat person had access to lab**: Badge credential shows entry via east corridor, which connects to lab area per schematic V01.

3. **Service corridor blind spot does not exonerate anyone**: V10 notes camera maintenance on service corridor. Absence of footage does NOT prove absence of use during incident window.

4. **Witness statements are unverified**: All five staff provided statements (D02_witnesses.md) but these are not corroborated by continuous tracking. Point-in-time snapshots do not establish continuous whereabouts.

5. **Badge credentials establish credential use, not identity**: D01_access.csv shows badge usage but does not confirm biometric identity. Coat color is appearance evidence only.

6. **Motive exists for Eli Stone**: D03_messages shows Eli requested prototype at 17:00, but no access during incident window makes him unlikely perpetrator despite motive.

---

## 6. Contradictions

| Source | Claim | Contradicted By | Resolution |
|--------|-------|-----------------|-------------|
| Nora Vale witness statement (D02_witnesses.md) | "Only visited east corridor and left" | V04 shows person in teal coat exiting east exit at 18:14 carrying prototype | Visual evidence contradicts witness statement - person in teal coat did take the prototype |
| Service corridor camera status (V10) | "Camera maintenance - blind spot" | Case brief states service corridor is unmonitored link to lab | Absence of footage does NOT prove absence of use; unauthorized entry possible |
| Badge credential interpretation | Confirms identity | Security note (D03_messages) states doors log badge credentials, not biometric identity | Badge use confirmed but identity is appearance-based only |

---

## 7. Final Conclusion

**Most Likely Scenario:** A person wearing a teal coat entered the lab area via the east corridor at 18:10 and removed the prototype between 18:10-18:14, exiting with it at 18:14. This person matches the appearance description of Nora Vale (teal work coat). The prototype was transported from the east exit to an unknown location by 18:18.

**Supporting Observations:**
- V02 confirms prototype present at 18:00
- V03 shows teal coat person entering east corridor at 18:10
- V04 shows teal coat person exiting east exit at 18:14 with prototype visible
- V05 confirms prototype missing from lab at 18:18
- D01_access.csv timestamps align with visual evidence

**Plausible Alternatives:**
- Unauthorized entry via service corridor blind spot (V10) - cannot rule out due to camera maintenance
- Person in teal coat is not Nora Vale but someone wearing same coat color
- Badge credential was used by different individual than coat wearer

**Can Responsibility Be Identified?** Yes, with moderate confidence. The visual evidence strongly associates the teal coat person with prototype removal. However, without biometric verification, definitive identification cannot be made.

**Confidence Level:** 65% - Moderate confidence based on visual evidence correlation, but limited by blind spots and lack of biometric verification.

---

## 8. Confidence and Limitations

**Confidence Assessment:** 65%
- **Supporting factors:** Strong visual evidence correlation between teal coat person and prototype removal; access logs confirm entry/exit timing; multiple camera feeds corroborate sequence
- **Limiting factors:** Appearance-based identification only (no biometric verification); service corridor blind spot cannot be ruled out for unauthorized entry; witness statements unverified; point-in-time snapshots do not establish continuous tracking

**Key Limitations:**
1. **Identity uncertainty**: Coat color is appearance evidence, not biometric identity. Badge credentials establish credential use only.
2. **Blind spot uncertainty**: Service corridor (V10) has no camera coverage. Cannot rule out unauthorized entry via this route.
3. **Temporal gaps**: Snapshots are point-in-time observations. Cannot determine exact moments of prototype removal or continuous whereabouts.
4. **Witness reliability**: All statements are unverified and may be incomplete, biased, or inaccurate.

**Alternative Explanations Remaining Plausible:**
- Unauthorized entry via service corridor by someone not in access logs
- Teal coat wearer is not Nora Vale but another individual
- Prototype was removed before 18:10 (before teal coat person entered)

---

## 9. Recommended Next Investigative Steps

1. **Biometric verification**: Obtain badge swipe logs with biometric data to confirm identity of person who used credentials at 18:10-18:14.

2. **Service corridor investigation**: Deploy temporary camera or conduct physical inspection of service corridor to determine if unauthorized entry occurred during incident window.

3. **Coat inventory check**: Verify if multiple staff wear teal coats or if Nora Vale's coat is unique. Check for distinctive markings, patches, or modifications.

4. **Access log expansion**: Review all badge credential logs for 18:00-18:20 to identify any additional entries not captured in current analysis.

5. **Witness re-interview**: Conduct structured interviews with all five staff members, focusing on specific times and locations, to verify or correct statements.

6. **Prototype tracking**: If prototype has identifiable markings, trace its location after 18:14 using security footage from other areas.

7. **Service corridor access review**: Determine if service corridor requires authentication for entry and whether any unauthorized access attempts were logged.

8. **Timeline refinement**: Obtain more granular timestamps from camera feeds to narrow down exact removal window.

---

**Report Prepared By:** Independent Investigator  
**Date:** Investigation complete  
**Case Reference:** CASE_01 / V01-V10 / D01-D03
