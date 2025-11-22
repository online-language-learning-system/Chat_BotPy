"""
Nhà máy AI Service
Chọn nhà cung cấp AI cụ thể dựa trên cấu hình settings.
"""
from __future__ import annotations

from typing import Optional

from app.config.settings import settings
from .base_ai_service import BaseAIService, IAIService


class _MockAIService(BaseAIService):
    # Service giả lập cho mục đích test hoặc khi provider thật không hoạt động
    def chat(self, messages, topic, level) -> str:
        # Trả lời giả đơn giản về chủ đề
        return f"Bạn nghĩ gì về chủ đề {topic}?"

    def analyze_message(self, message, level):
        # Phân tích tin nhắn đơn giản, cố định để khởi tạo
        return {
            'grammar': {'score': 75, 'errors': [], 'corrections': []},
            'vocabulary': {'score': 72, 'level': level, 'advanced_words': [], 'suggestions': []},
            'naturalness': {'score': 74, 'feedback': 'Cảm giác tốt'},
        }


def create_service() -> IAIService:
    # Kiểm tra cấu hình AI_PROVIDER đã được đặt chưa
    if not getattr(settings, 'AI_PROVIDER', None):
        raise ValueError('AI_PROVIDER chưa được thiết lập. Vui lòng cấu hình trong .env')
    provider = settings.AI_PROVIDER.lower()  # Lấy tên provider và chuyển thành chữ thường

    # Trường hợp chọn MyAI làm provider
    if provider == 'myai':
        try:
            from .myai_service import MyAIService
            if not settings.MYAI_API_KEY:
                raise ValueError('MYAI_API_KEY là bắt buộc khi AI_PROVIDER=myai')
            return MyAIService(
                api_key=settings.MYAI_API_KEY,
                base_url=settings.MYAI_BASE_URL or 'https://api.myai.com/v1',
                model=getattr(settings, 'MYAI_MODEL', 'chat'),
                timeout=settings.REQUEST_TIMEOUT,
            )
        except Exception as e:
            print(f"[AI Factory Error] Tạo MyAIService thất bại: {e}")
            # Dùng service giả lập nếu thất bại
            return _MockAIService(api_key='', base_url='', model='mock')

    # Trường hợp chọn OpenAI làm provider
    elif provider == 'openai':
        try:
            from .openai_service import OpenAIService
            if not settings.OPENAI_API_KEY:
                raise ValueError('OPENAI_API_KEY là bắt buộc khi AI_PROVIDER=openai')

            # In thông tin cấu hình để debug
            print(f"[AI Factory] Tạo OpenAIService với:")
            print(f"  - Địa chỉ Base URL: {settings.OPENAI_BASE_URL or 'https://api.openai.com/v1'}")
            print(f"  - Model: {settings.OPENAI_MODEL or 'gpt-4'}")
            print(f"  - API Key: {'*' * 10 if settings.OPENAI_API_KEY else 'CHƯA ĐẶT'}")

            service = OpenAIService(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL or 'https://api.openai.com/v1',
                model=settings.OPENAI_MODEL or 'gpt-4',
                timeout=settings.REQUEST_TIMEOUT,
            )
            print("[AI Factory] Tạo OpenAIService thành công")
            return service
        except Exception as e:
            print(f"[AI Factory Error] Tạo OpenAIService thất bại: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            print("[AI Factory] Chuyển sang dùng MockAIService")
            return _MockAIService(api_key='', base_url='', model='mock')

    else:
        # Nếu provider không nhận diện được, sử dụng service giả lập
        print(f"[AI Factory Warning] Nhà cung cấp '{provider}' không xác định, sử dụng service giả lập")
        return _MockAIService(api_key='', base_url='', model='mock')
