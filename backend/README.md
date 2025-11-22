# **Japanese Chat AI – Python Backend**

**backend** (phía máy chủ) của ứng dụng học hội thoại tiếng Nhật.
Hệ thống được xây dựng bằng **Python**, **Flask** và **MongoDB**, áp dụng các nguyên tắc **SOLID** và kiến trúc **MVC phân lớp (Model–View–Controller)**.
Mã nguồn hướng đến khả năng kiểm thử (testability), dễ bảo trì (maintainability) và dễ mở rộng (extensibility) — ví dụ có thể thêm nhà cung cấp AI mới thông qua mẫu thiết kế Factory và Interface.

---

## **1) Tổng quan kiến trúc**

Hệ thống tuân theo mô hình **kiến trúc phân lớp (Layered Architecture)** với các tầng tách biệt rõ ràng:

* **Tầng trình bày (Presentation Layer):** định nghĩa các endpoint HTTP (Flask Blueprints).
* **Tầng ứng dụng (Application Layer):** các Controller điều phối luồng xử lý nghiệp vụ.
* **Tầng nghiệp vụ (Business Logic Layer):** các Service như AI, chấm điểm, gợi ý khóa học.
* **Tầng truy cập dữ liệu (Data Access Layer):** Repository đóng gói truy vấn đến MongoDB.
* **Tầng miền nghiệp vụ (Domain Layer):** mô hình dữ liệu (Entity/Aggregate) như Conversation, Message, Topic, Course.

**Các mẫu thiết kế (Design Patterns) sử dụng:**

* **Factory Pattern:** chọn nhà cung cấp AI tương ứng.
* **Repository Pattern:** đóng gói logic truy cập dữ liệu và ánh xạ (mapping).
* **Template Method Pattern:** `BaseAIService` cung cấp logic chung, các lớp con ghi đè (override) các bước cụ thể.
* **Dependency Injection (DI):** Controller nhận phụ thuộc qua hàm khởi tạo.
* **Singleton:** đối tượng cấu hình (settings) được khởi tạo một lần và tái sử dụng.

---

## **1.1) Mô tả chi tiết kiến trúc theo thư mục**

### **`app/services/ai/`**

Mục đích: chứa toàn bộ logic tương tác với các nhà cung cấp AI, tách biệt khỏi Controller và Route.

**Thành phần:**

* **`base_ai_service.py`**

  * `IAIService`: giao diện (interface) định nghĩa các phương thức `chat(messages, topic, level)` và `analyze_message(message, level)`.
  * `BaseAIService`: lớp cơ sở (template) chứa logic chung như `build_system_prompt`, `build_analysis_prompt`, và `get_fallback_analysis`.
  * Khi thêm nhà cung cấp AI mới, kế thừa `BaseAIService` và ghi đè các hàm `chat`/`analyze_message`.
  * Lưu ý: xử lý timeout; không ghi log chứa API key; chuẩn hóa (normalize) kết quả trả về về cùng định dạng.

* **`ai_factory.py`**

  * Đọc biến môi trường `AI_PROVIDER` từ `settings` và trả về đối tượng AI tương ứng (`MyAIService`, `DeepSeekService`, `OpenAIService`).
  * Khi mở rộng, chỉ cần thêm import và một nhánh `if` mới; không cần chỉnh sửa Controller.
  * Lưu ý: phải kiểm tra biến môi trường cần thiết; dừng sớm (fail fast) nếu thiếu cấu hình.

* **`myai_service.py`, `deepseek_service.py`, `openai_service.py`**

  * Hiện là bản mẫu (stub), trả về dữ liệu giả định (mock data).
  * Cần tích hợp gọi HTTP thật, xác thực (authentication), xử lý lỗi (429, 5xx), ánh xạ dữ liệu đầu ra về định dạng thống nhất (`grammar`, `vocabulary`, `naturalness`).
  * Lưu ý: kiểm soát định dạng JSON chặt chẽ, tránh lỗi "ảo giác" (hallucination) của mô hình AI, giới hạn tần suất gọi API (rate limiting).

---

### **`app/controllers/`**

Mục đích: tầng ứng dụng (Application Layer).
Controller điều phối các repository và service để xử lý yêu cầu nghiệp vụ, không truy cập HTTP hoặc cơ sở dữ liệu trực tiếp.

