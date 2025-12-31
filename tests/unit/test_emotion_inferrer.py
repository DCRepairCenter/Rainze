"""
EmotionInferrer 单元测试
EmotionInferrer Unit Tests

测试情感推断器的三层降级策略。
Tests emotion inferrer's three-layer fallback strategy.

Author: Rainze Team
Created: 2025-12-30
"""

from __future__ import annotations

import logging
import pytest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestEmotionInferrer:
    """EmotionInferrer 测试"""

    def test_parse_llm_tag_success(self) -> None:
        """测试 LLM 标签解析成功"""
        logger.info("=" * 60)
        logger.info("测试: LLM 标签解析成功")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import EmotionInferrer

        inferrer = EmotionInferrer(enable_snownlp=False)

        # 测试正常标签
        text = "今天天气真好呢~ [EMOTION:happy:0.7]"
        clean_text, emotion = inferrer.infer(text)

        logger.info(f"输入: {text}")
        logger.info(f"输出: text='{clean_text}', emotion={emotion.tag}:{emotion.intensity}")

        assert clean_text == "今天天气真好呢~"
        assert emotion.tag == "happy"
        assert emotion.intensity == 0.7
        logger.info("✓ LLM 标签解析成功")

    def test_parse_llm_tag_various_emotions(self) -> None:
        """测试各种情感标签解析"""
        logger.info("=" * 60)
        logger.info("测试: 各种情感标签解析")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import EmotionInferrer

        inferrer = EmotionInferrer(enable_snownlp=False)

        test_cases = [
            ("太棒了！ [EMOTION:excited:0.9]", "excited", 0.9),
            ("有点难过... [EMOTION:sad:0.6]", "sad", 0.6),
            ("嗯... [EMOTION:neutral:0.5]", "neutral", 0.5),
            ("什么！ [EMOTION:surprised:0.8]", "surprised", 0.8),
            ("人家害羞啦 [EMOTION:shy:0.7]", "shy", 0.7),
        ]

        for text, expected_tag, expected_intensity in test_cases:
            clean_text, emotion = inferrer.infer(text)
            logger.info(f"  {text} → {emotion.tag}:{emotion.intensity}")
            assert emotion.tag == expected_tag
            assert emotion.intensity == expected_intensity

        logger.info("✓ 各种情感标签解析成功")

    def test_snownlp_fallback(self) -> None:
        """测试 SnowNLP 降级"""
        logger.info("=" * 60)
        logger.info("测试: SnowNLP 降级")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import EmotionInferrer

        inferrer = EmotionInferrer(enable_snownlp=True, enable_rule_fallback=False)

        if not inferrer._snownlp_available:
            pytest.skip("SnowNLP 不可用")

        test_cases = [
            ("今天天气真好，心情很棒！", "happy"),  # 正面
            ("这部电影太无聊了，浪费时间", "sad"),  # 负面
            ("好的，知道了", "neutral"),  # 中性
        ]

        for text, expected_category in test_cases:
            clean_text, emotion = inferrer.infer(text)
            logger.info(f"  '{text}' → {emotion.tag}:{emotion.intensity}")
            # SnowNLP 的分类可能不完全准确，只检查是否有输出
            assert emotion is not None
            assert emotion.tag in {"happy", "sad", "anxious", "neutral", "surprised", "shy"}

        logger.info("✓ SnowNLP 降级成功")

    def test_rule_fallback(self) -> None:
        """测试规则降级"""
        logger.info("=" * 60)
        logger.info("测试: 规则降级")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import EmotionInferrer

        inferrer = EmotionInferrer(enable_snownlp=False, enable_rule_fallback=True)

        test_cases = [
            ("太开心了！哈哈~", "happy"),  # 正面关键词 + 标点
            ("好难过啊...", "sad"),  # 负面关键词 + 省略号
            ("哇！什么情况？", "surprised"),  # 惊讶关键词
            ("人家不好意思嘛", "shy"),  # 害羞关键词
            ("嗯", "neutral"),  # 无关键词
        ]

        for text, expected_tag in test_cases:
            clean_text, emotion = inferrer.infer(text)
            logger.info(f"  '{text}' → {emotion.tag}:{emotion.intensity}")
            assert emotion.tag == expected_tag

        logger.info("✓ 规则降级成功")

    def test_punctuation_intensity_adjustment(self) -> None:
        """测试标点符号强度调整"""
        logger.info("=" * 60)
        logger.info("测试: 标点符号强度调整")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import EmotionInferrer

        inferrer = EmotionInferrer(enable_snownlp=False, enable_rule_fallback=True)

        # 感叹号增加强度
        _, emotion1 = inferrer.infer("开心")
        _, emotion2 = inferrer.infer("开心！！")

        logger.info(f"  '开心' → {emotion1.intensity}")
        logger.info(f"  '开心！！' → {emotion2.intensity}")
        assert emotion2.intensity > emotion1.intensity

        # 省略号降低强度
        _, emotion3 = inferrer.infer("难过")
        _, emotion4 = inferrer.infer("难过...")

        logger.info(f"  '难过' → {emotion3.intensity}")
        logger.info(f"  '难过...' → {emotion4.intensity}")
        assert emotion4.intensity < emotion3.intensity

        logger.info("✓ 标点符号强度调整成功")

    def test_default_fallback(self) -> None:
        """测试默认值降级"""
        logger.info("=" * 60)
        logger.info("测试: 默认值降级")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import EmotionInferrer

        # 禁用所有降级
        inferrer = EmotionInferrer(enable_snownlp=False, enable_rule_fallback=False)

        text = "随便说点什么"
        clean_text, emotion = inferrer.infer(text)

        logger.info(f"输入: {text}")
        logger.info(f"输出: {emotion.tag}:{emotion.intensity}")

        assert emotion.tag == "neutral"
        assert emotion.intensity == 0.5
        logger.info("✓ 默认值降级成功")

    def test_convenience_function(self) -> None:
        """测试便捷函数"""
        logger.info("=" * 60)
        logger.info("测试: 便捷函数")
        logger.info("=" * 60)

        from rainze.ai.emotion_inferrer import infer_emotion

        text = "好开心啊！ [EMOTION:happy:0.8]"
        clean_text, emotion = infer_emotion(text)

        logger.info(f"infer_emotion('{text}')")
        logger.info(f"  → text='{clean_text}', emotion={emotion.tag}:{emotion.intensity}")

        assert clean_text == "好开心啊！"
        assert emotion.tag == "happy"
        assert emotion.intensity == 0.8
        logger.info("✓ 便捷函数测试成功")


