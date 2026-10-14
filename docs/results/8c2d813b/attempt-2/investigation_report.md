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
| 17:00 | Eli Stone requests prototype for tomorrow | D03_messages.md | Eli Stone | Confirmed |
| 17:10 | Maya Reed requests cardboard box move to loading bay | D03_messages.md | Maya Reed | Confirmed |
| 18:00 | Prototype confirmed present in lab | V02 | N/A | Confirmed |
| 18:10 | Person in teal coat enters EAST_CORRIDOR | D01_access.csv + V03 | Nora Vale (appearance) | Confirmed |
| 18:10-18:14 | Person in teal coat takes prototype from lab | V03 + V04 + D01 | Nora Vale (appearance) | Probable |
| 18:11 | Maya Reed at loading bay with cardboard box | V08 + D03 | Maya Reed | Confirmed |
| 18:12 | Person in blue coat enters CAFETERIA | D01_access.csv + V06 | Theo Park (appearance) | Confirmed |
| 18:13 | Person in red coat enters RECEPTION | D01_access.csv + V07 | Ada Finch (appearance) | Confirmed |
| 18:14 | Person in teal coat exits EAST_EXIT with prototype | D01_access.csv + V04 | Nora Vale (appearance) | Confirmed |
| 18:18 | Prototype confirmed missing from lab | V05 | N/A | Confirmed |

**Missing Intervals:**
- 18:14-18:18: Transport of prototype from east exit to unknown location
- Service corridor (V10): No camera footage, but blind spot does not prove absence of use

---

## 4. Suspect Analysis

### Nora Vale (Teal Coat)
- **Opportunity:** HIGH - Entered lab area at 18:10, only person with visual confirmation during incident window
- **Access:** Confirmed via badge credential (D01_access.csv)
- **Timeline Consistency:** ENTERED at 18:10, EXITED with prototype at 18:14
- **Contradictions:** Witness statement claims only visited corridor, but V04 shows her carrying prototype out
- **Supporting Evidence:** 
  - V03 shows entry without visible object
  - V04 shows exit with prototype visible
  - D01 confirms timing matches
- **Exculpatory Evidence:** None identified
- **Limitations:** Coat color is appearance evidence only; badge credential does not confirm biometric identity

### Eli Stone (Orange Coat)
- **Opportunity:** LOW - Not visually present in lab area during incident timeframe
- **Access:** Not logged in access records during 18:10-18:14
- **Timeline Consistency:** Statement aligns with visual evidence (not seen in cameras)
- **Contradictions:** None
- **Supporting Evidence:** D03_messages.md shows request for prototype at 17:00 (provides motive but no opportunity)
- **Exculpatory Evidence:** No visual evidence places him near lab during incident

### Maya Reed (Purple Coat)
- **Opportunity:** MEDIUM - Moved cardboard box, could have accessed lab
- **Access:** Confirmed at loading bay
- **Timeline Consistency:** At loading bay with cardboard box at 18:11, not in lab area
- **Contradictions:** None
- **Supporting Evidence:** 
  - V08 shows her with cardboard box at loading bay
  - D03_messages.md confirms box move request
- **Exculpatory Evidence:** Visual evidence places her away from lab during incident

### Theo Park (Blue Coat)
- **Opportunity:** LOW - In cafeteria
- **Access:** Confirmed at cafeteria
- **Timeline Consistency:** In cafeteria at 18:12 per witness and camera
- **Contradictions:** None
- **Supporting Evidence:** 
  - V06 shows him in cafeteria
  - D01 confirms cafeteria entry
- **Exculpatory Evidence:** Visual evidence places him away from lab during incident

### Ada Finch (Red Coat)
- **Opportunity:** LOW - At reception
- **Access:** Confirmed at reception
- **Timeline Consistency:** At reception at 18:13 per witness and camera
- **Contradictions:** None
- **Supporting Evidence:** 
  - V07 shows her at reception
  - D01 confirms reception entry
- **Exculpatory Evidence:** Visual evidence places her away from lab during incident
---

## 5. Key Deductions

1. **The prototype was taken between 18:10-18:14** - This is the only window where visual evidence shows a person entering and exiting with the object.

2. **Nora Vale (teal coat) is associated with taking the prototype** - Visual evidence V03-V04 shows a person in teal coat entering without visible object and exiting with prototype.

3. **The service corridor blind spot (V10) does not prove absence of use** - Absence of camera footage cannot definitively rule out access through this route during the incident window.

4. **Location snapshots are point-in-time observations** - Being in one location at a specific timestamp does not establish continuous whereabouts or rule out prior/later movement.

5. **Badge credentials establish credential use, not biometric identity** - The access log shows who used which badge, but cannot confirm the person behind the badge without additional verification.

6. **Coat color is supporting evidence only** - While coat color matches Nora Vale's description, this alone does not constitute conclusive identification.

---

## 6. Contradictions

| Statement | Evidence | Resolution |
|-----------|----------|-------------|
| Nora: "I only visited the east corridor and left" | V04 shows her exiting with prototype | Witness statement contradicted by visual evidence |
| Service corridor was unmonitored | V10 notes blind spot | Blind spot does not prove nobody used it; absence of footage is not proof of absence |
| Badge credentials confirm identity | D01_access.csv | Credentials only show badge use, not biometric identity |

---

## 7. Final Conclusion

**Most Likely Scenario:** A person wearing a teal coat entered the lab area through the east corridor at 18:10, took the prototype from the lab, and exited through the east exit at 18:14 carrying it. This person matches the appearance description of Nora Vale based on coat color evidence.

**Supporting Observations:**
- V02 confirms prototype present at 18:00
- V03 shows teal-coat person entering corridor at 18:10
- V04 shows teal-coat person exiting with prototype at 18:14
- V05 confirms prototype missing at 18:18
- D01_access.csv timestamps align with visual evidence

**Alternative Explanations:**
- The person in the teal coat could be someone else wearing similar attire
- The service corridor blind spot could have been used by another individual
- Badge credentials could have been shared or compromised

**Definitive Identification Limitation:** Without biometric verification (fingerprint, facial recognition) or continuous tracking through all camera feeds, a definitive identification cannot be made. The investigation identifies the most likely responsible party based on available evidence while acknowledging remaining uncertainty.

---

## 8. Confidence and Limitations

**Confidence Level: 65%**

**Supporting Factors:**
- Strong visual correlation between coat color and person in footage
- Timeline consistency across multiple evidence sources
- Access log timestamps align with camera observations

**Limitations:**
- No biometric verification available
- Coat color is appearance evidence only, not conclusive identification
- Service corridor blind spot (V10) does not prove absence of use
- Location snapshots are point-in-time, not continuous tracking
- Witness statements are unverified and may be incomplete
- Badge credentials establish credential use, not biometric identity

**What Would Resolve Uncertainty:**
- Biometric verification of badge users
- Continuous camera coverage including service corridor
- Access logs with biometric authentication
- Surveillance footage covering the full transport path from east exit to destination

---

## 9. Recommended Next Investigative Steps

1. **Review badge credential logs** - Cross-reference badge usage with known staff identities
2. **Check security system for blind spot coverage** - Determine if service corridor can be monitored
3. **Interview additional witnesses** - Look for anyone who saw the person leaving east exit
4. **Trace prototype destination** - Check loading bay, vehicle manifests, or other storage areas
5. **Review badge sharing policies** - Determine if credentials could have been shared
6. **Enhance camera coverage** - Install cameras in blind spots to prevent future incidents
7. **Implement biometric access control** - Replace badge-only authentication where possible