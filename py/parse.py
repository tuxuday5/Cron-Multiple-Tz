#!/usr/bin/python3
import re
import pytz
import calendar
import operator
import pprint

CRON_FILE = 'cron.file'

class InvalidCronEntryError(Exception):
    pass

DEFAULT_VALUES = {
    'minute' : '',
    'hour' : '',
    'dom' : '',
    'month' : '',
    'dow' : '',
    'year' : '',
}

VALID_SPECIAL_STRINGS = [
    '@reboot',
    '@yearly',
    '@annually',
    '@monthly',
    '@weekly',
    '@daily',
    '@midnight',
    '@hourly',
]

#monthNames = calender.month_abbr
#dayOfWeekNames = calender.day_abbr

REGEX_PATTERNS = {
    'server_tz' : re.compile('^#\s*SERVER_TZ='),
    'job_tz' : re.compile('^#\s*JOB_TZ='),
    'comment' : re.compile('^\s*#'),
    'blank_line' : re.compile('^\s*$'),
    'variable' : re.compile('^\s*\w+='),
    'parse_entry' : re.compile('\s'),
    'astreisk' : re.compile('^\s*\*\s*$'),
    'range' : re.compile('-'),
    'list' : re.compile(','),
    'step' : re.compile('/'),
}

JOB_ENTRY_ORDER = ['minute', 'hour', 'month', 'dom', 'dow', 'command']
CRON_FILED_HAS_ASTERISK = { }

def SetCronFieldAsteriskDefaultValues():
    for x in JOB_ENTRY_ORDER:
        CRON_FILED_HAS_ASTERISK[x] = False

def SetCronFieldAsterisk(field):
    CRON_FILED_HAS_ASTERISK[field] = True

def UnsetCronFieldAsterisk(field):
    CRON_FILED_HAS_ASTERISK[field] = False

def SetDefaultValues():
    td = pytz.datetime.datetime.now()
    DEFAULT_VALUES['year'] = [td.year]
    DEFAULT_VALUES['minute'] = [0,59]
    DEFAULT_VALUES['hour'] = [0,23]
    DEFAULT_VALUES['dom'] = [1]
    DEFAULT_VALUES['month'] = [1,12]
    DEFAULT_VALUES['dow'] = [1,7]
    DEFAULT_VALUES['month'] = [1] # for month it is ok.
    return
    #td = pytz.datetime.datetime.now()

    #DEFAULT_VALUES['year'] = [td.year]
    #DEFAULT_VALUES['minute'] = [0,59]
    #DEFAULT_VALUES['hour'] = [0,23]
    #DEFAULT_VALUES['dom'] = [1,31]
    #DEFAULT_VALUES['month'] = [1,12]
    #DEFAULT_VALUES['dow'] = [1,7]

def IsValidCronEntry(line):
    return True

def ParseCronEntry(line):
    values = []
    command = ''
    record = {
        'minute' : '',
        'hour' : '',
        'dom' : '',
        'month' : '',
        'dow' : '',
        'command' : '',
    }

    entries = line.split()
    for entry in entries:
        if REGEX_PATTERNS['blank_line'].match(entry):
            continue
        if len(values) >= 5:
            command += ' ' + entry
        else:
            values.append(entry)

    values.append(command)

    for k in range(len(JOB_ENTRY_ORDER)):
        record[JOB_ENTRY_ORDER[k]] = values[k]

    return record

def ExpandRange(r,s=1):
    if REGEX_PATTERNS['step'].search(r):
        [r1,s] = r.split('/')
        s=int(s)
    else:
        r1 = r

    (start,end) = r1.split('-')
    return [i for i in range(int(start),int(end)+1,s)]

def NormalizeEntry(inp):
    expanded = []
    if REGEX_PATTERNS['list'].search(inp):
        for entry in inp.split(','):
            if REGEX_PATTERNS['range'].search(entry):
                expanded.extend(ExpandRange(entry))
            else:
                expanded.append(entry)
    elif REGEX_PATTERNS['range'].search(inp):
        expanded.extend(ExpandRange(inp))
    else:
        expanded = [ inp ] # expanded.append(inp) too will do

    retVal = []
    for x in expanded:
        try:
            retVal.append(int(x))
        except ValueError:
            pass

    return retVal

def ExpandMonths(inp):
    if REGEX_PATTERNS['astreisk'].match(inp):
        SetCronFieldAsterisk('month')
        return DEFAULT_VALUES['month']
        #return [x for x in range(1,12+1)]
        #return [DEFAULT_VALUES['month']]
    else:
        return NormalizeEntry(inp)

def ExpandDoM(inp):
    if REGEX_PATTERNS['astreisk'].match(inp):
        SetCronFieldAsterisk('dom')
        return [DEFAULT_VALUES['dom']]
        #return [x for x in range(1,31+1)]
        #return DEFAULT_VALUES['dom']
    else:
        return NormalizeEntry(inp)

def ExpandDoW(inp):
    if REGEX_PATTERNS['astreisk'].match(inp):
        SetCronFieldAsterisk('dow')
        return [x for x in range(1,7+1)]
        #return DEFAULT_VALUES['dow']
        #return [DEFAULT_VALUES['dow']]
    else:
        return NormalizeEntry(inp)