**Ví dụ:**

* `conversation_controller.py`: tạo hội thoại, xử lý gửi tin nhắn, phân tích, chấm điểm, lưu trữ và gợi ý.
* `topic_controller.py`, `course_controller.py`: lấy danh sách chủ đề, khóa học.

Lưu ý:

* Giữ Controller đơn giản; đẩy logic nghiệp vụ phức tạp xuống tầng Service.
* Không chứa logic phụ thuộc vào nhà cung cấp AI.

---

### **`app/repositories/`**

Mục đích: tầng truy cập dữ liệu (Data Access Layer), ẩn chi tiết MongoDB.

* **`base_repository.py`**

  * `IRepository[T]`: giao diện CRUD hẹp.
  * `BaseRepository[T]`: cài đặt CRUD chung, hỗ trợ phân trang và xử lý `ObjectId`.
  * Lưu ý: loại bỏ trường `id` chuỗi trước khi thêm/cập nhật; cẩn thận khi chuyển đổi `ObjectId`.

* **Các repository cụ thể:**

  * `conversation_repository.py`: truy vấn hội thoại theo người dùng, thống kê.
  * `topic_repository.py`, `course_repository.py`: lọc theo cấp độ, danh mục, từ khóa.

---

### **`app/routes/`**

Mục đích: tầng trình bày (Presentation Layer).
Các Blueprint định nghĩa API endpoint, xác thực dữ liệu bằng Marshmallow, tài liệu hóa bằng Swagger.

Lưu ý: giữ route mỏng, không chứa logic nghiệp vụ; ủy quyền cho Controller.

---

### **`app/models/`**

Mục đích: định nghĩa thực thể miền nghiệp vụ (Domain Entities) như `Conversation`, `Message`, `Score`, `Recommendation`.

Lưu ý: khi thay đổi schema, cần đồng bộ với Repository và Schema.

---

### **`app/schemas/`**

Mục đích: xác thực (validate) và tuần tự hóa (serialize) dữ liệu request/response bằng **Marshmallow**.

---

### **`app/services/analysis/`**

Mục đích: tách riêng logic phân tích ngôn ngữ (ví dụ grammar, vocabulary, fluency).
Dự phòng cho việc mở rộng hoặc thay thế logic AI.

---

### **`scripts/` và `migrations/`**

* `scripts/seed_data.py`: chèn dữ liệu chủ đề/khóa học mẫu.
* `migrations/`: dự phòng cho công cụ di trú dữ liệu (migration).

---

### **`tests/`**

Cấu trúc sẵn để viết unit test (kiểm thử đơn vị) và integration test (kiểm thử tích hợp).
Khuyến nghị sử dụng pytest.

---

## **2) Cấu trúc thư mục tổng thể**
# File Tree: Chat_BotPy - Copy

**Generated:** 11/11/2025, 2:22:12 PM
**Root Path:** `d:\Chat_BotPy - Copy`

```
└── backend
    ├── app
    │   ├── config
    │   │   ├── __init__.py
    │   │   └── settings.py
    │   ├── controllers
    │   │   ├── __init__.py
    │   │   └── conversation_controller.py
    │   ├── models
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   └── conversation.py
    │   ├── repositories
    │   │   ├── __init__.py
    │   │   ├── base_repository.py
    │   │   └── conversation_repository.py
    │   ├── routes
    │   │   ├── __init__.py
    │   │   └── conversation_routes.py
    │   ├── schemas
    │   │   ├── __init__.py
    │   │   └── conversation_schema.py
    │   ├── services
    │   │   ├── ai
    │   │   │   ├── __init__.py
    │   │   │   ├── ai_factory.py
    │   │   │   ├── base_ai_service.py
    │   │   │   ├── myai_service.py
    │   │   │   └── openai_service.py 
    │   │   ├── analysis
    │   │   │   ├── __init__.py
    │   │   │   ├── fluency_analyzer.py
    │   │   │   ├── grammar_analyzer.py
    │   │   │   └── vocabulary_analyzer.py
    │   │   ├── __init__.py
    │   │   ├── recommendation_service.py
    │   │   └── scoring_service.py
    │   ├── utils
    │   │   ├── __init__.py
    │   │   ├── decorators.py
    │   │   ├── exceptions.py
    │   │   └── validators.py
    │   └── __init__.py
    ├── migrations
    │   ├── versions
    │   └── __init__.py
    ├── README.md
    ├── requirements.txt
    └── run.py
```

