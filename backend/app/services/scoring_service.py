from typing import List
from app.models.conversation import Message, Score
from app.config.settings import settings


class ScoringService:
    """Service dùng để tính toán điểm số từ các message trong conversation"""

    @staticmethod
    def calculate_overall_score(messages: List[Message]) -> Score:
        """
        Tính điểm tổng thể dựa trên tất cả các message có phân tích (analysis)

        Args:
            messages: Danh sách message, mỗi message có thể có phân tích điểm số

        Returns:
            Đối tượng Score chứa điểm từng phần và tổng điểm
        """
        # Lọc ra chỉ những message của user có phần phân tích
        user_messages = [
            msg for msg in messages
            if msg.role == 'user' and msg.analysis
        ]

        # Nếu không có message user nào có phân tích, trả về Score mặc định (0)
        if not user_messages:
            return Score()

        # Lấy điểm ngữ pháp từ các message của user
        # Lấy điểm (cố gắng parse thành số nếu AI trả về string)
        grammar_scores = [
            ScoringService._to_number(msg.analysis.grammar.get('score', 0))
            for msg in user_messages
        ]
        # Lấy điểm từ vựng từ các message
        vocabulary_scores = [
            ScoringService._to_number(msg.analysis.vocabulary.get('score', 0))
            for msg in user_messages
        ]
        # Lấy điểm tính tự nhiên (naturalness)
        naturalness_scores = [
            ScoringService._to_number(msg.analysis.naturalness.get('score', 0))
            for msg in user_messages
        ]

        # Tính điểm trung bình cho từng phần
        grammar_score = ScoringService._average(grammar_scores)
        vocabulary_score = ScoringService._average(vocabulary_scores)
        naturalness_score = ScoringService._average(naturalness_scores)
        # Tính điểm lưu loát dựa trên thời gian phản hồi
        fluency_score = ScoringService._calculate_fluency_score(user_messages)

        # Tính tổng điểm theo trọng số từng phần cấu hình trong settings
        total_score = (
                grammar_score * settings.GRAMMAR_WEIGHT +
                vocabulary_score * settings.VOCABULARY_WEIGHT +
                fluency_score * settings.FLUENCY_WEIGHT +
                naturalness_score * settings.NATURALNESS_WEIGHT
        )

        # Trả về đối tượng Score với các điểm đã làm tròn
        return Score(
            grammar=round(grammar_score),
            vocabulary=round(vocabulary_score),
            fluency=round(fluency_score),
            naturalness=round(naturalness_score),
            total=round(total_score)
        )

    @staticmethod
    def _calculate_fluency_score(messages: List[Message]) -> float:
        """
        Tính điểm lưu loát dựa trên thời gian phản hồi trung bình (response_time)

        Quy tắc chấm điểm:
        - Dưới 5 giây: 100 điểm
        - Dưới 10 giây: 90 điểm
        - Dưới 20 giây: 80 điểm
        - Dưới 30 giây: 70 điểm
        - Dưới 45 giây: 60 điểm
        - Từ 45 giây trở lên: 50 điểm
        """
        # Lấy danh sách thời gian phản hồi từ phân tích của các message
        response_times = [
            ScoringService._to_number(msg.analysis.response_time)
            for msg in messages
            if msg.analysis and msg.analysis.response_time is not None
        ]

        # Nếu không có dữ liệu thời gian phản hồi thì trả về điểm mặc định 70
        if not response_times:
            return 70.0

        # Tính thời gian phản hồi trung bình (ms -> s)
        avg_time_ms = sum(response_times) / len(response_times)
        avg_time_s = avg_time_ms / 1000

        # Xếp loại điểm theo thời gian trung bình
        if avg_time_s < 5:
            return 100.0
        elif avg_time_s < 10:
            return 90.0
        elif avg_time_s < 20:
            return 80.0
        elif avg_time_s < 30:
            return 70.0
        elif avg_time_s < 45:
            return 60.0
        else:
            return 50.0

    @staticmethod
    def _average(scores: List[float]) -> float:
        """Tính điểm trung bình của một danh sách điểm"""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _to_number(value, default: float = 0.0) -> float:
        """Chuyển một giá trị (có thể là str/int/float) về float an toàn.

        Nếu không thể chuyển đổi, trả về default.
        """
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def identify_weaknesses(score: Score, threshold: int = 70) -> List[str]:
        """
        Xác định các điểm yếu dựa trên điểm số từng phần

        Args:
            score: Đối tượng Score
            threshold: Ngưỡng dưới mức này coi là điểm yếu

        Returns:
            Danh sách tên các phần yếu (grammar, vocabulary, fluency, naturalness)
        """
        weaknesses = []

        if score.grammar < threshold:
            weaknesses.append('grammar')
        if score.vocabulary < threshold:
            weaknesses.append('vocabulary')
        if score.fluency < threshold:
            weaknesses.append('fluency')
        if score.naturalness < threshold:
            weaknesses.append('naturalness')

        return weaknesses
