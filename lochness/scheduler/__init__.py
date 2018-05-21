import time
import datetime as dt

format = '%Y-%m-%dT%H:%M:%S'

def parse(date):
    '''parse date into a date object'''
    d = dt.datetime.strptime(date, format)
    return d

class DateFormatError(Exception):
    pass

def until(future):
    '''sleep until date'''
    if not future:
        return
    now = dt.datetime.now()
    seconds = (future - now).total_seconds()
    if seconds >= 0:
        time.sleep(seconds)

