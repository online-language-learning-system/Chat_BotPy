"""
Conversation Controller
Chỉ quản lý luồng điều khiển (flow) và tương tác giữa các service, repository
Logic nghiệp vụ được tách ra service riêng biệt
"""
from typing import Optional
from datetime import datetime
from app.models.conversation import Conversation, Message, MessageAnalysis
from app.repositories.conversation_repository import ConversationRepository
from app.services.ai.base_ai_service import IAIService
from app.services.scoring_service import ScoringService
from app.services.recommendation_service import RecommendationService


class ConversationController:
    """
    Controller cho các thao tác liên quan đến Conversation.
    Dùng Dependency Injection nhận các repo và service,
    tập trung điều phối các bước xử lý, không xử lý logic nghiệp vụ.
    """

    def __init__(
            self,
            conversation_repo: ConversationRepository,
            
            ai_service: IAIService,
            scoring_service: ScoringService,
            recommendation_service: RecommendationService
    ):
        self.conversation_repo = conversation_repo
    
        self.ai_service = ai_service
        self.scoring_service = scoring_service
        self.recommendation_service = recommendation_service

    def create_conversation(
            self,
            user_id: str,
            topic: str,
            level: str
    ) -> Conversation:
        """
        Tạo mới một conversation

        Args:
            user_id: id người dùng
            topic: chủ đề hội thoại
            level: trình độ (N5-N1)

        Returns:
            Đối tượng Conversation mới tạo
        """
        # Tạo đối tượng Conversation mới
        conversation = Conversation(
            user_id=user_id,
            topic=topic,
            level=level
        )
        # Lưu vào repository (DB)
        return self.conversation_repo.create(conversation)

    def send_message(
            self,
            conversation_id: str,
            message_content: str,
            response_time: Optional[int] = None
    ) -> dict:
        """
        Nhận tin nhắn người dùng, xử lý phản hồi AI,
        cập nhật điểm số, lưu lại conversation

        Args:
            conversation_id: id conversation cần xử lý
            message_content: nội dung tin nhắn người dùng
            response_time: thời gian phản hồi (ms)

        Returns:
            Dict chứa user_message, ai_message và điểm tổng thể (overall_score)

        Raises:
            ValueError nếu không tìm thấy conversation
        """
        # Lấy conversation từ DB
        conversation = self.conversation_repo.find_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Gọi service để phân tích tin nhắn người dùng
        analysis_data = self.ai_service.analyze_message(
            message_content,
            conversation.level
        )
        analysis = MessageAnalysis(
            grammar=analysis_data['grammar'],
            vocabulary=analysis_data['vocabulary'],
            naturalness=analysis_data['naturalness'],
            response_time=response_time
        )

        # Tạo Message user
        user_message = Message(
            role='user',
            content=message_content,
            timestamp=datetime.utcnow(),
            analysis=analysis
        )

        # Thêm message user vào conversation
        conversation.add_message(user_message)

        # Lấy lịch sử chat dưới dạng list dict (role, content) cho AI service
        chat_history = conversation.get_chat_history()
        ai_response = self.ai_service.chat(
            chat_history,
            conversation.topic,
            conversation.level
        )

        # Tạo Message AI
        ai_message = Message(
            role='assistant',
            content=ai_response,
            timestamp=datetime.utcnow()
        )
        # Thêm message AI vào conversation
        conversation.add_message(ai_message)

        # Tính điểm tổng thể bằng scoring service
        new_score = self.scoring_service.calculate_overall_score(
            conversation.messages
        )
        # Cập nhật điểm tổng thể vào conversation
        conversation.update_score(new_score)

        # Lưu conversation đã cập nhật
        self.conversation_repo.update(conversation_id, conversation)

        # Trả dữ liệu cho API response
        return {
            'user_message': user_message.to_dict(),
            'ai_message': ai_message.to_dict(),
            'overall_score': new_score.to_dict()
        }

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Lấy conversation theo id
        """
        return self.conversation_repo.find_by_id(conversation_id)

    def get_user_conversations(
            self,
            user_id: str,
            skip: int = 0,
            limit: int = 20
    ) -> list[Conversation]:
        """
        Lấy danh sách conversation của một user, có phân trang
        """
        return self.conversation_repo.find_by_user_id(user_id, skip, limit)

    def get_recommendations(self, conversation_id: str) -> list[dict]:
        """
        Lấy danh sách đề xuất khóa học dựa trên conversation

        Args:
            conversation_id: id conversation

        Returns:
            List dict đề xuất kèm thông tin chi tiết khóa học
        """
        conversation = self.conversation_repo.find_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Lấy danh sách khóa học theo trình độ
        courses = self.course_repo.find_by_level(conversation.level)

        # Gọi recommendation service để tạo danh sách đề xuất
        recommendations = self.recommendation_service.generate_recommendations(
            conversation,
            courses
        )

        # Thêm đề xuất vào conversation và lưu
        conversation.add_recommendations(recommendations)
        self.conversation_repo.update(conversation_id, conversation)

        # Lấy chi tiết khóa học cho từng đề xuất
        detailed_recommendations = []
        for rec in recommendations:
            course = self.course_repo.find_by_id(rec.course_id)
            detailed_recommendations.append({
                **rec.to_dict(),
                'course': course.to_dict() if course else None
            })

        return detailed_recommendations

    def get_user_statistics(self, user_id: str) -> dict:
        """
        Lấy thống kê các cuộc hội thoại của người dùng

        Args:
            user_id: id người dùng

        Returns:
            Dict thống kê (tổng số conversation, điểm cuối cùng,...)
        """
        return self.conversation_repo.get_user_statistics(user_id)
