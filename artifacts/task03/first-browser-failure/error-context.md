# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: golden-path.spec.ts >> custom file upload never receives mocked findings
- Location: tests\golden-path.spec.ts:95:5

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: locator.click: Test timeout of 45000ms exceeded.
Call log:
  - waiting for getByRole('link', { name: /Submission Upload/ })

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "본문으로 이동" [ref=e2] [cursor=pointer]:
    - /url: "#main"
  - banner [ref=e3]:
    - link "✓ FINAL CHECK" [ref=e4] [cursor=pointer]:
      - /url: /
      - generic [ref=e5]: ✓
      - text: FINAL CHECK
    - generic [ref=e6]: MVP / DEMO
  - generic [ref=e8]:
    - navigation "검사 단계" [ref=e9]:
      - link "01 시작" [ref=e10] [cursor=pointer]:
        - /url: /
        - generic [ref=e11]: "01"
        - generic [ref=e12]: 시작
      - link "02 공고 분석" [ref=e13] [cursor=pointer]:
        - /url: /announcement
        - generic [ref=e14]: "02"
        - generic [ref=e15]: 공고 분석
      - link "03 파일 업로드" [ref=e16] [cursor=pointer]:
        - /url: /upload
        - generic [ref=e17]: "03"
        - generic [ref=e18]: 파일 업로드
      - generic [ref=e19]:
        - generic [ref=e20]: "04"
        - generic [ref=e21]: 검사 결과
      - generic [ref=e22]:
        - generic [ref=e23]: "05"
        - generic [ref=e24]: 재검사
    - main [ref=e25]:
      - generic [ref=e26]:
        - strong [ref=e28]: GENERIC · 실행 전
        - generic [ref=e29]: 로컬 규칙 후보 · AI 모델 미연결. 자동 검증 미지원 → REVIEW / EXTERNAL. 스캔 PDF Vision 미연결.
      - generic [ref=e31]:
        - generic [ref=e32]: 01 / ANNOUNCEMENT ANALYSIS
        - heading "공고의 조건부터 확인하세요" [level=1] [ref=e33]
        - paragraph [ref=e34]: 제출 전에 지켜야 할 조건과 공고문에 적힌 근거를 살펴봅니다.
      - generic [ref=e35]:
        - generic [ref=e36]:
          - generic [ref=e37]:
            - heading "요구사항 검토" [level=2] [ref=e38]
            - generic [ref=e39]: 0개 항목
          - generic [ref=e40]:
            - paragraph [ref=e41]:
              - strong [ref=e42]: "Profile: DRAFT"
              - text: · READABLE
            - paragraph [ref=e43]: 아직 실행 전 · 로컬 규칙 기반 추출기
            - paragraph
            - button "요구사항 추출 실행" [ref=e44] [cursor=pointer]
        - complementary [ref=e45]:
          - generic [ref=e46]: ANNOUNCEMENT / HUMAN REVIEW
          - heading "demo-announcement.txt" [level=3] [ref=e47]
          - paragraph [ref=e48]: 추출 후보를 원문과 대조해 수정·삭제·승인하세요. 항목 승인은 제출파일이 조건을 충족했다는 뜻이 아닙니다.
          - group [ref=e49]:
            - generic "공고 원문과 provenance" [ref=e50]
          - group [ref=e51]:
            - generic "검토 이력 0개" [ref=e52]
          - generic [ref=e53]:
            - checkbox "공고 원문 전체와 누락 가능성을 직접 검토했습니다." [ref=e54]
            - text: 공고 원문 전체와 누락 가능성을 직접 검토했습니다.
          - button "Profile 확정" [disabled] [ref=e55]
          - paragraph [ref=e56]:
            - link "다른 공고로 새 검사" [ref=e57] [cursor=pointer]:
              - /url: /
    - contentinfo [ref=e58]:
      - strong [ref=e59]: FINAL CHECK
      - generic [ref=e60]: 확신은, 근거에서 시작됩니다.
      - generic [ref=e61]: FROZEN v1.5 · LOCAL DEMO
  - alert [ref=e62]: 공고의 조건부터 확인하세요
