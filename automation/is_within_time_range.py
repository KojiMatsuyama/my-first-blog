from datetime import datetime, timedelta


def is_within_time_range(actual_time_str, planned_time_str=None, tolerance_minutes=30):
    """
    実施された時刻が計画時刻から許容範囲内にあるかを判定する関数。
    計画時刻が 'ANY_TIME' であれば、実施された時刻は常にOKとする。

    :param actual_time_str: 実施された時刻（"YYYYMMDDHHMMSS"形式の文字列）
    :param planned_time_str: 計画時刻（"YYYYMMDDHHMMSS"形式の文字列、デフォルトはNone）
    :param tolerance_minutes: 許容範囲（分単位、デフォルトは30分）
    :return: 範囲内であれば True、範囲外であれば False、計画時刻が 'ANY_TIME' であれば常に True
    """

    # 計画時刻が 'ANY_TIME' ならば、実施された時刻は全てOK
    if planned_time_str == 'ANY_TIME':
        return True

    # 実施された時刻を datetime 型に変換
    actual_time = datetime.strptime(actual_time_str, "%Y%m%d%H%M%S")

    # 計画時刻が None であれば比較しない
    if planned_time_str is None:
        return True

    # 計画時刻を datetime 型に変換（'ANY_TIME' 以外の場合のみ）
    try:
        planned_time = datetime.strptime(planned_time_str, "%Y%m%d%H%M%S")
    except ValueError:
        # フォーマットが違う場合はエラーを返す
        raise ValueError(f"Invalid date format for planned_time_str: {planned_time_str}")

    # 計画時刻に対する許容範囲を設定
    tolerance_delta = timedelta(minutes=tolerance_minutes)
    start_time = planned_time - tolerance_delta
    end_time = planned_time + tolerance_delta

    # 実施された時刻が許容範囲内にあるか判定
    return start_time <= actual_time <= end_time


# 使用例
actual = "20250329150000"  # 実施された時刻
planned = "20250329120000"  # 計画時刻
special = "ANY_TIME"  # 計画時刻に特別な値を渡す場合

# 実施された時刻が許容範囲内かを判定
result = is_within_time_range(actual, planned)

if result:
    print("実施された時刻は範囲内です。")
else:
    print("実施された時刻は範囲外です。")

# 計画時刻に特別な値を渡した場合
result_special = is_within_time_range(actual, special)

if result_special:
    print("計画時刻に特別な値が渡されました。")
