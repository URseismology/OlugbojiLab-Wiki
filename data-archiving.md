# LabAI Data Archiving Architecture

This document outlines the architecture, logic, and failover mechanisms for the massive data archival pipeline between the lab's high-performance compute nodes (e.g., `terravibranium`) and the Synology NAS devices (`repovibranium` and `ATOS-nas`).

## 1. Overview
The lab handles petabytes of seismic data across millions of files. When data becomes older than 2 years (`-mtime +730`), it is automatically swept from the active compute nodes and archived into the multi-volume USB storage arrays attached to the `ATOS-nas`.

Because the data volumes exceed the capacity of a single hard drive, the system features a **Fault-Tolerant Automated USB Spillover** mechanism. 

## 2. Dynamic Disk Spillover Logic
Synology does not natively pool USB drives into a single logical volume (e.g., it mounts `/volumeUSB1`, `/volumeUSB2`, etc. individually). To prevent `rsync` from failing when a single 13 TB disk hits 100% capacity, the archival scripts execute a dynamic disk selector via `awk` on the `df` command output.

```bash
# Finds the first USB volume with >500 GB of free space
DEST_VOL=$(df -BG /volumeUSB*/usbshare | awk 'NR>1 && $4+0 > 500 {print $6; exit}')
```
This check is executed dynamically *before every 5,000-file batch*. This guarantees that if a disk fills up mid-transfer, the very next batch seamlessly redirects to the next empty drive in the chassis.

## 3. The Scripts

### 3.1 Push: `archive_old_data_terra.sh`
- **Source:** `terravibranium` (`/RAID6/`)
- **Destination:** `ATOS-nas`
- **Mechanism:** Runs on the compute node. Because it must query the destination's disk space, it executes the `df` check *over SSH* to the `ATOS-nas` before firing the `rsync` push.
- **Flags:** Uses `--remove-source-files` to guarantee that files are instantly deleted from the source node only *after* they are successfully verified on the destination.

### 3.2 Pull: `pull_archive_repo.sh`
- **Source:** `repovibranium` (`/volume1/bluehiveBackup/`)
- **Destination:** `ATOS-nas`
- **Mechanism:** Runs locally on `ATOS-nas` and pulls data over SSH from `repovibranium`. It leverages `find . -print0` piped into `xargs -0` over the SSH boundary to safely handle complex filenames with spaces.

## 4. Resilience and Resumption
If a transfer is interrupted (e.g., node reboot or network drop), the script can be cleanly restarted via `nohup` in the background. Because of the `--remove-source-files` approach, `find` will simply skip all data that was successfully archived, picking up the transfer exactly where it failed with zero data duplication.

## 5. Audit Trail
After clearing out a directory of old data, the scripts drop a `README_ARCHIVED.txt` placeholder file into the empty directory on the compute node. This serves as an audit trail for users looking for their old data, indicating the exact date and NAS destination where their files were relocated.
