# BabyAGI

# Mục tiêu

Script Python này là một ví dụ về hệ thống quản lý công việc được trí tuệ nhân tạo hỗ trợ. 
Hệ thống sử dụng OpenAI và cơ sở dữ liệu vector như Chroma hoặc Weaviate để tạo, 
ưu tiên và thực hiện các công việc. Ý tưởng chính đằng sau hệ thống này là nó tạo ra các 
đầu việc dựa trên kết quả của các nhiệm vụ trước đó và một mục tiêu đã được xác định trước. 
Sau đó, script sử dụng khả năng xử lý ngôn ngữ tự nhiên (NLP) của OpenAI để tạo ra các công việc 
mới dựa trên mục tiêu, và sử dụng Chroma/Weaviate để lưu trữ và truy xuất
kết quả công việc trước đó để có bối cảnh (context). Đây là phiên bản rút gọn của 
[Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) 
(28 tháng 3 năm 2023).

Bản README này bao gồm:
- [Cách script hoạt động](#how-it-works)
- [Cách sử dụng script](#how-to-use)
- [Các mô hình được hỗ trợ](#supported-models)
- [Cảnh báo về việc chạy script liên tục](#continuous-script-warning)



# Cách script hoạt động<a name="how-it-works"></a>

Script này hoạt động bằng cách chạy một vòng lặp vô hạn và thực hiện các bước sau:
1. Lấy công việc đầu tiên từ danh sách công việc.
2. Gửi công việc đến agent thực thi, sử dụng API của OpenAI để hoàn thành công việc dựa trên bối cảnh.
3. Bổ sung kết quả và lưu trữ nó trong [Chroma](https://docs.trychroma.com)/[Weaviate](https://weaviate.io/).
4. Tạo công việc mới và sắp xếp lại mức độ ưu tiên của danh sách công việc dựa trên mục tiêu và kết quả của công việc trước đó.


   </br>

![image](https://user-images.githubusercontent.com/21254008/235015461-543a897f-70cc-4b63-941a-2ae3c9172b11.png)

Hàm `execution_agent()` sử dụng API của OpenAI. Nó nhận hai tham số: mục tiêu và công việc. 
Sau đó, nó gửi một yêu cầu đầu vào (prompt) đến API của OpenAI, và nhận kết quả trả về từ đó. 
Yêu cầu đầu vào (prompt) bao gồm mô tả công việc của hệ thống AI, mục tiêu và yêu cầu công việc. 
Kết quả sau đó được trả về dưới dạng chuỗi.

Hàm `task_creation_agent()` sử dụng API của OpenAI để tạo ra các công việc mới dựa trên mục tiêu
và kết quả của công việc trước đó. Hàm nhận bốn tham số: mục tiêu, kết quả của công việc trước đó, mô tả công việc,
và danh sách công việc hiện tại. Sau đó, nó gửi một yêu cầu đầu vào (prompt) đến API của OpenAI, và nhận danh sách
công việc mới dưới dạng chuỗi. Hàm sau đó trả về các đầu việc mới dưới dạng danh sách các từ điển (dictionaries) chứa tên công việc.

Hàm `prioritization_agent()` sử dụng API của OpenAI để sắp xếp lại danh sách công việc dựa trên mức độ ưu tiên. 
Hàm nhận một tham số: ID của công việc hiện tại. Nó gửi một yêu cầu đầu vào (prompt) đến API của OpenAI, 
và nhận danh sách công việc đã được sắp xếp lại dưới dạng danh sách có số thứ tự.

Cuối cùng, script sử dụng Chroma/Weaviate để lưu trữ và truy xuất kết quả công việc để có bối cảnh.
Script tạo một bộ sưu tập (collection) Chroma/Weaviate dựa trên tên bảng biểu được chỉ định trong biến TABLE_NAME.
Chroma/Weaviate sau đó được sử dụng để lưu trữ kết quả của công việc trong bộ sưu tập, 
cùng với tên công việc và bất kỳ siêu dữ liệu (metadata) nào khác.


# Cách sử dụng script<a name="how-to-use"></a>

Để sử dụng script, bạn cần thực hiện các bước sau:
1. Clone repository bằng `git clone https://github.com/yoheinakajima/babyagi.git` và `cd` vào thư mục đã clone.
2. Cài đặt các package cần thiết bằng lệnh: `pip install -r requirements.txt`
3. Sao chép file *.env.example* thành *.env* bằng lệnh: `cp .env.example .env`. Đây là nơi bạn sẽ thiết lập các biến sau.
4. Đặt API key của OpenAI vào biến OPENAI_API_KEY và OPENAI_API_MODEL. Để sử dụng với Weaviate, bạn cũng cần thiết lập thêm các biến bổ sung, chi tiết xem [ở đây](docs/weaviate.md).
5. Đặt tên bảng biểu (table) mà kết quả công việc sẽ được lưu trữ vào biến TABLE_NAME.
6. (Tùy chọn) Đặt tên của BabyAGI instance trong biến BABY_NAME.
7. (Tùy chọn) Đặt mục tiêu của hệ thống quản lý công việc trong biến OBJECTIVE.
8. (Tùy chọn) Đặt công việc đầu tiên của hệ thống trong biến INITIAL_TASK.
9. Chạy script: `python babyagi.py`

Tất cả các giá trị tùy chọn ở trên cũng có thể được chỉ định khi chạy lệnh.

# Chạy script trong Docker container

Để chạy hệ thống trong Docker container, bạn cần cài đặt docker và docker-compose. 
Docker desktop là lựa chọn đơn giản nhất https://www.docker.com/products/docker-desktop/

Để chạy hệ thống trong một Docker container, thiết lập file *.env* như các bước ở trên và chạy lệnh sau:

        docker-compose up

# Các mô hình được hỗ trợ<a name="supported-models"></a>

Script này hoạt động được với tất cả các mô hình của OpenAI, cũng như Llama và các biến thể của nó thông qua Llama.cpp. 
Mô hình mặc định là **gpt-3.5-turbo**. Để sử dụng một mô hình khác, chỉ định nó thông qua biến LLM_MODEL hoặc sử dụng giao diện dòng lệnh (command line).


## Llama**

Llama yêu cầu cài đặt package llama-cpp. Bạn cũng cần tải về weights của mô hình Llama.

- **Không chia sẻ IPFS, magnet links, hoặc bất kỳ liên kết nào khác đến việc tải xuống mô hình ở bất kỳ nơi nào trong repository này, bao gồm trong issues, thảo luận hoặc pull requests. Chúng sẽ bị xóa ngay lập tức.**

Một khi bạn đã cài đặt và tải về các files cần thiết, đặt LLAMA_MODEL_PATH tới đường dẫn của mô hình cụ thể mà 
bạn muốn sử dụng. Để thuận tiện, bạn có thể liên kết `models` trong BabyAGI repo với thư mục chứa weights của
mô hình Llama. Sau đó chạy script với `LLM_MODEL=llama` hoặc thêm `-l` argument.

# Cảnh báo về việc chạy script liên tục<a name="continuous-script-warning"></a>

Script này được thiết kế để chạy liên tục như một phần của hệ thống quản lý công việc. 
Chạy script này liên tục có thể dẫn đến số lượng request API gửi đi là rất lớn, vì vậy hãy sử dụng nó một cách có trách nhiệm. 
Ngoài ra, BabyAGI script yêu cầu API của OpenAI được thiết lập đúng cách, vì vậy hãy chắc chắn rằng bạn đã set up API trước khi chạy script.


# Đóng góp

Cảm ơn bạn đã quan tâm đến việc đóng góp cho BabyAGI! 
Để giữ cho BabyAGI đơn giản và dễ hiểu, chúng tôi đề xuất bạn tuân thủ các hướng dẫn sau khi gửi PR:
- Tập trung vào các sửa đổi nhỏ, từng phần hơn là việc tái cấu trúc lớn.
- Khi giới thiệu các tính năng mới, hãy cung cấp mô tả chi tiết về trường hợp sử dụng cụ thể mà bạn đang giải quyết.

Lời ghi chú từ @yoheinakajima(Mùng 5 tháng 4 năm 2023):
> Tôi biết có nhiều PR đang chờ xử lý, cảm ơn sự kiên nhẫn của bạn - vì tôi vừa mới bắt đầu với GitHub/OpenSource,
> và không dự định thời gian của mình một cách hợp lý trong tuần này. Về hướng đi, tôi đang phân vân giữa giữ 
> nó đơn giản và mở rộng - hiện tôi đang hướng về việc giữ một Baby AGI cốt lõi đơn giản, và sử dụng nó như 
> một nền tảng để hỗ trợ và quảng bá các phương pháp khác nhau để mở rộng nó (ví dụ: BabyAGIxLangchain là 
> một hướng đi). Tôi tin rằng có nhiều phương pháp có giá trị để khám phá, và tôi thấy giá trị trong việc có 
> một nơi trung tâm để so sánh và thảo luận. Sắp tới sẽ có thêm nhiều cập nhật.

Tôi mới bắt đầu với GitHub và open source, vì vậy hãy kiên nhẫn khi tôi học cách quản lý dự án này
một cách tốt nhất. Tôi làm việc tại một quỹ đầu tư mạo hiểm vào ban ngày, vì vậy tôi thường xem qua PR và issues
vào buổi tối sau khi đưa con cái đi ngủ - có thể không phải mỗi tối. Tôi chào đón các ý tưởng về việc có thêm
sự hỗ trợ, và tôi sẽ cập nhật phần này sớm thôi (kỳ vọng, tầm nhìn, v.v.). 
Tôi đang nói chuyện với nhiều người và cùng lúc học hỏi thêm - hãy kiên nhẫn chờ đợi cập nhật nhé!

# Báo cáo hoạt động BabyAGI

Để giúp cộng đồng BabyAGI cập nhật thông tin về tiến trình dự án, Blueprint AI đã phát triển một bộ tóm tắt 
hoạt động Github cho BabyAGI. Báo cáo ngắn gọn này hiển thị tóm tắt tất cả các đóng góp vào repository BabyAGI trong
7 ngày qua (liên tục cập nhật), giúp bạn dễ dàng theo dõi các cập nhật mới nhất.

Để xem báo cáo hoạt động 7 ngày của BabyAGI, hãy truy cập vào đây: [https://app.blueprint.ai/github/yoheinakajima/babyagi](https://app.blueprint.ai/github/yoheinakajima/babyagi)

[<img width="293" alt="image" src="https://user-images.githubusercontent.com/334530/235789974-f49d3cbe-f4df-4c3d-89e9-bfb60eea6308.png">](https://app.blueprint.ai/github/yoheinakajima/babyagi)

# Các dự án được truyền cảm hứng

Trong thời gian ngắn kể từ khi nó được phát hành, BabyAGI đã truyền cảm hứng cho nhiều dự án. 
Bạn có thể xem tất cả chúng [tại đây](docs/inspired-projects.md).

# Nguồn gốc

BabyAGI là phiên bản rút gọn của [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) 
(28 tháng 3 năm 2023) được chia sẻ trên Twitter. Phiên bản này giảm xuống còn 140 dòng: 13 comment, 22 dòng trống, và 105 dòng code.
Tên của repository được đặt ra sau khi phản ứng với agent tự động ban đầu - tác giả không có ý định ngụ ý rằng đây là AGI.

Made with love bởi [@yoheinakajima](https://twitter.com/yoheinakajima), một nhà đầu tư mạo hiểm (và rất muốn biết bạn đang xây dựng cái gì!)
