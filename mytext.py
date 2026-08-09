import streamlit as st
import cv2
import numpy as np
from PIL import Image

if 'char_library' not in st.session_state:
    st.session_state.char_library = {}

def extract_characters(image):
    img_array = np.array(image)
    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 10 and h > 10:
            bounding_boxes.append((x, y, w, h))
            
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])
    char_images = []
    debug_img = img_array.copy()
    
    for (x, y, w, h) in bounding_boxes:
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cropped = img_array[y:y+h, x:x+w]
        char_images.append(cropped)
        
    return char_images, debug_img

def generate_handwriting(text, char_dict):
    images_to_concat = []
    space_width = 30
    max_height = 0
    
    for char in text:
        if char == ' ':
            images_to_concat.append({'is_space': True, 'width': space_width})
        elif char in char_dict:
            img_array = char_dict[char]
            img_pil = Image.fromarray(img_array)
            images_to_concat.append(img_pil)
            if img_pil.height > max_height:
                max_height = img_pil.height
        else:
            pass
            
    if not images_to_concat:
        return Image.new('RGB', (500, 200), color='white')
        
    total_width = 0
    for item in images_to_concat:
        if isinstance(item, dict): 
            total_width += item['width']
        else: 
            total_width += item.width
            
    result_image = Image.new('RGB', (total_width, max_height + 20), color='white')
    
    current_x = 0
    for item in images_to_concat:
        if isinstance(item, dict): 
            current_x += item['width']
        else:
            y_offset = (max_height - item.height) + 10 
            result_image.paste(item, (current_x, y_offset))
            current_x += item.width
            
    return result_image


st.set_page_config(page_title="내 필체 라이브러리", page_icon="📚")
st.title("📚 내 필체 라이브러리 구축하기")


st.header("1. 새 글자 등록하기")
uploaded_file = st.file_uploader("알파벳이 적힌 종이를 올려주세요 (한 글자도 좋고, 여러 글자도 됩니다)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 이미지", width=300)
    

    target_chars = st.text_input("사진에 있는 글자를 왼쪽부터 순서대로 적어주세요 (예: a, 또는 abc):")
    
    if st.button("라이브러리에 저장"):
        if target_chars:
            char_images, debug_img = extract_characters(image)
            st.image(debug_img, caption="인식된 영역 확인", width=300)
            

            if len(char_images) == len(target_chars):
                for i, char in enumerate(target_chars):
                    st.session_state.char_library[char] = char_images[i]
                st.success(f"'{target_chars}' 글자가 성공적으로 등록되었습니다!")
            else:
                st.error(f"입력한 글자 수는 {len(target_chars)}개인데, 인식된 글자(초록 박스)는 {len(char_images)}개입니다. 사진을 더 깔끔하게 찍거나 입력값을 확인해주세요.")
        else:
            st.warning("사진에 있는 글자가 무엇인지 입력해주세요.")

st.divider() 
st.header("2. Text Library")

collected_chars = sorted(list(st.session_state.char_library.keys()))
st.write(f"현재 사용할 수 있는 글자: **{', '.join(collected_chars) if collected_chars else '아직 등록된 글자가 없습니다.'}**")

st.divider()


st.header("3. 내 필체로 글쓰기")
user_text = st.text_input("변환할 영어 문장을 입력하세요:")

if st.button("내 필체로 변환하기") and user_text:
    missing_chars = [c for c in user_text if c != ' ' and c not in st.session_state.char_library]
    
    if missing_chars:
        missing_unique = sorted(list(set(missing_chars)))
        st.warning(f"앗! 아직 도감에 없는 글자가 포함되어 있습니다: {', '.join(missing_unique)}")
    
    with st.spinner("조합하는 중..."):
        result_image = generate_handwriting(user_text, st.session_state.char_library)
        st.success("변환 완료!")
        st.image(result_image, caption="생성된 결과물", use_column_width=True)
