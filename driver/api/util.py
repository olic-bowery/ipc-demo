import os
from datetime import datetime, date


def current_time() -> str:
    return datetime.now().strftime("%m_%d_%Y-%H_%M_%S")


def current_hour() -> str:
    return datetime.now().strftime("%m_%d_%Y-%H_00_00")


def to_hour(d: date) -> str:
    return d.strftime("%m_%d_%Y-%H_00_00")


def current_time_min() -> int:
    now = datetime.now()
    return now.hour * 60 + now.minute


def offset_to_datetime(offset: int) -> datetime:
    assert offset <= 1440
    today = date.today()
    return datetime(today.year, today.month, today.day, int(offset / 60), (offset % 60), 0)


def set_timezone():
    """
    mule@mule:~ $ timedatectl set-timezone America/Los_Angeles
==== AUTHENTICATING FOR org.freedesktop.timedate1.set-timezone ===
Authentication is required to set the system timezone.
Authenticating as: ,,, (mule)
Password:
==== AUTHENTICATION COMPLETE ===
mule@mule:~ $ timedatectl
               Local time: Tue 2022-12-27 11:13:37 PST
           Universal time: Tue 2022-12-27 19:13:37 UTC
                 RTC time: n/a
                Time zone: America/Los_Angeles (PST, -0800)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
mule@mule:~ $ date
    :return:
    """
    pass


def get_report_path(data_dir: str):
    report_dir = os.path.join(data_dir, 'report')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    return os.path.join(report_dir, f'report_{current_hour()}.csv')


def get_dump_path(data_dir: str):
    report_dir = os.path.join(data_dir, 'dump')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    return os.path.join(report_dir, f'dump_{current_hour()}.csv')


CROP_IMG_DIR = 'static/crop_image'


def clear_crop_images():
    for f in os.scandir(CROP_IMG_DIR):
        os.remove(f.path)