---
*Generated by FileTree Pro Extension*
Giải thích thêm:

Tại sao tách thành nhiều tầng?
→ Đảm bảo mô hình MVC mở rộng, mỗi tầng chỉ làm đúng một nhiệm vụ. Dễ kiểm thử và dễ thay thế, ví dụ đổi AI provider mà không sửa Controller.

Tại sao có __init__.py trong từng thư mục?
→ Để Python nhận diện đây là module hợp lệ, cho phép import theo dạng from app.services.ai import DeepSeekService.

Tại sao có config/settings.py?
→ Là nơi đọc .env bằng thư viện như python-dotenv, đảm bảo không hardcode giá trị trong code.

utils/ và services/analysis/ có tách riêng?
→ Có, để rõ ràng giữa “nghiệp vụ chính” (business logic) và “xử lý ngôn ngữ con” (analysis logic).
---

## **3) Ứng dụng nguyên tắc SOLID**

1. **Single Responsibility (SRP):** mỗi module chỉ đảm nhiệm một chức năng.
2. **Open/Closed (OCP):** có thể mở rộng (ví dụ thêm nhà cung cấp AI mới) mà không sửa mã hiện tại.
3. **Liskov Substitution (LSP):** mọi AI service đều tuân theo `IAIService`, có thể thay thế lẫn nhau.
4. **Interface Segregation (ISP):** giao diện hẹp, tách biệt cho từng mục đích (`IAIService`, `IRepository`).
5. **Dependency Inversion (DIP):** Controller phụ thuộc vào abstraction thay vì implementation cụ thể.

---

## **4) Cấu hình môi trường**

Tất cả cấu hình được nạp từ tệp `.env` trong thư mục `backend/`.

Ví dụ:

```
MONGODB_URI=mongodb://localhost:27017/japanese_learning
AI_PROVIDER=myai
MYAI_API_KEY=your_key_here
MYAI_BASE_URL=https://api.myai.com/v1
MYAI_MODEL=chat
```

---

## **5) Cài đặt và chạy**

Yêu cầu:

* Python ≥ 3.10
* MongoDB ≥ 6.0

Lệnh cài đặt:

```
cd backend
python -m venv venv
./venv/Scripts/Activate
pip install -r requirements.txt
python run.py
```

Ứng dụng chạy tại `http://localhost:5000`.

---

## **6) Tài liệu API (Swagger)**

Xem tại: `http://localhost:5000/apidocs`

Các endpoint chính:

* `/api/conversations` – quản lý hội thoại.
* `/api/topics` – danh sách chủ đề.
* `/api/courses` – danh sách khóa học.

---

## **7) Mô hình dữ liệu**

Các thực thể chính:

* `Conversation`: user_id, topic, level, messages[], score, recommendations[].
* `Message`: vai trò (người dùng hoặc AI), nội dung, thời gian, phân tích.
* `Score`: điểm ngữ pháp, từ vựng, độ tự nhiên, độ trôi chảy.
* `Recommendation`: khóa học gợi ý.

---

## **8) Lưu trữ và Repository**

`BaseRepository` cung cấp CRUD chung.
Tạo chỉ mục (index) để tăng tốc truy vấn:

```
db.conversations.createIndex({ user_id: 1, updated_at: -1 })
db.courses.createIndex({ level: 1, category: 1 })
```

---

## **9) Dịch vụ**

* **AI Service:** chọn nhà cung cấp AI, chuẩn hóa đầu ra.
* **Scoring Service:** tính điểm tổng hợp dựa trên trọng số.
* **Recommendation Service:** gợi ý khóa học dựa trên điểm yếu.

---

## **10) Controller và Route**

Controller gọi Repository và Service; Route xử lý HTTP, xác thực dữ liệu và trả về JSON.

---

## **11) Kiểm thử và công cụ**

Chạy thử:

```
python run.py
pytest
```

Kiểm tra chất lượng mã:

