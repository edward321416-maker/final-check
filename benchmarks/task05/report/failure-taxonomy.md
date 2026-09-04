# TASK 05 failure taxonomy

Counts overlap. Unit counts use the same manual judgements for RAW and GATED.

| Category | RAW | GATED | Meaning/example |
|---|---:|---:|---|
| Fragmentation | 92 | 73 | C04 R31-R34 split the single complete pipeline unit. C02 R15-R17 split required markings. |
| Excluded organizer/prize information | 48 | 39 | C02 R22-R27 and C08 R26-R36 enumerate evaluation operations. |
| Empty form labels promoted to obligations | 43 | 7 | C01 R35-R41, C07 R09-R12. |
| Supported items outside frozen Gold | 22 | 15 | C07 R43 residual city-decision clause; C08 R58-R59 responsibility notices. No retrospective Gold additions. |
| Duplicate content | 18 | 14 | C04 R38-R39 restate single-LLM restriction; C05 R02 repeats its theme. |
| Modality-related defect | 13 | 11 | Includes non-MATCH candidates, unlike the MATCH-only accuracy denominator. |
| Semantic atomicity violation | 7 | 3 | GATED C03 R10, C06 R02 and C08 R24 combine separately judged constraints. |
| Selected evidence does not support full assertion | 7 | 3 | GATED C02 R14, C04 R58 and C08 R24. |
| Lost applicability/exception | 4 | 2 | C04 R17 unconditional augmentation; C08 R24 stage conflation. |
| Unresolved source conflict mishandled | 2 | 2 | C02 R01-R02 do not preserve the complete deadline conflict in a single requirement. |

Mechanical gate separately rejects all 117 C01 candidates because the unchanged
product cap is 100 per extraction. Gate syntax flags 29 retained candidates; these
are review signals, not the manual atomicity count. Unsupported BLOCKER counts
are RAW 5 and GATED 3; all quotes are exact. Hallucination count is zero under the
frozen definition, with conditional/scope defects still explicitly recorded.

No remedial prompt, regex change, Gold edit, semantic repair, case retry, rescoring
policy change, model replacement or production integration was performed.
