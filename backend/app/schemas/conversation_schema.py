from marshmallow import Schema, fields, validate, validates, ValidationError


class ConversationCreateSchema(Schema):
    """Schema dùng để validate dữ liệu khi tạo mới cuộc hội thoại (conversation)"""
    user_id = fields.Str(required=True)  # user_id phải là chuỗi và bắt buộc
    topic = fields.Str(required=True)  # chủ đề cuộc hội thoại, chuỗi bắt buộc
    level = fields.Str(  # trình độ (level), chuỗi bắt buộc
        required=True,
        validate=validate.OneOf(['N5', 'N4', 'N3', 'N2', 'N1'])  # chỉ chấp nhận các giá trị trong danh sách này
    )


class MessageSendSchema(Schema):
    """Schema dùng để validate dữ liệu gửi tin nhắn mới vào cuộc hội thoại"""
    message = fields.Str(
        required=True,  # trường message là bắt buộc
        validate=validate.Length(min=1, max=1000)  # độ dài tối thiểu 1 ký tự, tối đa 1000 ký tự
    )
    response_time = fields.Int(
        required=False,  # response_time không bắt buộc
        validate=validate.Range(min=0)  # nếu có, phải là số nguyên >= 0
    )

    @validates('message')
    def validate_message(self, value):
        """Kiểm tra message không chỉ toàn khoảng trắng"""
        if not value.strip():  # nếu sau khi loại bỏ khoảng trắng, chuỗi rỗng thì lỗi
            raise ValidationError("Message cannot be empty or whitespace")


class MessageAnalysisSchema(Schema):
    """Schema cho dữ liệu phân tích tin nhắn (grammar, vocabulary, naturalness, thời gian phản hồi)"""
    grammar = fields.Dict(required=True)  # grammar: dict bắt buộc
    vocabulary = fields.Dict(required=True)  # vocabulary: dict bắt buộc
    naturalness = fields.Dict(required=True)  # naturalness: dict bắt buộc
    response_time = fields.Int(required=False)  # response_time không bắt buộc, kiểu int


class MessageSchema(Schema):
    """Schema cho 1 tin nhắn trong conversation"""
    role = fields.Str(
        required=True,
        validate=validate.OneOf(['user', 'assistant'])  # chỉ nhận 2 vai trò user hoặc assistant
    )
    content = fields.Str(required=True)  # nội dung tin nhắn bắt buộc
    timestamp = fields.DateTime(required=True)  # thời gian gửi tin nhắn, bắt buộc và phải đúng định dạng datetime
    analysis = fields.Nested(MessageAnalysisSchema, required=False)  # dữ liệu phân tích, không bắt buộc


class ScoreSchema(Schema):
    """Schema cho điểm đánh giá"""
    grammar = fields.Int()  # điểm grammar
    vocabulary = fields.Int()  # điểm vocabulary
    fluency = fields.Int()  # điểm fluency
    naturalness = fields.Int()  # điểm naturalness
    total = fields.Int()  # điểm tổng


class RecommendationSchema(Schema):
    """Schema cho đề xuất khóa học"""
    type = fields.Str(required=True)  # loại đề xuất, bắt buộc
    course_id = fields.Str(required=True)  # id khóa học, bắt buộc
    reason = fields.Str(required=True)  # lý do đề xuất, bắt buộc


class ConversationSchema(Schema):
    """Schema toàn bộ dữ liệu cuộc hội thoại (dùng để serialize/deserialize toàn bộ conversation)"""
    id = fields.Str(dump_only=True)  # id chỉ dùng khi xuất (dump), không cần validate khi nhận vào
    user_id = fields.Str(required=True)  # user_id bắt buộc
    topic = fields.Str(required=True)  # topic bắt buộc
    level = fields.Str(required=True)  # level bắt buộc
    messages = fields.List(fields.Nested(MessageSchema))  # danh sách tin nhắn, mỗi tin nhắn theo schema MessageSchema
    overall_score = fields.Nested(ScoreSchema)  # điểm tổng thể, theo ScoreSchema
    recommendations = fields.List(fields.Nested(RecommendationSchema))  # danh sách đề xuất
    created_at = fields.DateTime(dump_only=True)  # thời gian tạo, chỉ xuất ra
    updated_at = fields.DateTime(dump_only=True)  # thời gian cập nhật, chỉ xuất ra
