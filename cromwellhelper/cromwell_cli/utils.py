import datetime
import re

CROMWELL_TIME = re.compile(
    r'(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)\.(\d\d\d)Z')


def convert_localtime(s: str) -> str:
    m = CROMWELL_TIME.match(s)
    if not m:
        raise Exception("unknown format: " + s)
    d = datetime.datetime(year=int(m.group(1)),
                          month=int(m.group(2)),
                          day=int(m.group(3)),
                          hour=int(m.group(4)),
                          minute=int(m.group(5)),
                          second=int(m.group(6)),
                          microsecond=int(m.group(7)) * 1000,
                          tzinfo=datetime.timezone.utc)
    local_time = d.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
    return local_time.strftime("%Y-%m-%d %H:%M:%S%z")


def print2(f: str,
           d: dict,
           key: str,
           *args,
           value_map=(lambda x: x),
           **keywords):
    if key in d:
        print(f.format(value=value_map(d[key]), *args, **keywords))


def summarize_command(command: str) -> str:
    if len(command) > 70:
        command = command[:67] + '...'
    return command.replace('\n', ' ')
