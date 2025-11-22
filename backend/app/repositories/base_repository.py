from abc import ABC, abstractmethod
from typing import List, Generic, TypeVar, Optional
from bson import ObjectId
from pymongo.collection import Collection

# T là kiểu dữ liệu tổng quát (Generic Type)
# cho phép class này làm việc với bất kỳ kiểu đối tượng nào (User, Conversation,...)
T = TypeVar('T')


# ------------------------- LỚP TRỪU TƯỢNG (INTERFACE) -------------------------
class IRepository(ABC, Generic[T]):
    """
    Interface định nghĩa các hành vi chung cho mọi Repository
    """

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """
        Đây là phương thức trừu tượng, có nhiệm vụ tìm và trả về một đối tượng kiểu T theo id chuỗi.
        Nếu không tìm thấy, trả về None.
        """
        pass

    @abstractmethod
    def find_all(self, skip: int = 0, limit: int = 20) -> List[T]:
        """Phương thức trừu tượng: lấy tất cả đối tượng (có phân trang)."""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Phương thức trừu tượng: tạo mới một đối tượng trong DB."""
        pass

    @abstractmethod
    def update(self, id: str, entity: T) -> Optional[T]:
        """Phương thức trừu tượng: cập nhật đối tượng theo id."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Phương thức trừu tượng: xóa đối tượng theo id."""
        pass


