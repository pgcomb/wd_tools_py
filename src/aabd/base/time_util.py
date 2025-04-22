import datetime

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
                date_time_obj = datetime.datetime.strptime(time_str, str_f)
                return int(date_time_obj.timestamp() * 1000)
            except:
                continue
    raise Exception('format time error')


def timestamp_ms2str(timestamp_ms):
    dt_object = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0)

    # 格式化datetime对象为指定格式
    formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    return formatted_date


def ms_to_str(milliseconds, split_char=':'):
    milliseconds = int(milliseconds)
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}{split_char}{minutes:02d}{split_char}{seconds:02d}.{milliseconds:03d}"
