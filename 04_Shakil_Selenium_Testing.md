# HELPNET Selenium Testing — Shakil

## Scope

Test only the completed Shakil work:

- ST 41 — Waste pickup
- ST 42 — Waste collector rating/report
- ST 43 — Farmer produce listing
- ST 44 — Consumer views/contact farmer
- ST 45 — Simple farmer UI
- ST 47 — Farmer marketplace disclaimer

Do NOT test Mokarram's ST 48 price range or ST 55 work.

---

## 1. Setup

```powershell
cd E:\HELPNET
.\.venv\Scripts\Activate.ps1
pip install selenium pytest pytest-django
python manage.py runserver
```

Run all Shakil tests:

```powershell
pytest tests\selenium\test_shakil.py -v
```

Run one test:

```powershell
pytest tests\selenium\test_shakil.py -v -k "waste_pickup"
```

---

# ST 41 — Waste pickup

### Test

Login as citizen.

Create a waste pickup request:

```text
Waste type
Area/location
Preferred pickup date/time if available
```

Submit.

Verify request appears successfully.

Then verify nearby/available collector contact information is displayed where implemented.

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "waste_pickup"
```

### Negative test

Submit without a required field.

Expected:

```text
Validation error is shown.
Request is not incorrectly created.
```

---

# ST 42 — Collector rating/report

### Test

After pickup:

- Open collector details.
- Submit a valid rating.
- Verify success.
- If report is implemented for this story, submit a report and verify success.

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "collector_rating"
```

---

# ST 43 — Farmer produce listing

### Test

Login as farmer.

Create:

```text
Produce name
Price
Quantity
Availability
General location
Description
```

Submit.

Verify listing appears in farmer marketplace.

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "produce_listing"
```

### Negative test

Try submitting without required produce information.

Expected:

```text
Validation error.
```

---

# ST 44 — Consumer view/contact farmer

### Test

- Login as consumer.
- Open farmer marketplace.
- Select produce listing.
- Open details.
- Verify farmer information.
- Verify allowed contact information is visible.

No payment should be required.

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "consumer_contact"
```

---

# ST 45 — Simple farmer UI

Use Selenium to inspect the farmer marketplace pages.

Verify:

```text
Large/clickable main buttons.
Clear labels.
Simple form.
Few steps to create listing.
Basic mobile-friendly layout.
```

If the test suite supports viewport resizing:

```python
driver.set_window_size(390, 844)
```

Then verify important controls remain visible/clickable.

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "farmer_ui"
```

---

# ST 47 — Farmer marketplace disclaimer

Open farmer marketplace and produce details.

Verify the required disclaimer about:

```text
HELPNET not handling payment or delivery.
Arrangements being directly between farmer and consumer.
```

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "farmer_disclaimer"
```

---

# Protected-action test

For waste creation and farmer listing:

1. Logout.
2. Open the page.
3. Try the protected action.

Expected:

```text
Unauthenticated user cannot perform protected action.
```

### Command

```powershell
pytest tests\selenium\test_shakil.py -v -k "protected"
```

---

# Final command

```powershell
pytest tests\selenium\test_shakil.py -v
```

Record:

```text
ST 41  PASS   (test_waste_pickup_success, test_waste_pickup_validation_error)
ST 42  PASS   (test_collector_rating_and_report)
ST 43  PASS   (test_produce_listing_success, test_produce_listing_validation_error)
ST 44  PASS   (test_consumer_contact_farmer)
ST 45  PASS   (test_farmer_ui_layout_and_responsive)
ST 47  PASS   (test_farmer_disclaimer_displayed)
```

---

## Run Summary

```
Platform  : win32 — Python 3.14.0, pytest-8.4.2, Django 5.2.17
Config    : pytest.ini (DJANGO_SETTINGS_MODULE = helpnet.settings)
Date      : 2026-09-30
Command   : pytest tests/selenium/test_shakil.py -v --tb=short

Collected : 9 tests
Passed    : 9
Failed    : 0
Duration  : 49.92s
```
