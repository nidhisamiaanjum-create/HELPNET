from django.db import migrations


def import_goods_reports(apps, schema_editor):
    GoodsReport = apps.get_model("goods", "GoodsReport")
    Report = apps.get_model("reports", "Report")
    ContentType = apps.get_model("contenttypes", "ContentType")
    content_type, _ = ContentType.objects.get_or_create(
        app_label="goods",
        model="goodslisting",
    )
    status_map = {
        "Open": "pending",
        "Reviewed": "reviewed",
        "Resolved": "resolved",
    }
    for old_report in GoodsReport.objects.select_related("listing", "reporter").iterator():
        listing = old_report.listing
        if listing is None:
            continue
        description = "\n".join(
            part for part in (old_report.reason, old_report.description) if part
        )
        Report.objects.create(
            reporter=old_report.reporter,
            reported_user=listing.seller,
            content_type=content_type,
            object_id=str(listing.pk),
            category="fraud",
            description=description,
            status=status_map.get(old_report.status, "pending"),
            created_at=old_report.created_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("goods", "0001_initial"),
        ("reports", "0002_report_content_target"),
    ]

    operations = [
        migrations.RunPython(import_goods_reports, migrations.RunPython.noop),
    ]
