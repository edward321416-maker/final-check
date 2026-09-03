# Collection and Gold notes (before extraction)

Eight distinct 2025 competitions: education/video, climate video, university
humanities hackathon, financial AI model competition, weather startup ideas,
public data startup planning, festival programs, regional public-data products.
Four HTML article bodies and four actual text PDFs. Pure private-company-hosted
competition coverage is absent; DACON is the commercial competition platform.
This is a purposive small sample, not a representative survey.

- C01: complete nine-page education-office PDF, including three form attachments.
  Page 1 table visually checked: filenames are requirements; PDF and video
  formats are recommendations under the column heading, not mandatory formats.
- C02: complete HTML announcement body on the official government participation
  portal. Attached HWP/poster not included. Two contradictory closing minutes
  (23:59 and 23:50) are preserved. Gold records the unresolved deadline as INFO,
  rather than inventing a corrected deadline. The applicant should ask the
  organizer, but no new obligation to contact them is invented in Gold.
- C03: university article body only. Linked application HWP/form internals are
  outside scope. Selection criteria are not turned into mandatory essay fields.
- C04: entire first rules article and its adjacent schedule. Responsive duplicate
  article removed before Gold. Other tabs, linked FAQ and policy pages are outside
  scope. Year 2025 is established by the captured page title. Resource compatibility
  is one operational requirement; hardware/software parameters are one specified
  environment, not many independent submission rules.
- C05: the official linked PDF is actually one page, not the imagined full multi-page
  instructions. All of that page is included. Its small Gold count is intentional.
  Numeric dates are badly separated in PyMuPDF text; the page was visually checked
  to write the actual dates in Gold. Input text is not repaired.
- C06: complete HTML article, including both schedule and award tables. The award
  table is excluded from Gold but retained in input. Linked poster not included.
- C07: all five PDF pages, including proposal and consent forms. Proposal table
  checked visually. Optional consent refusal is not rewritten as mandatory consent.
- C08: all seven PDF pages from the JCIA download link. The captured landing HTML
  is retained only as acquisition provenance. Actual attachment URL was resolved
  from `cf_download('FS_0000013358')` and the public `cf_download` JavaScript
  implementation (`/async/MultiFile/download.do?FS_KEYNO=...`). Page 2 table was
  visually checked to preserve conditional document requirements. Separate HWP
  forms are outside scope.

Pre-output selection change: the initially considered Korea University BK21 notice
`https://ie.korea.ac.kr/ie/news/g_notice.do?articleNo=769552&mode=view` returned HTTP
404 during direct capture (2026-09-03T11:38:35.701027+00:00). It was replaced by C02
before Gold; no extractor output was seen. C08 landing body lacked the requirements,
so its linked PDF was acquired. These are collection issues, not benchmark failures.

Initial PDF exploration used pypdf, then source inspection confirmed the application's
reader is PyMuPDF. All frozen PDF inputs were rebuilt using the application's exact
newline-joined `page.get_text()` behavior before annotation. No product code was
imported or executed for collection. Screenshots are document visual inspection,
not an implemented Vision/OCR provider. Manual annotation/scoring by the same
engineering agent is disclosed in PROTOCOL.md; no independent human adjudication.

Atomicity convention: separate independently testable file/duration/name/rights
constraints. A single allowed-value set, a complete contact instruction with its
exception, a specified environment, or one complete workflow is one requirement.
Do not split alternatives into simultaneous obligations. Post-award obligations
explicitly imposed on applicants (costs/rights/returns) remain in scope; organizer
plans, general selection criteria, and remedies without submission duties do not.
