from __future__ import annotations  # Cho phép annotation kiểu trả về là class đang định nghĩa (forward references)

from dataclasses import dataclass  # Dùng để tạo class dạng data container tự sinh __init__, __repr__...
from datetime import datetime  # Xử lý thời gian
from typing import List, Optional, Dict, Any  # Định kiểu cho biến, hàm
from bson import ObjectId  # Lớp ObjectId đặc biệt dùng cho ID trong MongoDB

from .base import BaseModel, Entity  # Import lớp cơ sở (Entity có thể chứa các thuộc tính như _id, created_at,...)


@dataclass
class MessageAnalysis:
    # Lớp này lưu trữ kết quả phân tích chi tiết cho một tin nhắn (như điểm ngữ pháp, từ vựng, tự nhiên...)
    grammar: Dict[str, Any]  # Dữ liệu phân tích về ngữ pháp, kiểu dict vì có thể có nhiều chỉ số khác nhau
    vocabulary: Dict[str, Any]  # Phân tích về từ vựng
    naturalness: Dict[str, Any]  # Độ tự nhiên khi nói
    response_time: Optional[int] = None  # Thời gian phản hồi tính bằng giây, có thể không có (None)

    def to_dict(self) -> dict:
        # Chuyển đổi đối tượng thành dict để lưu database hoặc trả về API
        return {
            'grammar': self.grammar,
            'vocabulary': self.vocabulary,
            'naturalness': self.naturalness,
            'response_time': self.response_time,
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> Optional[MessageAnalysis]:
        # Tạo đối tượng MessageAnalysis từ dict (ví dụ khi đọc dữ liệu từ database)
        if not data:
            # Nếu data là None hoặc rỗng thì trả về None luôn
            return None
        return MessageAnalysis(
            grammar=data.get('grammar', {}),  # Lấy trường 'grammar' hoặc dict rỗng nếu không có
            vocabulary=data.get('vocabulary', {}),  # Tương tự với 'vocabulary'
            naturalness=data.get('naturalness', {}),  # Và 'naturalness'
            response_time=data.get('response_time'),  # Lấy response_time, có thể None
        )


@dataclass
class Score:
    # Lớp lưu điểm tổng quan từng mảng về kỹ năng của người học
    grammar: int = 0  # Điểm ngữ pháp (mặc định 0)
    vocabulary: int = 0  # Điểm từ vựng
    fluency: int = 0  # Điểm lưu loát
    naturalness: int = 0  # Điểm tự nhiên
    total: int = 0  # Tổng điểm (có thể là tổng các điểm trên hoặc tính khác)

    def to_dict(self) -> dict:
        # Chuyển đổi thành dict để lưu hoặc trả về API
        return {
            'grammar': self.grammar,
            'vocabulary': self.vocabulary,
            'fluency': self.fluency,
            'naturalness': self.naturalness,
            'total': self.total,
        }

    @staticmethod
    def from_dict(data: Optional[dict]) -> Score:
        # Tạo đối tượng Score từ dict (như khi đọc từ DB)
        if not data:
            # Nếu không có dữ liệu, trả về điểm mặc định (0 tất cả)
            return Score()
        return Score(
            grammar=int(data.get('grammar', 0) or 0),  # Lấy điểm grammar, ép kiểu int, nếu None hoặc False thì thành 0
            vocabulary=int(data.get('vocabulary', 0) or 0),
            fluency=int(data.get('fluency', 0) or 0),
            naturalness=int(data.get('naturalness', 0) or 0),
            total=int(data.get('total', 0) or 0),
        )


@dataclass
class Recommendation:
    # Lớp lưu trữ đề xuất khóa học dựa trên kết quả hoặc lịch sử học tập
    type: str  # Loại đề xuất (ví dụ: 'course', 'practice', ...)
    course_id: str  # ID khóa học được đề xuất
    reason: str  # Lý do đề xuất (ví dụ: 'Bạn cần cải thiện ngữ pháp')

    def to_dict(self) -> dict:
        # Chuyển đối tượng thành dict
        return {
            'type': self.type,
            'course_id': self.course_id,
            'reason': self.reason,
        }

    @staticmethod
    def from_dict(data: dict) -> Recommendation:
        # Tạo đối tượng Recommendation từ dict
        return Recommendation(
            type=data.get('type', ''),
            course_id=str(data.get('course_id', '')),  # Ép course_id thành chuỗi nếu không phải
            reason=data.get('reason', ''),
        )


class Message(Entity):
    # Lớp đại diện cho một tin nhắn trong cuộc trò chuyện (có vai trò user/assistant, nội dung,...)
    def __init__(
        self,
        role: str,  # Ai gửi tin nhắn (ví dụ: 'user' hoặc 'assistant')
        content: str,  # Nội dung tin nhắn
        timestamp: Optional[datetime] = None,  # Thời gian gửi, nếu không cung cấp thì lấy thời gian hiện tại
        analysis: Optional[MessageAnalysis] = None,  # Phân tích tin nhắn (có thể None)
    ):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp: datetime = timestamp or datetime.utcnow()  # Gán thời gian hiện tại nếu không có timestamp
        self.analysis = analysis

    def to_dict(self) -> dict:
        # Chuyển thành dict để lưu hoặc truyền đi
        # timestamp được convert thành chuỗi ISO để dễ lưu trữ và đọc
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'analysis': self.analysis.to_dict() if self.analysis else None,
        }

    @staticmethod
    def from_dict(data: dict) -> Message:
        # Tạo đối tượng Message từ dict (ví dụ khi lấy dữ liệu từ DB)
        timestamp_value = data.get('timestamp')
        if isinstance(timestamp_value, str):
            # Nếu timestamp là chuỗi, cố parse thành datetime
            try:
                parsed_ts = datetime.fromisoformat(timestamp_value)
            except ValueError:
                # Nếu parse lỗi thì lấy thời gian hiện tại thay thế
                parsed_ts = datetime.utcnow()
        elif isinstance(timestamp_value, datetime):
            # Nếu timestamp đã là datetime thì dùng luôn
            parsed_ts = timestamp_value
        else:
            # Nếu không có hoặc kiểu khác, lấy thời gian hiện tại
            parsed_ts = datetime.utcnow()

        return Message(
            role=data.get('role', ''),  # Lấy role hoặc chuỗi rỗng nếu không có
            content=data.get('content', ''),  # Lấy nội dung tin nhắn hoặc chuỗi rỗng
            timestamp=parsed_ts,
            analysis=MessageAnalysis.from_dict(data.get('analysis')),  # Phân tích tin nhắn (có thể None)
        )


