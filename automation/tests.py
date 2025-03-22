# 同じディレクトリにあるevaluate_bitwise_or.pyから関数をインポート
from evaluate_bitwise_or import evaluate_bitwise_or

# テストケース
target = "10000000"
mask = "11000000"

# 使用例
result = evaluate_bitwise_or(target, mask)

# 結果を確認
print(result)  # 期待値: True

