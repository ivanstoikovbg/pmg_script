import os
from PIL import Image, ExifTags
from psd_tools import PSDImage
from tqdm import tqdm
from plyer import notification

input_folder = "input_images"
output_folder = "output_images"
logo_path = "logo.psd"

os.makedirs(output_folder, exist_ok=True)

def remove_unwanted_files(directory):
    unwanted_extensions = [".nef", ".raw", ".cr2"]
    for filename in os.listdir(directory):
        if any(filename.lower().endswith(ext) for ext in unwanted_extensions):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Изтрит файл: {filename}")
            except Exception as e:
                print(f"Грешка при изтриването на {filename}: {e}")

def correct_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                return image.rotate(180, expand=True)
            elif orientation_value == 6:
                return image.rotate(270, expand=True)
            elif orientation_value == 8:
                return image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

def check_image_orientation(img):
    width, height = img.size
    if height > width:
        return "Вертикално"
    elif width > height:
        return "Хоризонтално"
    else:
        return "Квадратно"

def load_logo(logo_path):
    try:
        psd = PSDImage.open(logo_path)
        logo = psd.topil()
        return logo.convert("RGBA")
    except Exception as e:
        print(f"Грешка при зареждане на логото от PSD: {e}")
        return None

def add_logo(img, logo, orientation):
    try:
        img = img.convert("RGBA")
        img_width, img_height = img.size
        logo_width, logo_height = logo.size
        if orientation == "Вертикално":
            scale_factor = min(img_width * 0.5 / logo_width, img_height * 0.5 / logo_height)
        else:
            scale_factor = min(img_width * 0.3 / logo_width, img_height * 0.3 / logo_height)
        new_logo_width = int(logo_width * scale_factor)
        new_logo_height = int(logo_height * scale_factor)
        logo = logo.resize((new_logo_width, new_logo_height), Image.LANCZOS)

        logo = logo.copy()
        alpha = logo.split()[3]
        alpha = alpha.point(lambda p: p * 0.8)
        logo.putalpha(alpha)

        position = (10, img_height - new_logo_height - 10)
        img.paste(logo, position, logo)
        return img.convert("RGB")
    except Exception as e:
        print(f"Грешка при добавянето на логото: {e}")
        return img

def convert_images_to_png(input_dir, output_dir):
    logo = load_logo(logo_path)
    if logo is None:
        print("Неуспешно зареждане на логото. Прекратяване на програмата.")
        return

    files = os.listdir(input_dir)
    with tqdm(total=len(files), desc="Обработка на изображения") as pbar:
        for index, filename in enumerate(files, start=1):
            input_path = os.path.join(input_dir, filename)
            try:
                with Image.open(input_path) as img:
                    img = correct_orientation(img)
                    orientation = check_image_orientation(img)
                    print(f"{filename}: {orientation}")
                    img = add_logo(img, logo, orientation)
                    new_filename = f"{index}.png"
                    output_path = os.path.join(output_dir, new_filename)
                    img.save(output_path, "PNG")
                    print(f"Успешно конвертирано: {filename} -> {new_filename}")
            except Exception as e:
                print(f"Грешка при обработката на {filename}: {e}")
            pbar.update(1)

def main():
    if not os.path.exists(input_folder):
        print(f"Папката {input_folder} не съществува. Моля, добавете изображения.")
        return
    if not os.path.exists(logo_path):
        print(f"Логото {logo_path} не е намерено. Моля, проверете пътя до логото.")
        return
    remove_unwanted_files(input_folder)
    convert_images_to_png(input_folder, output_folder)
    notification.notify(
        title="Обработка на изображения",
        message="Конвертирането завърши успешно!",
        timeout=5
    )
    print("Конвертирането завърши!")

if __name__ == "__main__":
    main()
