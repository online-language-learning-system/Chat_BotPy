from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class IAIService(ABC):
    """
    Giao diện dịch vụ AI
    Các implementation khác nhau (ví dụ DeepSeek, OpenAI) sẽ kế thừa và triển khai giao diện này
    """

    @abstractmethod
    def chat(
            self,
            messages: List[Dict[str, str]],
            topic: str,
            level: str
    ) -> str:
        """
        Gửi tin nhắn chat và nhận phản hồi

        Args:
            messages: Danh sách các message, mỗi message là dict có 'role' và 'content'
            topic: Chủ đề hội thoại
            level: Mức độ JLPT (N5-N1)

        Returns:
            Chuỗi phản hồi từ AI
        """
        pass

    @abstractmethod
    def analyze_message(
            self,
            message: str,
            level: str
    ) -> Dict:
        """
        Phân tích một tin nhắn tiếng Nhật

        Args:
            message: Văn bản tiếng Nhật cần phân tích
            level: Mức JLPT dự kiến

        Returns:
            Dict chứa kết quả phân tích gồm điểm ngữ pháp, từ vựng, tự nhiên
        """
        pass

    @abstractmethod
    def build_system_prompt(self, topic: str, level: str) -> str:
        """
        Xây dựng prompt hệ thống cho hội thoại

        Args:
            topic: Chủ đề hội thoại
            level: Mức độ JLPT

        Returns:
            Chuỗi prompt cho hệ thống
        """
        pass


class BaseAIService(IAIService):
    """
    Base implementation với logic chung dùng lại được
    Tuân thủ mẫu thiết kế Template Method
    """

    # Hướng dẫn theo cấp độ JLPT, dùng để xây dựng prompt
    LEVEL_GUIDELINES = {
        'N5': 'câu cơ bản, thì hiện tại/quá khứ, từ vựng phổ biến (～です、～ます)',
        'N4': 'đoạn hội thoại đơn giản, thể te, các trợ từ cơ bản (～て、～から、～ので)',
        'N3': 'chủ đề hàng ngày, thể điều kiện, từ vựng trung cấp (～ば、～たら)',
        'N2': 'chủ đề trừu tượng, cơ bản kính ngữ, từ vựng trình độ tin tức (尊敬語、謙譲語)',
        'N1': 'thảo luận phức tạp, kính ngữ nâng cao, từ vựng học thuật'
    }

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def build_system_prompt(self, topic: str, level: str) -> str:
        """
        Xây dựng prompt hệ thống (Template Method)

        Args:
            topic: Chủ đề hội thoại
            level: Mức độ JLPT

        Returns:
            Chuỗi prompt hệ thống cho AI
        """
        guidelines = self.LEVEL_GUIDELINES.get(level, self.LEVEL_GUIDELINES['N5'])

        # Prompt hướng dẫn AI làm đối tác hội thoại cho người học tiếng Nhật
        return f"""Bạn là đối tác hội thoại dành cho người học tiếng Nhật.

【Cài đặt】
- Chủ đề: {topic}
- Mức độ: {level} ({guidelines})

【Vai trò】
- Hội thoại bằng tiếng Nhật tự nhiên phù hợp trình độ người học
- Nhẹ nhàng sửa lỗi ngữ pháp và từ vựng
- Giải thích đơn giản khi dạy biểu hiện mới
- Đặt câu hỏi để tiếp tục hội thoại

【Quy tắc】
- Sử dụng ngữ pháp và từ vựng cấp độ {level}
- Trả lời không quá dài (khoảng 2-3 câu)
- Sử dụng đúng hiragana, katakana, kanji
- Giọng điệu tự nhiên, thân thiện
- Tuyệt đối không sử dụng tiếng Anh"""

    def build_analysis_prompt(self, message: str, level: str) -> str:
        """
        Xây dựng prompt để phân tích tin nhắn

        Args:
            message: Tin nhắn tiếng Nhật cần phân tích
            level: Mức độ JLPT

        Returns:
            Prompt yêu cầu AI phân tích và trả về JSON theo cấu trúc định sẵn
        """
        return f"""Hãy phân tích câu tiếng Nhật sau với tư cách là người học cấp độ {level}:

「{message}」

Vui lòng trả về kết quả chỉ dưới dạng JSON theo định dạng sau:
{{
  "grammar": {{
    "score": "Điểm số từ 0-100",
    "errors": ["Danh sách lỗi ngữ pháp"],
    "corrections": ["Các cách sửa lỗi"]
  }},
  "vocabulary": {{
    "score": "Điểm số từ 0-100",
    "level": "Mức độ từ vựng (N5-N1)",
    "advanced_words": ["Các từ vựng nâng cao"],
    "suggestions": ["Các đề xuất từ vựng tốt hơn"]
  }},
  "naturalness": {{
    "score": "Điểm số từ 0-100",
    "feedback": "Phản hồi về mức độ tự nhiên"
  }}
}}"""

    def get_fallback_analysis(self) -> Dict:
        """
        Phân tích mặc định khi API phân tích bị lỗi hoặc không phản hồi

        Returns:
            Dict chứa điểm số và phản hồi mặc định
        """
        return {
            'grammar': {
                'score': 70,
                'errors': [],
                'corrections': []
            },
            'vocabulary': {
                'score': 70,
                'level': 'N4',
                'advanced_words': [],
                'suggestions': []
            },
            'naturalness': {
                'score': 70,
                'feedback': 'Đã xảy ra lỗi trong quá trình phân tích'
            }
        }
