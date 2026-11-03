# HELPNET

HELPNET is a Bangladesh-focused community services platform for blood donation,
volunteering, health questions, goods exchange, farming, and waste pickup.

## Technology

- Python and Django 5.2
- Django REST Framework and SimpleJWT
- MySQL for regular application runs; SQLite for pytest
- Django templates and vanilla HTML, CSS, and JavaScript

## NGO verification and profiles

An account can hold an NGO profile and personal Citizen, Donor, Farmer, or
Volunteer profiles under the same login. Select the NGO profile from
**Dashboard → My Profiles** to submit organization details and a required
registration certificate; supporting documents are optional. Owners can see
their application status and replace documents after rejection or an additional
documents request. Superusers review applications and access private documents
from **Admin NGO Approval**. NGO verification is separate from the
representative's personal NID verification.

## Local setup

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend\.env` for the local environment. Configure database connection
values and replace the development-only `SECRET_KEY`. Keep `.env` files,
private uploads, and production credentials out of Git.

Apply migrations and start Django:

```powershell
python backend\manage.py migrate
python backend\manage.py runserver
```

The project serves the HTML pages and static files from Django. There is no
separate npm build step.

## Tests and checks

```powershell
pytest
```

The pytest configuration uses a separate SQLite test database. Selenium tests
are in `tests\selenium\`; they require a running app, compatible browser/WebDriver,
and any test accounts/data required by the selected test.

## Project documentation

- [Project summary](PROJECT_SUMMARY.md): modules, API routes, models, and known gaps.
- [Technical documentation](project_documentation/HELPNET_Technical_Documentation.docx)
- [Final academic report](project_documentation/HELPNET_Final_Project_Report.docx)
- [Testing report](project_documentation/HELPNET_Testing_Report.docx)
- [API documentation](project_documentation/HELPNET_API_Documentation.md) and [database documentation](project_documentation/HELPNET_Database_Documentation.md)
- [User manual](project_documentation/HELPNET_User_Manual.docx)
- [Selenium evidence, screenshots, and diagrams](project_documentation/)
- [Selenium test plan](docs/testing/selenium-test-plan.md)
- [Selenium test results](docs/testing/selenium-test-results.md)
- [Sprint 4 volunteer acceptance](docs/sprint4-volunteer-acceptance.md)
- [Backup and restore notes](docs/backup-restore.md)

## Audit and submission drafts

- [Audit reports](audit_reports/FINAL_AUDIT_REPORT.md)
- [Course End Project report source](final_submission/HELPNET_CEP_REPORT.md) and [PDF](final_submission/HELPNET_CEP_REPORT.pdf)
- [Requirement change log source](final_submission/REQUIREMENT_CHANGE_LOG.md) and [PDF](final_submission/REQUIREMENT_CHANGE_LOG.pdf)
- [Video demonstration script](final_submission/VIDEO_DEMONSTRATION_SCRIPT.md) (script only; no recording is claimed)
