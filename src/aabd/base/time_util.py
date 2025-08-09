import time
from datetime import datetime, timedelta, timezone

time_str_format = ['%Y-%m-%d %H:%M:%S.%f',
                   '%Y-%m-%d %H:%M:%S',
                   '%Y-%m-%d',
                   '%Y-%m-%dT%H:%M:%S.%f',
                   '%Y-%m-%dT%H:%M:%S']


def str2timestamp(time_str):
    try:
        return int(time_str)
    except:

        for str_f in time_str_format:
            try:
                date_time_obj = datetime.strptime(time_str, str_f)
                return int(date_time_obj.timestamp() * 1000)
            except:
                continue
    raise Exception('format time error')


def timestamp_ms2str(timestamp_ms):
    dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)

    # 格式化datetime对象为指定格式
    formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    return formatted_date


def ms_to_str(milliseconds, split_char=':'):
    milliseconds = int(milliseconds)
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}{split_char}{minutes:02d}{split_char}{seconds:02d}.{milliseconds:03d}"


def ms_to_str_auto(milliseconds, include_split_char=True, include_ms=True):
    return vms2str_auto(milliseconds, include_split_char, include_ms)


def vms2str_auto(milliseconds=time.time() * 1000, include_split_char=True, include_ms=True):
    milliseconds = int(milliseconds)

    # 判断是否需要包含毫秒部分
    if not include_ms:
        milliseconds_part = ''
    else:
        if include_split_char:
            milliseconds_part = f".{milliseconds % 1000:03d}"
        else:
            milliseconds_part = f"{milliseconds % 1000:03d}"

    # 如果毫秒数大于等于1970年（63115200000）则视为完整时间戳
    if milliseconds >= 63115200000:
        end_date = datetime.fromtimestamp(milliseconds/1000)

        if include_split_char:
            formatted_time = end_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted_time = end_date.strftime("%Y%m%d%H%M%S")

        return f"{formatted_time}{milliseconds_part}"

    else:
        # 否则表示时间段，只显示时分秒
        seconds, millis = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if include_split_char:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{hours:02d}{minutes:02d}{seconds:02d}"

        return f"{time_str}{milliseconds_part}"


if __name__ == '__main__':
    # 示例调用
    print(vms2str_auto())  # 有分隔符，含毫秒
    print(vms2str_auto(1752223212000, include_split_char=True, include_ms=True))  # 有分隔符，含毫秒
    print(vms2str_auto(1752223212000, include_split_char=True, include_ms=False))  # 有分隔符，含毫秒
    print(vms2str_auto(1752223212000, include_split_char=False, include_ms=False))  # 无分隔符，不含毫秒
    print(vms2str_auto(1752223212000, include_split_char=False, include_ms=True))  # 无分隔符，不含毫秒
    print(vms2str_auto(5000, include_split_char=True, include_ms=True))  # 短时间，有分隔符，含毫秒
    print(vms2str_auto(5000, include_split_char=True, include_ms=False))  # 短时间，有分隔符，含毫秒
    print(vms2str_auto(5000, include_split_char=False, include_ms=False))  # 短时间，无分隔符，不含毫秒
    print(vms2str_auto(5000, include_split_char=False, include_ms=True))  # 短时间，无分隔符，不含毫秒
