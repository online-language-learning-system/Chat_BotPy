from __future__ import annotations

from typing import List

from app.models.conversation import Conversation, Recommendation


class RecommendationService:
    def generate_recommendations(self, conversation: Conversation, courses: List) -> List[Recommendation]:
        """
        Sinh danh sách đề xuất khóa học dựa trên điểm yếu trong cuộc hội thoại

        Args:
            conversation: Đối tượng Conversation chứa điểm số tổng thể
            courses: Danh sách các khóa học có thể đề xuất

        Returns:
            Danh sách Recommendation tương ứng
        """
        recs: List[Recommendation] = []  # Danh sách lưu các đề xuất sẽ trả về
        score = conversation.overall_score  # Lấy điểm tổng thể conversation

        # Bảng ánh xạ từ điểm yếu sang category của khóa học
        weakness_to_category = {
            'grammar': 'grammar',       # Ngữ pháp
            'vocabulary': 'vocabulary', # Từ vựng
            'fluency': 'fluency',       # Lưu loát
            'naturalness': 'conversation', # Tính tự nhiên khi giao tiếp
        }

        # Xác định các điểm yếu dựa trên ngưỡng 70 điểm
        weaknesses = []
        if score.grammar < 70:
            weaknesses.append('grammar')       # Ngữ pháp yếu
        if score.vocabulary < 70:
            weaknesses.append('vocabulary')    # Từ vựng yếu
        if score.fluency < 70:
            weaknesses.append('fluency')       # Lưu loát kém
        if score.naturalness < 70:
            weaknesses.append('naturalness')   # Tự nhiên khi nói kém

        # Dựa trên các điểm yếu, tìm khóa học phù hợp thuộc category tương ứng
        for area in weaknesses:
            cat = weakness_to_category.get(area)
            for c in courses:
                c_dict = c.to_dict()
                # Nếu khóa học cùng category với điểm yếu thì đề xuất
                if c_dict.get('category') == cat:
                    recs.append(Recommendation(
                        type=area,                  # Loại đề xuất theo điểm yếu
                        course_id=c_dict.get('id') or '',  # ID khóa học
                        reason=f"{area} を強化しましょう"  # Lý do đề xuất (bằng tiếng Nhật)
                    ))

        # Nếu không có đề xuất nào do không tìm được khóa học phù hợp
        # Thì fallback: đề xuất bất kỳ 3 khóa học đầu ở cấp độ hiện tại
        if not recs:
            for c in courses[:3]:
                c_dict = c.to_dict()
                recs.append(Recommendation(
                    type='general',                # Loại chung chung
                    course_id=c_dict.get('id') or '',
                    reason='学習を続けましょう'  # Lý do: "Hãy tiếp tục học tập"
                ))

        # Trả về danh sách đề xuất
        return recs
