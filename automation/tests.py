# utils.pyにevaluate_bitwise_orがあることを前提としています。
from utils import evaluate_bitwise_or


def evaluate_bitwise_or(target: str, mask: str) -> bool:
    """
    ビットごとのOR演算を行い、targetに対するmaskの影響を評価する。
    :param target: 対象となる2進数文字列
    :param mask: マスクとしての2進数文字列
    :return: OR演算の結果が期待通りならTrue、そうでなければFalse
    """
    # targetとmaskの長さを確認（長さが異なる場合はエラー）
    if len(target) != len(mask):
        raise ValueError("targetとmaskは同じ長さである必要があります")

    # ビットごとのOR演算を実行
    result = int(target, 2) | int(mask, 2)

    # 結果を2進数文字列に変換して比較
    return bin(result)[2:] == mask


if __name__ == "__main__":
    # テストケース
    target = "10000000"
    mask = "11000000"

    # 使用例
    result = evaluate_bitwise_or(target, mask)

    # 結果を確認
    print(result)  # 期待値: True
