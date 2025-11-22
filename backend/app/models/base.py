from datetime import datetime  # để làm việc với thời gian
from typing import Optional    # cho phép khai báo biến có thể là None
from bson import ObjectId      # kiểu ObjectId đặc biệt dùng trong MongoDB


class BaseModel:
    """Base model với các trường chung và phương thức cơ bản"""

    def __init__(self):
        # _id là trường lưu ID (ObjectId) của document trong MongoDB
        self._id: Optional[ObjectId] = None
        # created_at lưu thời điểm tạo object (theo chuẩn UTC hiện tại)
        self.created_at: datetime = datetime.utcnow()
        # updated_at lưu thời điểm cập nhật cuối cùng (mặc định lúc tạo cũng là thời điểm hiện tại)
        self.updated_at: datetime = datetime.utcnow()

    def to_dict(self) -> dict:
        """
        Chuyển đổi object thành dictionary
        để có thể lưu vào database hoặc serialize trả về client
        """
        data = {
            # chuyển _id thành chuỗi, nếu _id chưa có thì None
            'id': str(self._id) if self._id else None,
            # created_at chuyển thành chuỗi ISO8601, nếu không có thì None
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # tương tự với updated_at
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """
        Tạo một instance từ dict (ví dụ lấy dữ liệu từ database)
        - cls đại diện cho class được gọi (BaseModel hoặc class con kế thừa)
        """
        instance = cls()  # tạo instance mới
        # nếu dữ liệu dict có trường '_id', gán cho instance
        if '_id' in data:
            instance._id = data['_id']
        # nếu có created_at thì gán (ở đây chưa xử lý convert datetime, có thể cần bổ sung)
        if 'created_at' in data:
            instance.created_at = data['created_at']
        # tương tự với updated_at
        if 'updated_at' in data:
            instance.updated_at = data['updated_at']
        return instance

    def update_timestamp(self):
        """Cập nhật lại thời gian updated_at thành thời gian hiện tại"""
        self.updated_at = datetime.utcnow()


class Entity(BaseModel):
    """
    Lớp Entity base, mở rộng BaseModel
    Áp dụng pattern Entity: đối tượng có định danh (identity)
    """

    def __eq__(self, other) -> bool:
        """
        Định nghĩa phép so sánh bằng (==) giữa hai entity
        Hai entity cùng loại và có cùng _id thì được xem là bằng nhau
        """
        if not isinstance(other, self.__class__):
            return False  # khác loại thì không bằng
        return self._id == other._id  # cùng _id thì bằng

    def __hash__(self) -> int:
        """
        Định nghĩa hàm băm để Entity có thể dùng trong tập hợp set hoặc làm key dict
        Dựa trên _id làm căn cứ tính hash
        """
        return hash(self._id)
