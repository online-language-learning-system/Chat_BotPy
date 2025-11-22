from __future__ import annotations  # Cho phép dùng kiểu annotation tham chiếu trong class
from typing import List, Optional, Dict, Any  # Kiểu dữ liệu chuẩn để gõ kiểu (type hint)
from pymongo.collection import Collection  # Lớp đại diện cho Collection trong MongoDB
from bson import ObjectId  # Định dạng ID chuẩn của MongoDB

from app.models.conversation import Conversation  # Model Conversation định nghĩa dữ liệu cuộc hội thoại
from .base_repository import BaseConversation  # Lớp repository base đã implement CRUD chung


class ConversationRepository(BaseConversation[Conversation]):
    def __init__(self, collection: Collection):
        # Gọi constructor của lớp cha BaseConversation với collection và model Conversation
        # collection ở đây chính là MongoDB collection để lưu trữ cuộc hội thoại
        super().__init__(collection, Conversation)

    def find_by_user_id(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Conversation]:
        # Hàm tìm tất cả các cuộc hội thoại của một user cụ thể, có phân trang
        query = {'user_id': user_id}  # Điều kiện lọc: chỉ lấy document có user_id tương ứng
        return self.find_by_query(query, skip, limit)
        # Gọi lại hàm tìm theo query của lớp cha BaseConversation

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        # Hàm lấy thống kê liên quan đến user, bao gồm:
        # - tổng số cuộc hội thoại user đã có
        # - điểm số cuối cùng của user trong cuộc hội thoại gần nhất

        total_conversations = self.count({'user_id': user_id})
        # Đếm tổng số cuộc hội thoại của user (dùng hàm đếm của BaseConversation)

        last_doc = self.collection.find({'user_id': user_id}).sort('updated_at', -1).limit(1)
        # Lấy document hội thoại cuối cùng của user dựa trên thời gian cập nhật (updated_at giảm dần)
        # limit(1) để chỉ lấy 1 document gần nhất

        last_score = None
        for d in last_doc:
            conv = Conversation.from_dict(d)
            # Chuyển dict lấy từ DB thành object Conversation
            last_score = conv.overall_score.to_dict() if conv and conv.overall_score else None
            # Lấy điểm tổng kết (overall_score) của cuộc hội thoại gần nhất nếu có

        return {
            'total_conversations': total_conversations,
            'last_overall_score': last_score,
        }
        # Trả về dict chứa tổng số cuộc hội thoại và điểm số cuối cùng