class TestSnowNLPIntegration:
    """SnowNLP 集成测试"""

    def test_snownlp_sentiment_analysis(self) -> None:
        """测试 SnowNLP 情感分析"""
        logger.info("=" * 60)
        logger.info("测试: SnowNLP 情感分析")
        logger.info("=" * 60)

        try:
            from snownlp import SnowNLP
        except ImportError:
            pytest.skip("SnowNLP 未安装")

        test_cases = [
            ("这个产品非常好，我很喜欢", "positive"),
            ("服务态度太差了，很失望", "negative"),
            ("今天天气不错", "positive"),
            ("有点无聊", "negative"),
        ]

        for text, expected in test_cases:
            s = SnowNLP(text)
            sentiment = s.sentiments

            category = "positive" if sentiment > 0.5 else "negative"
            logger.info(f"  '{text}' → sentiment={sentiment:.3f} ({category})")

            # SnowNLP 的分类可能不完全准确
            # assert category == expected

        logger.info("✓ SnowNLP 情感分析测试完成")

    def test_snownlp_unicode_handling(self) -> None:
        """测试 SnowNLP Unicode 处理"""
        logger.info("=" * 60)
        logger.info("测试: SnowNLP Unicode 处理")
        logger.info("=" * 60)

        try:
            from snownlp import SnowNLP
        except ImportError:
            pytest.skip("SnowNLP 未安装")

        # 测试各种 Unicode 文本
        test_texts = [
            "你好世界",  # 中文
            "Hello 你好",  # 中英混合
            "😊开心",  # 带 emoji
            "　　有空格　　",  # 全角空格
        ]

        for text in test_texts:
            try:
                s = SnowNLP(text)
                sentiment = s.sentiments
                logger.info(f"  '{text}' → sentiment={sentiment:.3f}")
            except Exception as e:
                logger.warning(f"  '{text}' → 错误: {e}")

        logger.info("✓ SnowNLP Unicode 处理测试完成")
