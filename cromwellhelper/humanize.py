import datetime


def humanize_bytes(byte_count: int, base: int = 1024) -> str:
    if byte_count >= base * base * base * base * base:
        return '{:.1f} PB'.format(byte_count /
                                  (base * base * base * base * base))
    if byte_count >= base * base * base * base:
        return '{:.1f} TB'.format(byte_count / (base * base * base * base))
    if byte_count >= base * base * base:
        return '{:.1f} GB'.format(byte_count / (base * base * base))
    if byte_count >= base * base:
        return '{:.1f} MB'.format(byte_count / (base * base))
    if byte_count >= base:
        return '{:.1f} kB'.format(byte_count / base)
    return '{} B'.format(byte_count)


def humanize_time_delta(d: datetime.timedelta) -> str:
    if d.days > 0:
        hum = '{:.0f} days'.format(d.days)
        if hum == '1 days':
            return '1 day'
        return hum
    sec = d.seconds
    if sec >= 60 * 60:
        hum = '{:.0f} hours'.format(int(sec / (60 * 60)))
        if hum == "1 hours":
            return '1 hour'
        return hum
    if sec >= 60:
        hum = '{:.0f} minutes'.format(int(sec / (60)))
        if hum == '1 minutes':
            return '1 minute'
        return hum
    hum = '{} seconds'.format(int(sec))
    if hum == '1 seconds':
        return '1 second'
    return hum
