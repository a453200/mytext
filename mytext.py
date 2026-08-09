```python
import streamlit as st
import cv2
import numpy as np
from PIL import Image


# -----------------------------------------------------
# Page Configuration
# -----------------------------------------------------

st.set_page_config(
    page_title="My Handwriting Library",
    page_icon="📚"
)


# -----------------------------------------------------
# User Database
# -----------------------------------------------------

if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "user1": {
            "password": "111",
            "library": {}
        },
        "user2": {
            "password": "222",
            "library": {}
        }
    }


# -----------------------------------------------------
# Login State
# -----------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None


# -----------------------------------------------------
# Extract Characters
# -----------------------------------------------------

def extract_characters(image):

    img_array = np.array(image)

    # Handle RGBA images
    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
        img_array = cv2.cvtColor(
            img_array,
            cv2.COLOR_RGBA2RGB
        )

    # Convert to grayscale
    gray = cv2.cvtColor(
        img_array,
        cv2.COLOR_RGB2GRAY
    )

    # Convert handwriting to white-on-black
    _, thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Find character regions
    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    bounding_boxes = []

    for cnt in contours:

        x, y, w, h = cv2.boundingRect(cnt)

        if w > 10 and h > 10:
            bounding_boxes.append(
                (x, y, w, h)
            )

    # Sort from left to right
    bounding_boxes = sorted(
        bounding_boxes,
        key=lambda b: b[0]
    )

    char_images = []
    debug_img = img_array.copy()

    for x, y, w, h in bounding_boxes:

        # Draw green rectangle
        cv2.rectangle(
            debug_img,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cropped = img_array[
            y:y+h,
            x:x+w
        ]

        char_images.append(cropped)

    return char_images, debug_img


# -----------------------------------------------------
# Generate Handwritten Text
# -----------------------------------------------------

def generate_handwriting(text, char_dict):

    images_to_concat = []

    space_width = 30
    max_height = 0

    for char in text:

        # Space
        if char == " ":

            images_to_concat.append({
                "is_space": True,
                "width": space_width
            })

        # Character exists in library
        elif char in char_dict:

            img_array = char_dict[char]

            img_pil = Image.fromarray(
                img_array
            )

            images_to_concat.append(
                img_pil
            )

            if img_pil.height > max_height:
                max_height = img_pil.height

    # Nothing to generate
    if not images_to_concat:

        return Image.new(
            "RGB",
            (500, 200),
            color="white"
        )

    # Calculate total width
    total_width = 0

    for item in images_to_concat:

        if isinstance(item, dict):

            total_width += item["width"]

        else:

            total_width += item.width

    # Create blank canvas
    result_image = Image.new(
        "RGB",
        (
            total_width,
            max_height + 20
        ),
        color="white"
    )

    current_x = 0

    # Paste characters
    for item in images_to_concat:

        if isinstance(item, dict):

            current_x += item["width"]

        else:

            y_offset = (
                max_height - item.height
            ) + 10

            result_image.paste(
                item,
                (current_x, y_offset)
            )

            current_x += item.width

    return result_image


# -----------------------------------------------------
# Login Screen
# -----------------------------------------------------

def show_login_screen():

    st.title("🔐 My Handwriting Library")

    st.write(
        "Please log in to access your personal handwriting library."
    )

    username = st.text_input(
        "Username",
        placeholder="e.g., user1"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="e.g., 111"
    )

    if st.button("Log In"):

        if username in st.session_state.users_db:

            if (
                st.session_state.users_db[username]["password"]
                == password
            ):

                st.session_state.logged_in = True
                st.session_state.current_user = username

                st.rerun()

            else:

                st.error(
                    "Incorrect password."
                )

        else:

            st.error(
                "Username does not exist."
            )


# -----------------------------------------------------
# Main Application
# -----------------------------------------------------

def show_main_app():

    user = st.session_state.current_user

    # Get this user's personal library
    user_library = (
        st.session_state.users_db[user]["library"]
    )

    # -------------------------------------------------
    # Header
    # -------------------------------------------------

    col1, col2 = st.columns([8, 2])

    with col1:

        st.title(
            "📚 My Handwriting Library"
        )

    with col2:

        st.write("")

        if st.button("Log Out"):

            st.session_state.logged_in = False
            st.session_state.current_user = None

            st.rerun()

    st.write(
        f"Welcome, **{user}**!"
    )


    # -------------------------------------------------
    # Section 1: Register New Characters
    # -------------------------------------------------

    st.header(
        "1. Register New Characters"
    )

    uploaded_file = st.file_uploader(
        "Upload a photo containing handwritten alphabet characters.",
        type=["jpg", "png", "jpeg"]
    )

    if uploaded_file is not None:

        image = Image.open(
            uploaded_file
        )

        st.image(
            image,
            caption="Uploaded Image",
            width=300
        )

        target_chars = st.text_input(
            "Enter the characters from left to right.",
            placeholder="Example: abc"
        )

        if st.button(
            "Save to My Library"
        ):

            if target_chars:

                char_images, debug_img = (
                    extract_characters(image)
                )

                st.image(
                    debug_img,
                    caption="Detected Character Regions",
                    width=300
                )

                if len(char_images) == len(target_chars):

                    for i, char in enumerate(
                        target_chars
                    ):

                        user_library[char] = (
                            char_images[i]
                        )

                    st.success(
                        f"Successfully registered: {target_chars}"
                    )

                else:

                    st.error(
                        f"You entered {len(target_chars)} "
                        f"characters, but "
                        f"{len(char_images)} character regions "
                        f"were detected. Please check the image "
                        f"or your input."
                    )

            else:

                st.warning(
                    "Please enter the characters shown in the image."
                )


    st.divider()


    # -------------------------------------------------
    # Section 2: My Character Library
    # -------------------------------------------------

    st.header(
        "2. My Character Library"
    )

    collected_chars = sorted(
        list(user_library.keys())
    )

    if collected_chars:

        st.write(
            "Characters currently available:"
        )

        st.write(
            "**"
            + ", ".join(collected_chars)
            + "**"
        )

    else:

        st.info(
            "Your handwriting library is currently empty."
        )


    st.divider()


    # -------------------------------------------------
    # Section 3: Write in My Handwriting
    # -------------------------------------------------

    st.header(
        "3. Write in My Handwriting"
    )

    user_text = st.text_input(
        "Enter an English sentence.",
        placeholder="Example: Hello World!"
    )

    if st.button(
        "Generate Handwritten Text"
    ):

        if not user_text:

            st.warning(
                "Please enter a sentence first."
            )

        else:

            # Check missing characters
            missing_chars = [
                c
                for c in user_text
                if c != " "
                and c not in user_library
            ]

            missing_unique = sorted(
                list(set(missing_chars))
            )

            if missing_unique:

                st.warning(
                    "The following characters are not "
                    "in your library: "
                    + ", ".join(missing_unique)
                )

            else:

                # Generate handwriting
                with st.spinner(
                    "Generating your handwriting..."
                ):

                    result_image = (
                        generate_handwriting(
                            user_text,
                            user_library
                        )
                    )

                st.success(
                    "Handwritten text generated successfully!"
                )

                st.image(
                    result_image,
                    caption="Your Handwriting",
                    use_container_width=True
                )


# -----------------------------------------------------
# Screen Routing
# -----------------------------------------------------

if not st.session_state.logged_in:

    show_login_screen()

else:

    show_main_app()
```
