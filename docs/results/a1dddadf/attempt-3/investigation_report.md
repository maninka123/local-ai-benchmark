# Investigation Report – Case 03: Missing Laboratory Prototype

## 1. Executive Summary
The prototype was last confirmed present at 18:00 and reported missing at 18:18. Access logs (D01) show five staff members entering various doors between 18:10 and 18:14, with two entries to the **SERVICE_DOOR** (Eli Stone and Maya Reed). No exit records exist for the service door, and the service corridor is a camera blind spot (D03). Witness statements (D02) conflict with the logs and are considered unreliable. The most plausible scenario is that the prototype was removed by an individual who entered the service door after 18:00, most likely **Eli Stone**. Maya Reed remains a secondary possibility. No definitive evidence identifies a single individual.

## 2. Evidence Inventory
| Exhibit ID | Type | Key Observation | Source |
|------------|------|-----------------|--------|
| D01 | Access log | Five entries 18:10‑18:14; two to SERVICE_DOOR | /input/D01_access.csv |
| D02 | Witness statements | Conflicting accounts; no timestamps | /input/D02_witnesses.md |
| D03 | Internal messages | Service corridor is a camera blind spot; badge logs not biometric | /input/D03_messages.md |

*Visual exhibits V01–V10 are not available in this text‑only track.*

## 3. Timeline
The timeline is derived from the access log and the missing‑prototype report.

| Time | Event | Evidence |
|------|-------|----------|
| 18:10 | Nora Vale enters EAST_CORRIDOR | D01 |
| 18:12 | Theo Park enters CAFETERIA | D01 |
| 18:13 | Ada Finch enters RECEPTION | D01 |
| 18:14 | Eli Stone enters SERVICE_DOOR | D01 |
| 18:14 | Maya Reed enters SERVICE_DOOR | D01 |
| 18:14‑18:18 | Unaccounted interval after service door entry | D01 |
| 18:18 | Prototype reported missing | D01 |

**Confirmed events**: 18:10‑18:14 entries. **Probable events**: exit from SERVICE_DOOR between 18:14‑18:18. **Missing interval**: 18:14‑18:18. **Contradictions**: Witness statements conflict with log entries.

## 4. Suspect Analysis
| Suspect | Opportunity | Access | Timeline Consistency | Contradictions | Supporting Evidence | Exculpatory Evidence | Assessment |
|---------|-------------|--------|----------------------|----------------|---------------------|----------------------|------------|
| Nora Vale | Entered EAST_CORRIDOR; no exit | Badge logged entry | Witness says only visited corridor | None | D01 18:10 | None | Possible but unconfirmed |
| Eli Stone | Entered SERVICE_DOOR; no exit | Badge logged entry | Witness denies lab after 18:00 | Witness statement | D01 18:14 | D02 Eli statement | **Strong candidate** |
| Maya Reed | Entered SERVICE_DOOR; no exit | Badge logged entry | Witness says carried cardboard at 18:11 | None | D01 18:14, D02 Maya | None | Possible secondary suspect |
| Theo Park | Entered CAFETERIA; no exit | Badge logged entry | Witness says remained in cafeteria | None | D01 18:12, D02 Theo | None | Unlikely |
| Ada Finch | Entered RECEPTION; no exit | Badge logged entry | Witness says staffed reception | None | D01 18:13, D02 Ada | None | Unlikely |

## 5. Key Deductions
1. **Badge logs confirm presence** of Eli Stone and Maya Reed in the service corridor at 18:14. 2. **No exit record** for the service door suggests the prototype could have been removed after 18:14. 3. **Camera blind spot** (D03) means the service corridor is not monitored. 4. **Witness statements** are unreliable and conflict with logs. 5. **Eli Stone’s denial** of lab access after 18:00 is contradicted by badge entry to the service door.

## 6. Contradictions
- Witness statements (D02) conflict with access log (D01).  - No exit logs for the service door, leaving the 18:14‑18:18 interval unaccounted for.

## 7. Final Conclusion
The most likely scenario is that the prototype was removed by an individual who entered the service door after 18:00, most plausibly **Eli Stone**. Maya Reed remains a possible secondary suspect due to simultaneous entry, but there is less direct evidence of her involvement. No definitive responsible person can be identified with the available written evidence.

## 8. Confidence and Limitations
- **Confidence**: 0.3 (low). The conclusion is based on indirect inference from badge logs and the absence of exit records, with no direct observation of the prototype’s removal. 
- **Limitations**: 
  - Badge logs record credentials, not biometric identity, so the presence of a badge does not prove the bearer was physically present. 
  - The service corridor is a camera blind spot; no visual evidence exists. 
  - Witness statements are unverified and conflict with each other. 
  - No exit records for the service door; the interval 18:14‑18:18 is unobserved.

## 9. Recommended Next Investigative Steps
1. **Obtain video footage** from any cameras that may cover the service corridor or adjacent areas. 
2. **Interview staff** again, focusing on the 18:14‑18:18 interval and any knowledge of prototype handling. 
3. **Check badge usage logs** for any subsequent use of the service door badge after 18:18. 
4. **Inspect the prototype’s storage location** for physical evidence (e.g., fingerprints, tool marks). 
5. **Review any maintenance or security logs** that might record door usage or anomalies during the incident window.

*This report is based solely on the written evidence supplied (D01–D03). Visual exhibits V01–V10 were not available and are not referenced.*
