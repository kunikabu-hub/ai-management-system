#!/usr/bin/env python3
"""
画像を2000ピクセル以下にリサイズ
"""
import os
from PIL import Image

INPUT_DIR = "output/all_survey_images"
OUTPUT_DIR = "output/all_survey_images_resized"
MAX_SIZE = 1800  # 安全マージンを持たせて1800

def resize_image(input_path, output_path, max_size=MAX_SIZE):
    """画像をリサイズ（アスペクト比維持）"""
    img = Image.open(input_path)
    width, height = img.size

    # 最大サイズを超えている場合のみリサイズ
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    img.save(output_path, 'PNG', optimize=True)
    return img.size

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # page_*.png ファイルを取得
    files = sorted([f for f in os.listdir(INPUT_DIR) if f.startswith('page_') and f.endswith('.png')])

    print(f"リサイズ対象: {len(files)} 枚\n")

    for i, filename in enumerate(files, 1):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)

        new_size = resize_image(input_path, output_path)

        if i % 10 == 0 or i == len(files):
            print(f"  [{i}/{len(files)}] {filename} → {new_size[0]}x{new_size[1]}")

    print(f"\n✅ 完了: {len(files)}枚の画像を {OUTPUT_DIR} に保存しました")

if __name__ == '__main__':
    main()
