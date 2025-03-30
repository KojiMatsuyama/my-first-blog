def is_planned_day_matching(target: str, mask: str) -> bool:
    """
    評価対象の曜日と計画曜日を基に論理和を計算し、
    結果が計画曜日と一致する場合はTrue、一致しない場合はFalseを返す。

    Args:
        target (str): 実施された曜日（8文字のビット文字列）
        mask (str): 計画曜日（8文字のビット文字列）

    Returns:
        bool: 論理和の結果が計画曜日と一致するかどうか
    """
    # 入力値の長さチェック
    if len(target) != 8 or len(mask) != 8:
        raise ValueError(
            f"Invalid input: Both 'target' and 'mask' must be 8-character binary strings. Got target='{target}', mask='{mask}'"
        )

    # 入力値が2進数か確認
    if not (target.isdigit() and mask.isdigit()) or not all(c in "01" for c in target + mask):
        raise ValueError("Both 'target' and 'mask' must contain only binary digits (0 or 1).")

    # 2進数に変換
    target_int = int(target, 2)
    mask_int = int(mask, 2)

    # 論理和を計算
    result = target_int | mask_int

    # 結果を元の形式（文字列）に戻して評価
    return format(result, '08b') == mask


if __name__ == "__main__":
    # テストケース
    assert is_planned_day_matching("10000000", "11000000") == True
    assert is_planned_day_matching("10101010", "11111111") == True
    assert is_planned_day_matching("00000000", "00000000") == True
    assert is_planned_day_matching("10101010", "10000000") == False
    print("すべてのテストが成功しました！")
