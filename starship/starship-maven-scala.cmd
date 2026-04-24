@echo off

if not exist pom.xml exit /b 1
if not exist src\main\scala\nul exit /b 1

for /f "tokens=3 delims=<>" %%A in ('findstr /R /C:"<scala.version>.*</scala.version>" /C:"<scala.binary.version>.*</scala.binary.version>" pom.xml') do (
    echo v%%A
    exit /b 0
)

exit /b 1