# ------------------------- LỚP TRIỂN KHAI CỤ THỂ -------------------------
class BaseConversation(IRepository[T]):
    """
    Lớp BaseConversation triển khai (implement) các phương thức CRUD cơ bản
    dựa trên MongoDB Collection.
    """

    def __init__(self, collection: Collection, model_class):
        self.collection = collection  # Collection là bảng (table) trong MongoDB
        self.model_class = model_class  # model_class là lớp model tương ứng (VD: Conversation)

    # ------------------ TÌM THEO ID ------------------
    def find_by_id(self, id: str) -> Optional[T]:
        try:
            obj_id = ObjectId(id)  # chuyển chuỗi id thành ObjectId để MongoDB hiểu
            data = self.collection.find_one({'_id': obj_id})  # tìm document trong Mongo theo _id
            return self.model_class.from_dict(data) if data else None
            # from_dict là chuyển dữ liệu từ dict → Python object ( dùng để đọc dữ liệu từ MongoDB)
        except Exception as e:
            print(f"Lỗi tìm theo ID: {e}")
            return None

    # ------------------ LẤY TẤT CẢ DỮ LIỆU ------------------
    def find_all(self, skip: int = 0, limit: int = 20) -> List[T]:
        try:
            data_cursor = self.collection.find().skip(skip).limit(limit)
            # find() trả về Cursor chứa nhiều document
            # skip/limit dùng để phân trang
            return [self.model_class.from_dict(doc) for doc in data_cursor]
            # duyệt từng document và chuyển thành Python object
        except Exception as e:
            print(f"Lỗi find_all: {e}")
            return []

    # ------------------ TẠO MỚI ĐỐI TƯỢNG ------------------
    def create(self, entity: T) -> T:
        try:
            data = entity.to_dict()  # lấy entity chuyển thành dạng dict để sau đó lưu vào biến data
            data.pop('id', None)  # xoá trường id ở dữ liệu, tại vì MongoDB tự sinh _id
            result = self.collection.insert_one(data)  # Gọi hàm insert_one() của PyMongo để chèn document vào MongoDB
            entity._id = result.inserted_id  # gán _id MongoDB vừa tạo cho entity hiện tại
            return entity  # trả về lại entity (lúc này đã có _id)
        except Exception as e:#Nếu bất kỳ lỗi nào (Exception) xảy ra trong khối try,thì gán thông tin lỗi đó vào biến e và chạy đoạn code trong except.
            print(f"Lỗi tạo entity: {e}")
            raise

    def update(self, id: str, entity: T) -> Optional[T]:
        """Update existing entity"""
        try:
            object_id = ObjectId(id)
            # Chuyển id từ chuỗi (string) → ObjectId để MongoDB có thể hiểu và truy vấn
            # Vì trong MongoDB, _id là kiểu ObjectId chứ không phải string

            entity.update_timestamp()
            # Gọi hàm update_timestamp() để cập nhật lại thời gian sửa đổi (nếu model có thuộc tính này)
            # Ví dụ: updated_at = datetime.now()

            data = entity.to_dict()
            # Chuyển object entity (Python class) → dict (định dạng có thể lưu vào MongoDB)

            data.pop('id', None)
            # Xóa trường 'id' dạng string trong dict (vì MongoDB dùng _id riêng)
            # Nếu không xóa, nó có thể gây lỗi "cannot change _id of a document"

            result = self.collection.update_one(
                {'_id': object_id},  # Điều kiện: tìm document có _id trùng khớp
                {'$set': data}  # Lệnh MongoDB: cập nhật (set) các field trong document đó
            )
            # update_one() trả về một đối tượng chứa thông tin cập nhật
            # ví dụ: result.modified_count = số document đã được thay đổi

            if result.modified_count > 0:
                # Nếu có ít nhất 1 document bị ảnh hưởng (được cập nhật thành công)
                return entity  # Trả về đối tượng sau khi cập nhật
            return None
            # Ngược lại (không có document nào bị cập nhật) → trả về None

        except Exception as e:
            print(f"Error updating entity: {e}")
            # Nếu có bất kỳ lỗi nào trong quá trình (ví dụ id sai, kết nối Mongo lỗi, v.v.)
            # Thì in ra thông tin lỗi để dễ debug
            return None
            # Trả về None để báo hiệu cho tầng trên biết là update thất bại
    def delete(self, id: str) -> bool:
        """Delete entity"""
        try:
            object_id = ObjectId(id)
            # Chuyển id từ kiểu string → ObjectId (vì MongoDB lưu _id dạng ObjectId)
            # Nếu không chuyển, MongoDB sẽ không tìm thấy document cần xóa

            result = self.collection.delete_one({'_id': object_id})
            # Gọi hàm delete_one() để xóa 1 document trong collection có _id trùng khớp
            # MongoDB sẽ trả về một đối tượng chứa thông tin kết quả xóa

            return result.deleted_count > 0
            # Nếu deleted_count > 0 → tức là đã xóa thành công ít nhất 1 document
            # Trả về True (thành công), ngược lại False (không có gì bị xóa)

        except Exception as e:
            print(f"Error deleting entity: {e}")
            # Nếu có lỗi (ví dụ id không hợp lệ, không kết nối được DB, v.v.)
            # Thì in ra thông báo lỗi để dễ debug
            return False
            # Trả về False để báo hiệu thao tác xóa thất bại

    def find_by_query(self, query: dict, skip: int = 0, limit: int = 20) -> List[T]:
        """Find entities by custom query"""
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            # Gọi hàm find() của PyMongo với điều kiện lọc (query)
            # skip() và limit() dùng để phân trang — bỏ qua 'skip' document đầu, và chỉ lấy tối đa 'limit' document

            return [self.model_class.from_dict(doc) for doc in cursor]
            # Duyệt qua từng document trong cursor (dạng dict)
            # Mỗi document được chuyển về object Python thông qua from_dict()
            # Trả về danh sách (list) các object

        except Exception as e:
            print(f"Error finding by query: {e}")
            # Nếu có lỗi (ví dụ query sai cú pháp, DB lỗi, v.v.)
            # Thì in ra thông tin lỗi
            return []
            # Trả về list rỗng nếu có lỗi

    def count(self, query: Optional[dict] = None) -> int:
        """Count entities matching query"""
        try:
            return self.collection.count_documents(query or {})
            # Dùng hàm count_documents() của MongoDB để đếm số document thỏa mãn điều kiện (query)
            # Nếu query = None → mặc định đếm tất cả document trong collection
            # query or {} có nghĩa là: nếu query không có, thì dùng dict rỗng {}

        except Exception as e:
            print(f"Error counting: {e}")
            # Nếu có lỗi (ví dụ mất kết nối DB, query sai, v.v.)
            # Thì in ra lỗi để debug
            return 0
            # Trả về 0 (nghĩa là đếm thất bại)