```

# Test source

```ts
  4   |
  5   | class GoldenPath {
  6   |   constructor(readonly page: Page, readonly info: TestInfo) {}
  7   |   async capture(name: string) {
  8   |     const directory = path.resolve("../artifacts/screenshots");
  9   |     await fs.mkdir(directory, { recursive: true });
  10  |     await this.page.screenshot({ path: path.join(directory, `${this.info.project.name}-${name}.png`), fullPage: true });
  11  |     const overflow = await this.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  12  |     expect(overflow, `horizontal overflow on ${name}`).toBe(false);
  13  |   }
  14  |   async start() {
  15  |     await this.page.goto("/");
  16  |     await expect(this.page.getByRole("heading", { level: 1 })).toContainText("마지막 한 번");
  17  |     await this.capture("01-home");
  18  |     await this.page.getByRole("button", { name: "demo 검사 시작하기" }).click();
  19  |     await expect(this.page).toHaveURL(/\/announcement$/);
  20  |     await expect(this.page.getByRole("heading", { name: "동결 공고 요구사항" })).toBeVisible();
  21  |     await expect(this.page.getByText("16개 항목")).toBeVisible();
  22  |     await this.capture("02-announcement");
  23  |     await this.page.getByRole("link", { name: "제출파일 선택하기" }).click();
  24  |     await expect(this.page).toHaveURL(/\/upload$/);
  25  |   }
  26  | }
  27  |
  28  | test("five-screen golden path, evidence, filter, reload and recheck", async ({ page }, info) => {
  29  |   const errors: string[] = [];
  30  |   const uploads: string[] = [];
  31  |   page.on("request", request => {
  32  |     if (request.method() === "POST" && /\/sessions\/[^/]+\/files$/.test(new URL(request.url()).pathname)) {
  33  |       uploads.push(request.headers()["content-type"] ?? "");
  34  |     }
  35  |   });
  36  |   page.on("pageerror", error => errors.push(error.message));
  37  |   page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  38  |   const flow = new GoldenPath(page, info);
  39  |   await flow.start();
  40  |   await expect(page.getByRole("button", { name: "Preflight 실행하기" })).toBeDisabled();
  41  |   await page.getByRole("button", { name: "문제 있는 demo 불러오기" }).click();
  42  |   await expect(page.getByText("테스트어린이집_숏폼공모서류.pdf", { exact: true })).toBeVisible();
  43  |   await flow.capture("03-upload");
  44  |   const brokenRun = page.waitForResponse(response => response.url().endsWith("/validate") && response.request().method() === "POST");
  45  |   await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  46  |   const brokenBody = await (await brokenRun).json();
  47  |   expect(brokenBody.source_mode).toBe("validator");
  48  |   expect(brokenBody.engine_sha256).toBe("4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11");
  49  |   await expect(page).toHaveURL(/\/results$/);
  50  |   await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("BLOCKED");
  51  |   const blockers = page.getByRole("article").filter({ has: page.getByText("BLOCKER", { exact: true }) });
  52  |   await expect(blockers).toHaveCount(2);
  53  |   await expect(page.getByRole("article", { name: "R09 참가 신청서 및 개인정보 동의서" })).toContainText("BLOCKER");
  54  |   await expect(page.getByRole("article", { name: "R13 영상 길이 30~60초" })).toContainText("BLOCKER");
  55  |   for (const blocker of await blockers.all()) {
  56  |     await expect(blocker.getByText("공고문 근거", { exact: true })).toBeVisible();
  57  |     await expect(blocker.getByText("제출파일 근거", { exact: true })).toBeVisible();
  58  |     await expect(blocker.locator("blockquote")).toHaveCount(2);
  59  |   }
  60  |   const r19 = page.getByRole("article", { name: "R19 사진만으로 구성된 영상 확인" });
  61  |   await expect(r19.getByText("REVIEW", { exact: true })).toBeVisible();
  62  |   await flow.capture("04-results-broken");
  63  |   await page.getByRole("button", { name: "BLOCKER 2", exact: true }).click();
  64  |   await expect(page.getByRole("article")).toHaveCount(2);
  65  |   await page.getByRole("button", { name: "전체 16", exact: true }).click();
  66  |   await page.reload();
  67  |   await expect(page.getByRole("article")).toHaveCount(16);
  68  |   await page.getByRole("link", { name: "수정 후 재검사", exact: false }).click();
  69  |   await expect(page).toHaveURL(/\/recheck$/);
  70  |   await page.getByRole("button", { name: "수정한 demo 불러오기" }).click();
  71  |   await expect(page.getByText("테스트어린이집_숏폼공모서류.pdf", { exact: true })).toBeVisible();
  72  |   await flow.capture("05-recheck");
  73  |   await page.getByRole("button", { name: "재검사 실행하기" }).click();
  74  |   await expect(page).toHaveURL(/\/results$/);
  75  |   await expect(page.getByRole("region", { name: "전체 검사 상태" })).toContainText("REVIEW_REQUIRED");
  76  |   await expect(page.getByRole("region", { name: "전체 검사 상태" })).not.toContainText("READY");
  77  |   await expect(page.getByRole("region", { name: "재검사 비교" })).toContainText("2개 판정 변경");
  78  |   await expect(page.getByRole("article").filter({ has: page.getByText("BLOCKER", { exact: true }) })).toHaveCount(0);
  79  |   await expect(page.getByRole("article", { name: "R19 사진만으로 구성된 영상 확인" })).toContainText("REVIEW");
  80  |   await expect(page.getByRole("article", { name: "R09 참가 신청서 및 개인정보 동의서" })).toContainText("PASS");
  81  |   await expect(page.getByRole("article", { name: "R13 영상 길이 30~60초" })).toContainText("PASS");
  82  |   expect(uploads).toHaveLength(2);
  83  |   expect(uploads.every(value => value.includes("multipart/form-data"))).toBe(true);
  84  |   await flow.capture("06-results-fixed");
  85  |   expect(errors).toEqual([]);
  86  | });
  87  |
  88  | test("deep link without a session has a recovery path", async ({ page }) => {
  89  |   await page.goto("/results");
  90  |   await expect(page.getByRole("heading", { name: "먼저 검사를 시작해 주세요" })).toBeVisible();
  91  |   await page.getByRole("link", { name: "홈으로 돌아가기" }).click();
  92  |   await expect(page).toHaveURL("/");
  93  | });
  94  |
  95  | test("custom file upload never receives mocked findings", async ({ page }) => {
  96  |   await page.goto("/");
  97  |   await page.getByLabel("공고문 파일").setInputFiles(path.resolve("../fixtures/demo-announcement.txt"));
  98  |   await page.getByRole("button", { name: "파일 정보 확인" }).click();
  99  |   await expect(page).toHaveURL(/\/announcement$/);
  100 |   await expect(page.getByRole("heading", { name: "요구사항 검토" })).toBeVisible();
  101 |   await expect(page.getByTestId("profile-status")).toHaveText("DRAFT");
  102 |   await expect(page.getByRole("article")).toHaveCount(0);
  103 |   // TASK 03 adds extraction/review; merely receiving a file still grants no verified profile.
> 104 |   await page.getByRole("link", { name: /Submission Upload/ }).click();
      |                                                               ^ Error: locator.click: Test timeout of 45000ms exceeded.
  105 |   await page.getByLabel("제출파일", { exact: true }).setInputFiles(path.resolve("../fixtures/demo-fixed/proposal.pdf"));
  106 |   await page.getByRole("button", { name: "선택한 1개 파일 확인" }).click();
  107 |   await page.getByRole("button", { name: "Preflight 실행하기" }).click();
  108 |   await expect(page.getByRole("alert", { name: "작업 오류" })).toContainText("이 공고의 분석 프로필 또는 검증 엔진을 사용할 수 없습니다");
  109 |   await expect(page).toHaveURL(/\/upload$/);
  110 |   await expect(page.getByRole("article")).toHaveCount(0);
  111 | });
  112 |
  113 | test("backend failure is recoverable and does not advance", async ({ page }) => {
  114 |   await page.route("**/api/sessions", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"test service unavailable"}' }));
  115 |   await page.goto("/");
  116 |   await page.getByRole("button", { name: "demo 검사 시작하기" }).click();
  117 |   await expect(page.getByRole("alert", { name: "작업 오류" })).toBeVisible();
  118 |   await expect(page).toHaveURL("/");
  119 |   await expect(page.getByRole("button", { name: "demo 검사 시작하기" })).toBeEnabled();
  120 | });
  121 |
```
