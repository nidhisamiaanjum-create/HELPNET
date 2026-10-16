# HELPNET database and upload backup

This procedure covers a MySQL database and files stored in the backend's
`media/` and `private_media/` directories. Run backups on a trusted machine and
store them outside the repository. Private verification documents can contain
sensitive personal information; encrypt backup storage and limit access.

## Create a backup (PowerShell)

Load `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_NAME` from the deployment's
secret store or environment. Do not put the database password in the command
line or commit a backup. `mysqldump --password` prompts for it.

```powershell
$backupDir = "D:\HELPNET-backups"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

mysqldump --host="$env:DB_HOST" --port="$env:DB_PORT" `
  --user="$env:DB_USER" --password --single-transaction `
  --routines --triggers --result-file="$backupDir\helpnet-$stamp.sql" `
  "$env:DB_NAME"

tar -a -c -f "$backupDir\helpnet-media-$stamp.zip" `
  -C "backend" media private_media
```

If uploads are configured to use an external storage provider in a deployment,
back up that provider's objects and credentials separately; the local archive
does not include remote objects.

## Restore to a dedicated recovery database

Restore only to a newly created or intentionally selected recovery database.
Set `DB_NAME` to that database and keep the original production database name
unchanged. MySQL prompts for the password.

```powershell
mysql --host="$env:DB_HOST" --port="$env:DB_PORT" `
  --user="$env:DB_USER" --password "$env:DB_NAME" `
  < "D:\HELPNET-backups\helpnet-YYYYMMDD-HHMMSS.sql"

Expand-Archive `
  -LiteralPath "D:\HELPNET-backups\helpnet-media-YYYYMMDD-HHMMSS.zip" `
  -DestinationPath "backend" -Force
```

After restore, verify the target database settings, run `py backend/manage.py
check`, inspect representative users/listings/requests, and confirm private and
public uploads can be read by their intended application flows. Record the
backup timestamp, restore duration, and any missing files. This document is a
procedure; it does not claim that automated backups or a restore drill are
currently configured.
