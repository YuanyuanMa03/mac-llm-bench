"""D5 regression tests：`_pad_batch` / `default_loss` 的 padding 语义。

覆盖 research/deviations_public.md D5 修复的四个维度：
A. 变长 validation 各 batch size 不因 non-uniform length 崩溃；
B. padding mask 正确性——padded batch 的有效 token loss 与逐样本独立
   计算（token 加权）在数值容差内一致，且证明旧 [0,len] 语义确实泄漏
   pad target（测试有区分度，非空洞通过）；
C. b=1 语义回归——新 helper 的 [0,L-1] 与旧实现 [0,L] 在 default_loss
   下 mask/loss/tokens 逐位等价（已有全部 b1 formal run 不受影响）；
D. 样本数不能整除 batch size 时的尾批正确工作。

使用合成 token 序列 + tiny 前缀模型；仅验证软件行为，非 benchmark 数据。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import pytest
from mlx.utils import tree_flatten

SRC = Path(__file__).resolve().parents[1]
TRAIN_DIR = SRC / "src" / "train"
if str(TRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(TRAIN_DIR))

from lora_smoke import _forward_validation_loss, _pad_batch  # noqa: E402
from mlx_lm.tuner.trainer import default_loss  # noqa: E402

PAD_ID = 0  # 与 trainer 回退值一致；样本 token id 刻意避开 0

# 真实变长样本（len ∈ {7,3,11,5,2}；token id ≥ 2，vocab=37）
VAL_SAMPLES = [
    list(range(2, 9)),
    list(range(5, 8)),
    list(range(11, 22)),
    list(range(3, 8)),
    list(range(9, 11)),
]


class TinyLM(nn.Module):
    """最小 LM：embedding → linear logits（float32，固定 seed 确定性）。"""

    def __init__(self, vocab: int = 37, dim: int = 16):
        super().__init__()
        self.embed = nn.Embedding(vocab, dim)
        self.proj = nn.Linear(dim, vocab, bias=False)

    def __call__(self, inputs):
        return self.proj(self.embed(inputs))


@pytest.fixture(scope="module")
def model() -> TinyLM:
    mx.random.seed(0)
    m = TinyLM()
    mx.eval(m.parameters())
    return m


def _forward(model, chunk):
    batch_ids, lens = _pad_batch(chunk, PAD_ID)
    loss, toks = default_loss(model, mx.array(batch_ids), mx.array(lens))
    mx.eval(loss, toks)
    return float(loss), int(toks)


def _per_sample_reference(model, samples):
    """逐样本（无 pad 邻居、无 batch 化）的 token 加权 reference。"""
    total_loss, total_toks = 0.0, 0
    for s in samples:
        loss, toks = default_loss(
            model, mx.array([s]), mx.array([[0, len(s) - 1]]))
        mx.eval(loss, toks)
        total_loss += float(loss) * int(toks)
        total_toks += int(toks)
    return total_loss / total_toks, total_toks


# ---- A + D：变长样本（含尾批）各 batch size 正常前向 ----

@pytest.mark.parametrize("batch_size", [2, 4, 8])
def test_variable_length_batches_do_not_crash(model, batch_size):
    n = len(VAL_SAMPLES)  # 5：batch_size ∈ {2,4,8} 均产生非整除尾批
    total_toks = 0
    for i in range(0, n, batch_size):
        chunk = VAL_SAMPLES[i:i + batch_size]
        loss, toks = _forward(model, chunk)
        assert math.isfinite(loss)
        assert toks == sum(len(s) - 1 for s in chunk)
        total_toks += toks
    assert total_toks == sum(len(s) - 1 for s in VAL_SAMPLES)


def test_validation_is_forward_only_and_does_not_update_parameters(model):
    """validation 只调用 forward loss；模型参数在调用前后逐元素不变。"""
    chunk = VAL_SAMPLES[:4]
    batch_ids, lens = _pad_batch(chunk, PAD_ID)
    before = [mx.array(value) for _, value in tree_flatten(model.parameters())]
    loss, toks = _forward_validation_loss(
        model, mx.array(batch_ids), mx.array(lens))
    mx.eval(loss, toks)
    after = [value for _, value in tree_flatten(model.parameters())]
    assert math.isfinite(float(loss))
    assert int(toks) == sum(len(s) - 1 for s in chunk)
    assert all(mx.array_equal(left, right).item()
               for left, right in zip(before, after, strict=True))


# ---- B：padding mask 正确性 ----

@pytest.mark.parametrize("batch_size", [2, 4, 5])
def test_padded_batch_matches_per_sample_reference(model, batch_size):
    """padded batch 聚合 loss 与逐样本 reference 在容差内一致；
    tokens 口径严格相等（每样本恰 len-1 个真实 next-token target）。"""
    total_loss, total_toks = 0.0, 0
    for i in range(0, len(VAL_SAMPLES), batch_size):
        loss, toks = _forward(model, VAL_SAMPLES[i:i + batch_size])
        total_loss += loss * toks
        total_toks += toks
    ref_loss, ref_toks = _per_sample_reference(model, VAL_SAMPLES)
    assert total_toks == ref_toks
    assert total_loss / total_toks == pytest.approx(ref_loss, rel=1e-5,
                                                    abs=1e-6)


def test_old_length_semantics_leaks_pad_target(model):
    """B 的区分度证明：旧 [0,len] lengths 在 padded batch 下，每个非批内
    最长的样本比 reference 多计 1 个位置（target=pad token），loss 偏离
    reference——即 test_padded_batch_matches_per_sample_reference 对旧
    实现必失败（最长样本 targets 仅 L-1 列，无从多计，故 +1 仅限短行）。"""
    chunk = VAL_SAMPLES[:2]  # len 7（最长）与 len 3
    max_len = max(len(s) for s in chunk)
    old_batch = [s + [PAD_ID] * (max_len - len(s)) for s in chunk]
    old_lens = [[0, len(s)] for s in chunk]
    loss_old, toks_old = default_loss(
        model, mx.array(old_batch), mx.array(old_lens))
    mx.eval(loss_old, toks_old)
    ref_loss, ref_toks = _per_sample_reference(model, chunk)
    shorter = sum(1 for s in chunk if len(s) < max_len)
    assert int(toks_old) == ref_toks + shorter
    assert float(loss_old) != pytest.approx(ref_loss, rel=1e-4, abs=1e-4)


# 注：不构造"纯 pad 样本"测试——default_loss 的 mask 是位置区间
# [0, len(s)]，信任 len(s) 为样本真实长度；纯 pad 行不是数据集的真实
# 形态（样本 = 真实文本 tokenize）。"pad 位置零贡献"由
# test_padded_batch_matches_per_sample_reference 的 tokens 严格相等
# （每样本恰 len-1）直接覆盖。

# ---- C：b=1 语义回归（新 helper vs 旧实现逐位等价） ----

@pytest.mark.parametrize("sample", VAL_SAMPLES)
def test_batch1_new_lengths_equivalent_to_old(model, sample):
    """b=1：helper 产出 batch_ids 与旧 b1 分支字面相同；新 [0,L-1] 与旧
    [0,L] 的 mask/loss/tokens 完全一致。"""
    new_ids, new_lens = _pad_batch([sample], PAD_ID)
    assert new_ids == [sample]          # 无 pad 追加（旧 b1 分支 = [chunk[0]]）
    assert new_lens == [[0, len(sample) - 1]]

    loss_new, toks_new = default_loss(
        model, mx.array(new_ids), mx.array(new_lens))
    loss_old, toks_old = default_loss(
        model, mx.array([sample]), mx.array([[0, len(sample)]]))
    mx.eval(loss_new, toks_new, loss_old, toks_old)

    # mask 显式全等（default_loss 的 mask 公式逐位复刻）
    steps = mx.arange(1, len(sample))           # targets 仅 L-1 列
    mask_old = (steps >= 0) & (steps <= len(sample))
    mask_new = (steps >= 0) & (steps <= len(sample) - 1)
    assert mask_old.tolist() == mask_new.tolist()

    assert int(toks_new) == int(toks_old) == len(sample) - 1
    assert float(loss_new) == pytest.approx(float(loss_old), rel=1e-7,
                                            abs=1e-7)


# ---- helper 直接性质 ----

def test_pad_batch_shapes_and_values():
    chunk = [list(range(2, 5)), list(range(5, 7))]  # len 3 与 2
    batch_ids, lengths = _pad_batch(chunk, PAD_ID)
    assert batch_ids == [[2, 3, 4], [5, 6, PAD_ID]]
    assert lengths == [[0, 2], [0, 1]]
    # 等长 batch：无任何 pad 追加
    eq = [list(range(2, 4)), list(range(6, 8))]
    b2, l2 = _pad_batch(eq, PAD_ID)
    assert b2 == eq and l2 == [[0, 1], [0, 1]]
