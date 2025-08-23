@echo off
set BASE_DIR=pipeline

rem -------------------------------
rem SynPUF Project Directory Setup
rem -------------------------------

mkdir %BASE_DIR%\logs
mkdir %BASE_DIR%\raw\beneficiary
mkdir %BASE_DIR%\raw\inpatient
mkdir %BASE_DIR%\raw\outpatient
mkdir %BASE_DIR%\raw\carrier
mkdir %BASE_DIR%\raw\pde

mkdir %BASE_DIR%\parquet\beneficiary
mkdir %BASE_DIR%\parquet\inpatient
mkdir %BASE_DIR%\parquet\outpatient
mkdir %BASE_DIR%\parquet\carrier
mkdir %BASE_DIR%\parquet\pde

echo ✅ Directory structure created under "%BASE_DIR%\"
pause