```
ruff check app/
```

---

## **12) Thêm nhà cung cấp AI mới**

1. Tạo file mới trong `app/services/ai/`, kế thừa `BaseAIService`.
2. Cập nhật `ai_factory.py`.
3. Thêm biến môi trường tương ứng (`NEWAI_API_KEY`, `NEWAI_BASE_URL`, `NEWAI_MODEL`).

Không cần chỉnh sửa Controller hoặc Route.

---

## **13) Triển khai (Deployment)**

* Production: chạy qua WSGI (`wsgi.py`).
* Ví dụ:

```
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## **14) Xử lý sự cố**

* Lỗi kết nối MongoDB: kiểm tra URI và trạng thái dịch vụ.
* 500 Internal Error: đảm bảo URI có tên database.
* Swagger không hiển thị: cài `flasgger` và khởi động lại.

---

## **15) Bảo mật và vận hành**

* Không commit file `.env` hoặc khóa bí mật.
* Thiết lập giới hạn tần suất gọi API (rate limiting).
* Có thể thêm xác thực (authentication middleware) trong `utils/decorators.py`.

---

## **16) Lộ trình phát triển**

* Tích hợp AI thực tế (DeepSeek, OpenAI, MyAI).
* Viết test đầy đủ.
* Thêm dữ liệu mẫu.
* Hoàn thiện logic phân tích ngữ pháp và từ vựng.

---

## **16.1) Lỗi thường gặp & cách sửa**

### Lỗi: "unsupported operand type(s) for +: 'int' and 'str'"

Triệu chứng:
- Ứng dụng bị crash hoặc trả về lỗi 500 khi tính điểm tổng hợp (scoring) cho các message.
- Traceback cho thấy TypeError với thông báo trên khi gọi các hàm tính tổng hoặc trung bình (sum/average).

Nguyên nhân:
- Dữ liệu phân tích trả về từ AI (hoặc dữ liệu mock) có thể chứa các giá trị số dưới dạng chuỗi, ví dụ `"score": "85"` hoặc `"response_time": "1200"`.
- Khi code cố gắng dùng `sum()` hoặc phép cộng giữa số và chuỗi (int/float + str) Python sẽ ném TypeError.

Tệp liên quan:
- `app/services/scoring_service.py` — nơi tổng hợp các điểm (grammar, vocabulary, naturalness) và thời gian phản hồi để tính điểm lưu loát.

Sửa nhanh đã áp dụng:
1. Thêm helper an toàn `_to_number(value, default=0.0)` để cố gắng chuyển mọi giá trị về `float`.
2. Khi xây danh sách điểm và `response_times`, gọi `ScoringService._to_number(...)` cho từng phần tử trước khi tính toán.
3. Lọc bỏ giá trị `None` cho `response_time` trước khi chuyển.

Tác dụng:
- Ngăn chặn lỗi TypeError khi AI trả về số ở dạng chuỗi.
- Giá trị không thể chuyển sẽ trả về `0.0` (có thể thay đổi tùy nhu cầu) để đảm bảo tính toán tiếp tục an toàn.

Kiểm tra sau sửa (quick check):
1. Trong PowerShell (đặt `backend` vào PYTHONPATH) kiểm tra import để xác nhận không có lỗi cú pháp:

```powershell
$env:PYTHONPATH='backend'; python -c "import importlib; importlib.import_module('app.services.scoring_service'); print('scoring_service imported OK')"
```

2. Chạy một kịch bản hoặc unit test giả lập message có `score` dưới dạng chuỗi và `response_time` dưới dạng chuỗi, đảm bảo `calculate_overall_score` trả về `Score` hợp lệ.

Gợi ý cải thiện thêm:
- Ghi log cảnh báo nếu `_to_number` phải dùng giá trị mặc định (để dễ phát hiện dữ liệu AI trả về sai định dạng).
- Thêm validation đầu vào cho dữ liệu phân tích AI (schema) trước khi sử dụng.
- Viết unit test kiểm thử trường hợp `score`/`response_time` là chuỗi, `None`, hay mất trường.


---

## **17) Giấy phép**

Dự án phát hành theo giấy phép **MIT License** (hoặc giấy phép khác nếu có chỉ định).

---


