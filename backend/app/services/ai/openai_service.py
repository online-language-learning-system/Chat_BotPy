from __future__ import annotations

import json
import requests
from typing import Dict, List
from .base_ai_service import BaseAIService


class OpenAIService(BaseAIService):
    """Triển khai dịch vụ AI sử dụng OpenAI API hoặc API tương thích ChatAnywhere"""

    def chat(self, messages: List[Dict[str, str]], topic: str, level: str) -> str:
        """Trả lời hội thoại dựa trên lịch sử trò chuyện"""
        try:
            # Kiểm tra API key và base_url có được thiết lập chưa
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY chưa được thiết lập")
            if not self.base_url:
                raise ValueError("OPENAI_BASE_URL chưa được thiết lập")

            # Tạo prompt hệ thống dựa trên topic và level
            system_prompt = self.build_system_prompt(topic, level)

            # Ghép prompt hệ thống vào đầu danh sách message để gửi cho API
            full_messages = [{"role": "system", "content": system_prompt}] + messages

            # Địa chỉ endpoint API chat completion
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            print(f"[OpenAI] Gọi API chat: {url}")

            # Gửi POST request đến API OpenAI
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",  # Header xác thực
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,  # Model AI đang sử dụng (ví dụ: gpt-4)
                    "messages": full_messages,  # Toàn bộ message chat history
                    "temperature": 0.7,  # Độ sáng tạo câu trả lời
                    "max_tokens": 500  # Giới hạn số token (đơn vị tính độ dài câu)
                },
                timeout=self.timeout  # Timeout request
            )

            # Log trạng thái trả về
            print(f"[OpenAI] Trạng thái phản hồi: {response.status_code}")

            # Nếu HTTP error, raise exception
            response.raise_for_status()

            # Parse dữ liệu JSON trả về
            data = response.json()

            # Kiểm tra cấu trúc response có hợp lệ không
            if "choices" not in data or len(data["choices"]) == 0:
                raise ValueError(f"Cấu trúc phản hồi không đúng: {data}")

            # Lấy nội dung câu trả lời từ AI
            content = data["choices"][0]["message"]["content"].strip()
            print(f"[OpenAI] Chat thành công, độ dài nội dung: {len(content)}")

            return content

        except requests.exceptions.RequestException as e:
            # Bắt lỗi khi gọi API bị lỗi (timeout, kết nối...)
            print(f"[OpenAI Error chat] Lỗi request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[OpenAI Error chat] Phản hồi lỗi: {e.response.text}")
            return "Xin lỗi, đã xảy ra lỗi khi tạo phản hồi. Vui lòng thử lại."
        except KeyError as e:
            # Lỗi thiếu trường trong dữ liệu phản hồi JSON
            print(f"[OpenAI Error chat] Thiếu khóa trong phản hồi: {e}")
            return "Xin lỗi, đã xảy ra lỗi khi xử lý phản hồi từ API."
        except Exception as e:
            # Bắt các lỗi bất thường khác
            print(f"[OpenAI Error chat] Lỗi không xác định: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return "Xin lỗi, đã xảy ra lỗi khi tạo phản hồi. Vui lòng thử lại."

    def analyze_message(self, message: str, level: str) -> Dict:
        """Phân tích câu tiếng Nhật (ngữ pháp, từ vựng, tự nhiên)"""
        try:
            # Kiểm tra API key và base_url
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY chưa được thiết lập")
            if not self.base_url:
                raise ValueError("OPENAI_BASE_URL chưa được thiết lập")

            # Tạo prompt yêu cầu AI phân tích câu
            prompt = self.build_analysis_prompt(message, level)

            # Endpoint API chat completions
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            print(f"[OpenAI] Gọi API phân tích: {url}")

            # Gửi POST request để phân tích tin nhắn
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        # Dòng system hướng dẫn AI chuyên gia tiếng Nhật, trả về đúng JSON
                        {"role": "system", "content": "Bạn là chuyên gia tiếng Nhật. Vui lòng trả lời chỉ bằng JSON."},
                        # Dòng user gửi prompt phân tích câu
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Thấp để kết quả ổn định hơn
                    "max_tokens": 500
                },
                timeout=self.timeout
            )

            # Log trạng thái response
            print(f"[OpenAI] Phản hồi phân tích status: {response.status_code}")

            # Raise lỗi nếu HTTP error
            response.raise_for_status()

            # Parse JSON data
            data = response.json()

            # Kiểm tra cấu trúc phản hồi hợp lệ
            if "choices" not in data or len(data["choices"]) == 0:
                raise ValueError(f"Cấu trúc phản hồi không đúng: {data}")

            content = data["choices"][0]["message"]["content"].strip()
            print(f"[OpenAI] Nội dung phản hồi phân tích: {content[:200]}...")

            # Xử lý trường hợp AI trả về JSON trong code block markdown
            content_clean = content
            if "```json" in content:
                content_clean = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content_clean = content.split("```")[1].split("```")[0].strip()

            # Chuyển JSON string thành dict Python
            analysis = json.loads(content_clean)
            print(f"[OpenAI] Phân tích thành công: grammar score = {analysis.get('grammar', {}).get('score', 'N/A')}")

            # Trả về dict phân tích với mặc định nếu thiếu trường nào
            return {
                'grammar': analysis.get('grammar', {
                    'score': 70,
                    'errors': [],
                    'corrections': []
                }),
                'vocabulary': analysis.get('vocabulary', {
                    'score': 70,
                    'level': level,
                    'advanced_words': [],
                    'suggestions': []
                }),
                'naturalness': analysis.get('naturalness', {
                    'score': 70,
                    'feedback': 'Phân tích hoàn tất'
                })
            }

        except json.JSONDecodeError as e:
            # Lỗi khi JSON trả về không hợp lệ
            print(f"[OpenAI Error analyze_message] Lỗi decode JSON: {e}")
            print(f"[OpenAI Error analyze_message] Nội dung lỗi: {content[:500]}")
            return self.get_fallback_analysis()
        except requests.exceptions.RequestException as e:
            # Lỗi khi gọi API thất bại
            print(f"[OpenAI Error analyze_message] Lỗi request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[OpenAI Error analyze_message] Phản hồi lỗi: {e.response.text}")
            return self.get_fallback_analysis()
        except KeyError as e:
            # Thiếu key trong response JSON
            print(f"[OpenAI Error analyze_message] Thiếu khóa trong phản hồi: {e}")
            return self.get_fallback_analysis()
        except Exception as e:
            # Lỗi không xác định khác
            print(f"[OpenAI Error analyze_message] Lỗi không xác định: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return self.get_fallback_analysis()