class Conversation(Entity):
    # Lớp chính lưu trữ toàn bộ cuộc hội thoại của người dùng
    def __init__(
        self,
        user_id: str,  # ID người dùng
        topic: str,  # Chủ đề của cuộc hội thoại
        level: str,  # Cấp độ trình độ (ví dụ: N5, N4...)
        messages: Optional[List[Message]] = None,  # Danh sách tin nhắn (có thể trống)
        overall_score: Optional[Score] = None,  # Điểm tổng thể cho cuộc hội thoại
        recommendations: Optional[List[Recommendation]] = None,  # Danh sách đề xuất liên quan
    ):
        super().__init__()
        self.user_id = user_id
        self.topic = topic
        self.level = level
        self.messages: List[Message] = messages or []  # Nếu không có messages thì khởi tạo danh sách rỗng
        self.overall_score: Score = overall_score or Score()  # Nếu không có điểm thì tạo Score mặc định (0)
        self.recommendations: List[Recommendation] = recommendations or []  # Nếu không có thì danh sách rỗng

    def add_message(self, message: Message) -> None:
        # Thêm tin nhắn mới vào cuộc hội thoại
        self.messages.append(message)
        # Cập nhật thời gian cập nhật cuối (có thể để tracking sửa đổi)
        self.update_timestamp()

    def get_chat_history(self) -> List[Dict[str, str]]:
        # Trả về lịch sử trò chuyện dưới dạng list dict với mỗi dict có role + content (dùng cho frontend hoặc AI)
        return [{'role': m.role, 'content': m.content} for m in self.messages]

    def update_score(self, score: Score) -> None:
        # Cập nhật điểm tổng thể cho cuộc hội thoại và update timestamp
        self.overall_score = score
        self.update_timestamp()

    def add_recommendations(self, recs: List[Recommendation]) -> None:
        # Thêm các đề xuất mới vào danh sách hiện tại
        self.recommendations.extend(recs)
        self.update_timestamp()

    def to_dict(self) -> dict:
        # Chuyển Conversation thành dict để lưu hoặc trả về API
        base = super().to_dict()  # Lấy dict có sẵn từ lớp cha Entity (có thể bao gồm id, created_at, updated_at)
        base.update({
            'user_id': self.user_id,
            'topic': self.topic,
            'level': self.level,
            # Chuyển từng tin nhắn thành dict
            'messages': [m.to_dict() for m in self.messages],
            # Chuyển điểm tổng thể thành dict, hoặc None nếu không có
            'overall_score': self.overall_score.to_dict() if self.overall_score else None,
            # Chuyển danh sách đề xuất thành list dict
            'recommendations': [r.to_dict() for r in self.recommendations],
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> Conversation:
        # Tạo Conversation từ dict (ví dụ lấy dữ liệu từ database)
        instance = cls(
            user_id=data.get('user_id', ''),
            topic=data.get('topic', ''),
            level=data.get('level', ''),
            # Tạo list Message từ dict
            messages=[Message.from_dict(d) for d in data.get('messages', [])],
            # Tạo Score từ dict
            overall_score=Score.from_dict(data.get('overall_score')),
            # Tạo list Recommendation từ dict
            recommendations=[Recommendation.from_dict(d) for d in data.get('recommendations', [])],
        )
        # Xử lý trường _id (ObjectId của MongoDB)
        if data.get('_id'):
            # Nếu _id đã là ObjectId thì giữ nguyên, nếu là chuỗi thì chuyển sang ObjectId
            instance._id = data['_id'] if isinstance(data['_id'], ObjectId) else ObjectId(str(data['_id']))
        # Cập nhật thời gian tạo nếu có và đúng kiểu datetime
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            instance.created_at = data['created_at']
        # Cập nhật thời gian sửa đổi nếu có
        if 'updated_at' in data and isinstance(data['updated_at'], datetime):
            instance.updated_at = data['updated_at']
        return instance
