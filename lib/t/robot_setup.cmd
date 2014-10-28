SETLOCAL

SET JUB_SRC=%~dp0..\..\..\jubjub_robofab
SET JUB_DST=%~dp0..\..\arena\robots\jubjub_robofab
mkdir "%JUB_DST%"
copy "%JUB_SRC%\RandomRunner.class" "%JUB_DST%"
@ECHO RandomRunner.class>"%JUB_DST%\RandomRunner.robot"

SET SAMPLEDIR=%~dp0..\..\arena\robots\sample
:: xcopy /e /i /y "%~dp0..\robocode\robots\sample" "%SAMPLEDIR%"

FOR /F %%b IN ('perl -e "print(join(qq(\n),qw(Crazy Fire VelociRobot Tracker RamFire SittingDuck SpinBot TrackFire Walls)));"') DO @ECHO %%b.class>"%SAMPLEDIR%\%%b.robot"

DIR /S %~dp0..\..\arena\robots\*.robot