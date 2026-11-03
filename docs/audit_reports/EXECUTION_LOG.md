# HELPNET Audit Execution Log

| Phase | Action | Result |
|---|---|---|
| Repository inspection | Confirmed branch `samia`, commit `e1523e3`, clean worktree at start; inventoried apps, pages, scripts, docs, requirements, tests, migrations, and local history. | PASS |
| Evidence review | Found no SRS/SDS/sample report or approved change log; inspected acceptance/test-plan notes and Git commits. | Missing inputs recorded; no history invented. |
| Sensitive-path review | Checked tracked environment files, private uploads, SQL dump insert statements, and ignore rules without reading private document contents or printing environment values. | `.env` not tracked; 19 tracked private uploads found; SQL dump had 0 INSERT statements. |
| Security/code review | Reviewed settings, upload paths, API permissions, dynamic HTML rendering, static includes, report/ratings code, and raw SQL use. | Findings recorded in `BUG_TRACKER.md` and `SECURITY_REPORT.md`. |
| Code changes | Hardened settings, removed dynamic HTML rendering in verification admin, wired health review page, corrected certificate collection input, privatized blood documents, validated signatures, corrected unrated averages, implemented profile editing/reactivation, farmer listing edits, and NGO private document verification with owner/admin access, review states, profile permissions, migration, and UI. | Changes remain uncommitted. |
| Sensitive-file handling | Added ignore rules and removed 19 private uploads from the current index only. | Local files retained; old Git history unchanged. |
| Targeted regression testing | Blood, volunteer, common-page, verification, and rating tests run while implementing changes. An initial migration test exposed and led to fixes for migration registry and FieldFile-name handling; a Windows cleanup issue was corrected. | Final targeted tests passed. |
| Final backend suite | `python -m pytest -q` | PASS: 128 passed. |
| Django checks | Test/SQLite system check and migration drift check. | PASS: no issues/no migration changes. |
| Python and diff checks | Targeted compilation and `git diff --check`. | PASS. |
| Production settings simulation | Set DEBUG off in isolated test configuration and checked HTTPS/cookie/CORS defaults. | Secure defaults verified; HSTS warning remains intentionally open. |
| Initial integrated browser smoke | Exercised dashboard NGO submission/status and admin NGO additional-document review using mocked API responses. | Historical smoke only; not counted as Selenium evidence. |
| Initial Selenium review | Collected Selenium test cases before configuring the browser test environment. | 91 collected; execution was blocked at that phase. Superseded by the final execution below. |
| Final Selenium execution | Ran the Selenium directory: 51 WebDriver cases plus 47 HTTP-only page-route checks; corrected four NGO fixture failures and reran them. | 51 browser cases passed with screenshots; 47 route checks passed; 98 unique cases passed after reruns. |
| Final backend and configuration checks | Reran backend suite, Django test-settings check, migration drift, and diff check. | 128 backend tests passed; no system issues, migration drift, or whitespace errors. |
| Frontend syntax review | No standalone frontend lint/build command is configured. | Not tested independently; browser workflows exercised the JavaScript used by those pages. |
| MySQL validation | Attempted normal Django configuration checks. | BLOCKED: local `mysqlclient`/`MySQLdb` missing. |
| Submission preparation | Updated editable Markdown sources, regenerated PDFs from the latest sources, and checked PDF headers and page counts. | CEP report: 6 pages; requirement change log: 2 pages. Both remain drafts because teacher sample and team evidence are absent. |

No production database was accessed or changed. No video recording, commit,
push, or Git-history rewrite was performed. Selenium browser evidence and
generated documentation are under `project_documentation/`.
