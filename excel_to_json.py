"""
Script chuyển đổi file Excel sang JSON format cho vocab app
Yêu cầu: pip install pandas openpyxl
"""

import pandas as pd
import json
import os

def excel_to_json(excel_file, output_name=None):
    """
    Chuyển đổi file Excel sang JSON
    
    Format Excel cần có các cột:
    - word: từ vựng
    - pos: từ loại (n), (v), (adj)...
    - meaning: nghĩa tiếng Việt
    - example: câu ví dụ
    - example_meaning: nghĩa của ví dụ
    """
    
    # Đọc file Excel
    print(f"📖 Đang đọc file: {excel_file}")
    df = pd.read_excel(excel_file)
    
    # Kiểm tra các cột bắt buộc
    required_columns = ['word', 'pos', 'meaning', 'example', 'example_meaning']
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f"⚠️ Thiếu các cột: {', '.join(missing)}")
        print(f"📋 Các cột hiện có: {', '.join(df.columns)}")
        return
    
    # Chuyển đổi sang dictionary
    vocab_dict = {}
    
    for idx, row in df.iterrows():
        word_id = f"word_{idx + 1}"
        vocab_dict[word_id] = {
            "word": str(row['word']).strip(),
            "pos": str(row['pos']).strip(),
            "meaning": str(row['meaning']).strip(),
            "example": str(row['example']).strip(),
            "example_meaning": str(row['example_meaning']).strip()
        }
    
    # Tạo tên file output
    if output_name is None:
        base_name = os.path.splitext(os.path.basename(excel_file))[0]
        output_name = f"{base_name}.json"
    
    # Đảm bảo output có đuôi .json
    if not output_name.endswith('.json'):
        output_name += '.json'
    
    # Lưu vào thư mục Topics
    output_path = os.path.join("Topics", output_name)
    os.makedirs("Topics", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Đã chuyển đổi thành công!")
    print(f"📁 File output: {output_path}")
    print(f"📊 Tổng số từ: {len(vocab_dict)}")
    
    # Hiển thị preview
    print("\n🔍 Preview 3 từ đầu tiên:")
    for i, (word_id, info) in enumerate(list(vocab_dict.items())[:3]):
        print(f"\n{i+1}. {info['word']} {info['pos']}")
        print(f"   Nghĩa: {info['meaning']}")
        print(f"   VD: {info['example']}")

def create_sample_excel():
    """Tạo file Excel mẫu để tham khảo"""
    
    sample_data = {
        'word': ['hello', 'world', 'python', 'data', 'science'],
        'pos': ['(n)', '(n)', '(n)', '(n)', '(n)'],
        'meaning': ['xin chào', 'thế giới', 'ngôn ngữ lập trình', 'dữ liệu', 'khoa học'],
        'example': [
            'Hello, how are you?',
            'The world is beautiful.',
            'Python is easy to learn.',
            'Data is important.',
            'Science helps us understand.'
        ],
        'example_meaning': [
            'Xin chào, bạn khỏe không?',
            'Thế giới thật đẹp.',
            'Python dễ học.',
            'Dữ liệu rất quan trọng.',
            'Khoa học giúp chúng ta hiểu biết.'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    output_file = 'sample_vocab_template.xlsx'
    df.to_excel(output_file, index=False)
    
    print(f"✅ Đã tạo file mẫu: {output_file}")
    print("📝 Bạn có thể mở file này, chỉnh sửa và chạy lại script để chuyển đổi!")

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    print("=" * 50)
    print("📚 EXCEL TO JSON CONVERTER")
    print("=" * 50)
    print()
    
    choice = input("1. Chuyển đổi file Excel có sẵn\n2. Tạo file Excel mẫu\nLựa chọn: ").strip()
    
    if choice == '1':
        excel_file = input("\n📁 Nhập đường dẫn file Excel: ").strip()
        
        if not os.path.exists(excel_file):
            print(f"⚠️ Không tìm thấy file: {excel_file}")
        else:
            output_name = input("📝 Tên file JSON output (Enter để dùng tên mặc định): ").strip()
            if not output_name:
                output_name = None
            
            try:
                excel_to_json(excel_file, output_name)
            except Exception as e:
                print(f"❌ Lỗi: {e}")
                print("\n💡 Tips:")
                print("- Đảm bảo file Excel có đúng format")
                print("- Cài đặt thư viện: pip install pandas openpyxl")
    
    elif choice == '2':
        try:
            create_sample_excel()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            print("💡 Cài đặt thư viện: pip install pandas openpyxl")
    
    else:
        print("⚠️ Lựa chọn không hợp lệ!")

    print("\n" + "=" * 50)