def ExpandHour(inp):
    if REGEX_PATTERNS['astreisk'].match(inp):
        SetCronFieldAsterisk('hour')
        return [x for x in range(0,23+1)]
        #return DEFAULT_VALUES['hour']
        #return [DEFAULT_VALUES['hour']]
        #return [x for x in range(0,23+1)]
    else:
        return NormalizeEntry(inp)

def ExpandMinutes(inp):
    if REGEX_PATTERNS['astreisk'].match(inp):
        SetCronFieldAsterisk('minute')
        return [x for x in range(0,59+1)]
        #return DEFAULT_VALUES['minute']
        #return [DEFAULT_VALUES['minute']]
    else:
        return NormalizeEntry(inp)

def GetEntryAsTimeStamps(record,tz):
    expandedTs = []

    year = DEFAULT_VALUES['year'][0]
    expandedMonth = ExpandMonths(record['month'])
    expandedDoM = ExpandDoM(record['dom'])
    expandedDoW = ExpandDoW(record['dow'])
    expandedHours = ExpandHour(record['hour'])
    expandedMins = ExpandMinutes(record['minute'])

    for month in expandedMonth:
        for d in calendar.Calendar(firstweekday=1).itermonthdates(year,month):
            if d.month != month: #itermonthdates() returns complete weeks at beg,end
                continue 

            shouldProcess = False
            try:
                shouldProcess = True if expandedDoM.index(d.day) >= 0 else False
            except ValueError:
                try:
                    shouldProcess = True if expandedDoW.index(d.isoweekday()) >= 0 else False
                except ValueError:
                    pass

            if shouldProcess:
                for hr in expandedHours:
                    for mins in expandedMins:
                        expandedTs.append(pytz.datetime.datetime(d.year,d.month,d.day,hr,mins))

    return expandedTs

def AdjustForTz(record,serverTz,jobTz):
    ts = GetEntryAsTimeStamps(record,serverTz)

    adjustedEntries = []
    utcTzObj = pytz.utc
    serverTzObj = pytz.timezone(serverTz)
    jobTzObj = pytz.timezone(jobTz)

    for t in ts:
        jobTs = jobTzObj.localize(t)
        utcTs = jobTs.astimezone(utcTzObj)
        serverTs = utcTs.astimezone(serverTzObj)
        #print(ReplaceEntryWithServerTs(record,serverTs))
        adjustedEntries.append(ReplaceEntryWithServerTs(record,serverTs))

        #print(jobTs,serverTs)
        #print(t,jobTs,utcTs,serverTs)

    return adjustedEntries

def ReplaceEntryWithServerTs(entry,serverTs):
    #if REGEX_PATTERNS['astreisk'].match(inp):
    retVal = {}

    retVal['command'] = entry['command']
    #if REGEX_PATTERNS['astreisk'].match(entry['minute']):
    #    retVal['minute'] = '*'
    #else:
    #    retVal['minute'] = str(serverTs.minute)
    retVal['minute'] = str(serverTs.minute)

    if REGEX_PATTERNS['astreisk'].match(entry['hour']):
        retVal['hour'] = '*'
    else:
        retVal['hour'] = str(serverTs.hour)

    if REGEX_PATTERNS['astreisk'].match(entry['month']):
        retVal['month'] = '*'
    else:
        retVal['month'] = str(serverTs.month)

    if REGEX_PATTERNS['astreisk'].match(entry['dom']):
        retVal['dom'] = '*'
    else:
        retVal['dom'] = str(serverTs.month)

    if REGEX_PATTERNS['astreisk'].match(entry['dow']):
        retVal['dow'] = '*'
    else:
        retVal['dow'] = str(serverTs.isoweekday())

    return retVal

def GetLineAsRecord(line):
    record = {}
    if IsValidCronEntry(line):
        return ParseCronEntry(line)
    else:
        raise InvalidCronEntryError(line)

def PrintEntry(job):
    for k in JOB_ENTRY_ORDER:
        print(job[k],end=' ')

    print('',flush=True)

SetDefaultValues()
SetCronFieldAsteriskDefaultValues()
with open(CRON_FILE) as cronFileHandle:
    serverTz = ''
    jobTz = ''
    isJobTzSet = False
    for line in cronFileHandle:
        if REGEX_PATTERNS['job_tz'].match(line):
            jobTz = line.split('=')[1].strip()
            print(jobTz)
            isJobTzSet = True

        if REGEX_PATTERNS['server_tz'].match(line):
            serverTz = line.split('=')[1].strip()
            print(line,end='',flush=True)
        elif REGEX_PATTERNS['comment'].match(line):
            print(line,end='',flush=True)
        elif REGEX_PATTERNS['blank_line'].match(line):
            print(line,end='',flush=True)
        elif REGEX_PATTERNS['variable'].match(line):
            print(line,end='',flush=True)
        else:
            entryAsRecord = GetLineAsRecord(line)
            #print(line,end='',flush=True)
            if isJobTzSet:
                tzAdjustedEntry = AdjustForTz(entryAsRecord,serverTz,jobTz)
                tzAdjustedEntryUnique = list(map(dict, frozenset(frozenset(tuple(e.items()) for e in tzAdjustedEntry))))
                #pprint.pprint(tzAdjustedEntryUnique)
                tzAdjustedEntryUnique.sort(key=operator.itemgetter('month','dom','dow','hour','minute'))
                for entry in tzAdjustedEntryUnique:
                    #print(entry)
                    PrintEntry(entry)
                isJobTzSet = False
            else:
                PrintEntry(entryAsRecord)
                #tzAdjustedEntry = entryAsRecord
