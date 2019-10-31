# cron-multiple-tz
This project helps to configure cron tasks in multiple timezones under single userid/spool.

# Exisiting issue
The popular cron deamon in **nix** environment, is used to schedule tasks/jobs at specified time/date. Such tasks are of administrative nature.
cron daemon doesn't support running jobs in different timezones. 

Given situation, my server in UK - which has local timezone as Europe/London. One can schedule jobs only in London time. In the same box if i want to run some jobs in UK time and other jobs in NewYork time, then the user has to manually adjust for NewYork timezone different and schedule the job in UK time.

## Cron-Multiple-Tz

# Sample cron file

```
# SERVER_TZ=Asia/Calcutta
# Activity reports every 10 minutes everyday
5-10,20-30/2 6,7 7 8 1 root command -v debian-sa1 > /dev/null && debian-sa1 1 1
# JOB_TZ=Europe/London
* 20 * * 1 root command -v debian-sa1 > /dev/null && debian-sa1 1 1 ##JOB1
#
# JOB_TZ=America/New_York
* 20 * * 1 root command -v debian-sa1 > /dev/null && debian-sa1 1 1 ##JOB2
#
# JOB_TZ=Europe/London
* 5 * * 1-5 root command -v debian-sa1 > /dev/null && debian-sa1 1 1 ##JOB3
#
# JOB_TZ=Europe/London
30 5 * * 7 root command -v debian-sa1 > /dev/null && debian-sa1 1 1 ##JOB4
#
# JOB_TZ=Asia/Tokyo
30 5 * * 1 root command -v debian-sa1 > /dev/null && debian-sa1 1 1 ##JOB5
```

Here ***#SERVER_TZ*** specifies the time zone of the cron daemon.   
***#JOB_TZ*** specifies the timezone of the job. User doesn't need to convert from job tz to server tz manually.  

   * Cron deamon is running in Asia/Calcutta timezone.   
   * JOB1 is in Europe/London tz. In other words the job is scheduled to run every monday at 20hrs London time.   
   * JOB2 is in America/New_York tz. In other words the job is scheduled to run every monday at 20hrs New_York time   
   * JOB5 is in Tokyo tz. Job is scheduled to run every monday at 5.30 japan time.   

# Usage

Running the script would produce cron entries in server tz.

```
$  python3 cron_tz_conv.py -i input_cron_file -o adjusted_out_cron_file
# The first element of the path is a directory where the debian-sa1
# script is located
PATH=/usr/lib/sysstat:/usr/sbin:/usr/sbin:/usr/bin:/sbin:/bin

# SERVER_TZ=Asia/Calcutta
# Activity reports every 10 minutes everyday
5-10,20-30/2 6,7 7 8 1  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
# JOB_TZ=Europe/London
30 1 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
31 1 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
.......
8 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
9 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
# JOB_TZ=America/New_York
30 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
31 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
32 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
33 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
.....
8 7 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
9 7 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
# JOB_TZ=Europe/London
0 11 * * 7  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
# JOB_TZ=Asia/Tokyo
0 2 * * 1  root command -v debian-sa1 > /dev/null && debian-sa1 1 1

# Additional run at 23:59 to rotate the statistics file
#59 23 * * * command -v debian-sa1 > /dev/null && debian-sa1 60 2

8 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
9 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
# JOB_TZ=America/New_York
30 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
31 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
32 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
33 6 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
.....
8 7 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
9 7 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
# JOB_TZ=Europe/London
0 11 * * 7  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
# JOB_TZ=Asia/Tokyo
0 2 * * 1  root command -v debian-sa1 > /dev/null && debian-sa1 1 1

# Additional run at 23:59 to rotate the statistics file
#59 23 * * * command -v debian-sa1 > /dev/null && debian-sa1 60 2
....
```

   * -i specifiles input cron file. this file can contain jobs in varous timezones.   
   * -o contains jobs scheduled time converted to local timezone, **SERVER_TZ** . Defauts to stdout.   


The script converts only jobs that have JOB_TZ in their previous line. Rest of the lines are written as it is.
As we can see, job scheduled in Asia/Tokyo timezone as monday 5.30 is converted to cron daemon timezone Asia/Calcutta 2.00.

User can use the file as his crontab file.

There are some odd tz conversions. 
```
# JOB_TZ=Europe/London
* 20 * * 1 root command -v debian-sa1 > /dev/null && debian-sa1 1 1 ##JOB1
```

This job is scheduled to run on all monday at 8pm for every minute london time. As Calcutta is 5.30 hrs, summer time, ahead of  london the job needs to run every tuesday from 1.30am to 2.30am. The timezone adjuster converts accordingly.
```
# JOB_TZ=Europe/London
30 1 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
31 1 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
.......
17 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
18 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
19 2 * * 2  root command -v debian-sa1 > /dev/null && debian-sa1 1 1
#
```
It expands the entries, scheduling for every minute from 1.30-2.30am. Though it outputs 60 entries for every minute, it achieves the goal.
