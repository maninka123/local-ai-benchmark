# Investigation Report: Missing Laboratory Prototype

## 1. Executive Summary

A prototype was last confirmed present at 18:00 and discovered missing by 18:18. Access logs show all five staff members entered the facility between 18:10-18:14. The most likely responsible individual is **Eli Stone**, who had both motive (expressed need for the prototype for tomorrow's project) and opportunity (accessed SERVICE_DOOR at 18:14, a known camera blind spot). His witness statement directly contradicts the access log evidence.

## 2. Evidence Inventory

| Exhibit | Type | Description |
|---------|------|-------------|
| D01_access.csv | Access Log | Records 5 staff entries between 18:10-18:14 |
| D02_witnesses.md | Witness Statements | Unverified statements from 5 staff members |
| D03_messages.md | Internal Messages | Motive and security notes |
| V01-V10 | Images | Not available in text-only track |

## 3. Timeline

| Time | Event | Source |
|------|-------|--------|
| 17:00 | Eli: "My project needs that prototype tomorrow" | D03_messages |
| 17:10 | Maya asked to move cardboard box | D03_messages |
| 17:20 | Security notes SERVICE_DOOR is camera blind spot | D03_messages |
| 18:00 | Prototype last confirmed present | case_brief |
| 18:10 | Nora Vale enters EAST_CORRIDOR | D01_access |
| 18:12 | Theo Park enters CAFETERIA | D01_access |
| 18:13 | Ada Finch enters RECEPTION | D01_access |
| 18:14 | Eli Stone enters SERVICE_DOOR | D01_access |
| 18:14 | Maya Reed enters SERVICE_DOOR | D01_access |
| 18:18 | Prototype discovered missing | case_brief |

## 4. Suspect Analysis

| Suspect | Opportunity | Timeline Consistency | Contradictions | Motive | Exculpatory Evidence |
|---------|-------------|---------------------|----------------|--------|---------------------|
| **Eli Stone** | SERVICE_DOOR at 18:14 (near lab) | Contradicted by access log | "Did not approach lab" vs SERVICE_DOOR entry | High (needs prototype tomorrow) | None |
| Maya Reed | SERVICE_DOOR at 18:14 | Inconsistent (box at 18:11 vs entry at 18:14) | None directly implicating | None | Cardboard box task |
| Nora Vale | EAST_CORRIDOR at 18:10 | Consistent with statement | None | None | Statement matches access |
| Theo Park | CAFETERIA at 18:12 | Consistent with statement | None | None | Statement matches access |
| Ada Finch | RECEPTION at 18:13 | Consistent with statement | None | None | Statement matches access |

## 5. Key Deductions

1. **Motive**: Eli's 17:00 message establishes clear motive.
2. **Opportunity**: SERVICE_DOOR is a camera blind spot (D03_messages) and provides access to lab areas.
3. **Timeline**: Eli entered at 18:14; prototype missing by 18:18 — 4-minute window sufficient.
4. **Contradiction**: Eli's denial of approaching the lab directly conflicts with SERVICE_DOOR entry.
5. **Alternative entry**: Maya Reed also entered SERVICE_DOOR at 18:14, but no motive evidence.

## 6. Contradictions

1. **Eli Stone**: Statement says "I did not approach the lab after 18:00" but access log shows SERVICE_DOOR entry at 18:14.
2. **Maya Reed**: Statement says "I carried a cardboard supply box at 18:11" but access log shows SERVICE_DOOR entry at 18:14.

## 7. Final Conclusion

**Eli Stone** is the most likely responsible individual for the missing prototype. The combination of motive (expressed need for tomorrow's project), opportunity (SERVICE_DOOR access at 18:14, a blind spot), and a direct contradiction between his statement and the access log creates a strong preponderance of evidence pointing to him.

## 8. Confidence and Limitations

**Confidence**: 72%

**Limitations**:
- No visual evidence (V01-V10 unavailable in text-only track)
- No exit records to confirm departure
- Badge credentials may be shared (D03_messages: "doors log badge credentials, not biometric identity")
- 18:00-18:10 gap: no access log entries (possible pre-existing presence)
- 18:14-18:18 gap: no exit records

## 9. Recommended Next Investigative Steps

1. Review badge access logs for exits at SERVICE_DOOR
2. Interview Eli Stone about his 18:14-18:18 activities
3. Verify if Maya Reed's cardboard box task required lab access
4. Review any internal camera footage from other corridors
5. Confirm prototype storage location and access requirements
