import google.generativeai as genai
import requests
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageGrab
import os
import threading
import cv2
import time
import re

gemini_api_key = "Use Your Gemni key Here"
news_api_key = "Use Your News key Here"

genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction="""You are 'Your Personal AI Assistant', a very intelligent AI assistant.
    Current year is 2026. Current month is May 2026.
    Answer ANY question asked by the user in any language.
    Never refuse to answer. Never say you cannot help.
    Be friendly, helpful and conversational.
    If user speaks Urdu or Roman Urdu, reply in Roman Urdu.
    If user speaks English, reply in English."""
)

chat = model.start_chat(history=[])

# Color name to RGB mapping
COLOR_MAP = {
    "white": (255, 255, 255, 255),
    "black": (0, 0, 0, 255),
    "red": (255, 0, 0, 255),
    "green": (0, 255, 0, 255),
    "blue": (0, 0, 255, 255),
    "yellow": (255, 255, 0, 255),
    "purple": (128, 0, 128, 255),
    "orange": (255, 165, 0, 255),
    "pink": (255, 192, 203, 255),
    "gray": (128, 128, 128, 255),
    "grey": (128, 128, 128, 255),
    "cyan": (0, 255, 255, 255),
    "brown": (165, 42, 42, 255),
    "gold": (255, 215, 0, 255),
    "silver": (192, 192, 192, 255),
    "navy": (0, 0, 128, 255),
    "maroon": (128, 0, 0, 255),
    "lime": (0, 255, 0, 255),
    "violet": (238, 130, 238, 255),
    "indigo": (75, 0, 130, 255),
}

def detect_bg_action(text):
    text_lower = text.lower()

    # Check remove background
    if any(phrase in text_lower for phrase in [
        "remove background", "remove bg", "background remove",
        "background hatao", "background hata do", "background ko hata do",
        "bg remove", "background delete"
    ]):
        return "remove", None

    # Check change background — broad matching
    change_keywords = [
        "change", "badlo", "change kar", "change karo",
        "color change", "colour change", "background"
    ]

    has_change = any(word in text_lower for word in change_keywords)

    if has_change:
        for color_name, color_value in COLOR_MAP.items():
            if color_name in text_lower:
                return "change", color_value
        return "change", None

    return None, None
    if any(phrase in text_lower for phrase in change_phrases):
        # Find color in text
        for color_name, color_value in COLOR_MAP.items():
            if color_name in text_lower:
                return "change", color_value
        return "change", None

    return None, None

def get_news(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&apiKey={news_api_key}&language=en&pageSize=5"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "ok" and data["totalResults"] > 0:
        news_text = f"Latest news about '{topic}':\n\n"
        for i, article in enumerate(data["articles"][:5], 1):
            news_text += f"{i}. {article['title']}\n"
            news_text += f"   Source: {article['source']['name']}\n"
            news_text += f"   {article['description']}\n\n"
        return news_text
    else:
        return f"No news found about '{topic}'!"

def analyze_image(image_path, question):
    try:
        img = Image.open(image_path)
        response = model.generate_content([question, img])
        return response.text
    except Exception as e:
        return f"Error analyzing image: {e}"

def analyze_document(doc_path, question):
    try:
        with open(doc_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        prompt = f"Document content:\n{content}\n\nUser question: {question}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error reading document: {e}"

def change_background(image_path, bg_color):
    try:
        from rembg import remove
        import onnxruntime
        input_image = Image.open(image_path).convert("RGBA")
        removed = remove(input_image)
        background = Image.new("RGBA", removed.size, bg_color)
        final_image = Image.alpha_composite(background, removed)
        final_image = final_image.convert("RGB")
        output_path = "changed_bg.png"
        final_image.save(output_path)
        return output_path
    except Exception as e:
        return f"Error: {e}"

def remove_background(image_path):
    try:
        from rembg import remove
        import onnxruntime
        input_image = Image.open(image_path).convert("RGBA")
        output_image = remove(input_image)
        output_path = "removed_bg.png"
        output_image.save(output_path)
        return output_path
    except Exception as e:
        return f"Error: {e}"
class PersonalAIApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Your Personal AI Assistant")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.selected_image_path = None
        self.pending_image_path = None
        self.pending_ctk_image = None
        self.selected_doc_path = None
        self.setup_ui()

    def setup_ui(self):
        header = ctk.CTkFrame(self.root, height=60, fg_color="#1a1a2e")
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🤖 Your Personal AI Assistant",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00d4ff"
        ).pack(side="left", padx=20, pady=15)

        self.chat_frame = ctk.CTkScrollableFrame(
            self.root,
            fg_color="#0d0d1a"
        )
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.add_message("Assistant", "Hello! I am your Personal AI Assistant. How can I help you today? 😊", "#00d4ff")

        bottom_frame = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        bottom_frame.pack(fill="x", padx=0, pady=0)

        self.preview_frame = ctk.CTkFrame(bottom_frame, fg_color="#1a1a2e")
        self.preview_frame.pack(fill="x", padx=10, pady=5)
        self.preview_frame.pack_forget()

        self.preview_image_label = ctk.CTkLabel(self.preview_frame, text="")
        self.preview_image_label.pack(side="left", padx=5, pady=5)

        self.preview_text_label = ctk.CTkLabel(
            self.preview_frame,
            text="",
            text_color="#00d4ff",
            font=ctk.CTkFont(size=12)
        )
        self.preview_text_label.pack(side="left", padx=5)

        ctk.CTkButton(
            self.preview_frame,
            text="✕",
            width=25,
            height=25,
            fg_color="#ff4444",
            hover_color="#cc0000",
            command=self.remove_preview
        ).pack(side="left", padx=5)

        input_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            input_frame,
            text="+",
            width=40,
            height=40,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#2d2d4e",
            hover_color="#3d3d6e",
            command=self.show_options
        ).pack(side="left", padx=5)

        self.input_box = ctk.CTkTextbox(
            input_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#2d2d4e",
            border_color="#00d4ff",
            border_width=1
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=5)
        self.input_box.bind("<Return>", self.send_message_enter)

        ctk.CTkButton(
            input_frame,
            text="Send ➤",
            width=80,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#00d4ff",
            text_color="#000000",
            hover_color="#00a8cc",
            command=self.send_message
        ).pack(side="left", padx=5)

    def show_image_preview(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
            self.preview_image_label.configure(image=ctk_image, text="")
            self.preview_image_label.image = ctk_image
            self.pending_ctk_image = ctk_image
            self.preview_text_label.configure(text="")
            self.preview_frame.pack(fill="x", padx=10, pady=5)
        except Exception as e:
            print(f"Preview error: {e}")

    def show_doc_preview(self, doc_path):
        self.preview_image_label.configure(image=None, text="📄", font=ctk.CTkFont(size=40))
        self.preview_text_label.configure(text=f"{os.path.basename(doc_path)}")
        self.preview_frame.pack(fill="x", padx=10, pady=5)

    def remove_preview(self):
        self.selected_image_path = None
        self.pending_image_path = None
        self.selected_doc_path = None
        self.preview_frame.pack_forget()

    def add_message(self, sender, message, color="#ffffff", image_path=None, doc_name=None):
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="#1a1a2e", corner_radius=10)
        msg_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            msg_frame,
            text=sender,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color
        ).pack(anchor="w", padx=10, pady=2)

        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((400, 400))
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 400))
                img_label = ctk.CTkLabel(msg_frame, image=ctk_image, text="")
                img_label.pack(anchor="w", padx=10, pady=5)
                img_label.image = ctk_image
            except Exception as e:
                print(f"Image error: {e}")

        if doc_name:
            ctk.CTkLabel(
                msg_frame,
                text=f"📄 {doc_name}",
                font=ctk.CTkFont(size=13),
                text_color="#00d4ff"
            ).pack(anchor="w", padx=10, pady=5)

        if message:
            ctk.CTkLabel(
                msg_frame,
                text=message,
                font=ctk.CTkFont(size=13),
                text_color="#ffffff",
                wraplength=750,
                justify="left"
            ).pack(anchor="w", padx=10, pady=5)

    def show_options(self):
        options_window = ctk.CTkToplevel(self.root)
        options_window.title("Options")
        options_window.geometry("220x430")
        options_window.resizable(False, False)
        options_window.lift()
        options_window.focus_force()
        options_window.attributes("-topmost", True)

        ctk.CTkButton(
            options_window,
            text="📎 Upload Image",
            height=40,
            command=lambda: [options_window.destroy(), self.upload_image()]
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            options_window,
            text="📄 Upload Document",
            height=40,
            command=lambda: [options_window.destroy(), self.upload_document()]
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            options_window,
            text="📷 Camera",
            height=40,
            command=lambda: [options_window.destroy(), self.capture_camera()]
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            options_window,
            text="🖥️ Screenshot",
            height=40,
            command=lambda: [options_window.destroy(), self.capture_screenshot()]
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            options_window,
            text="📰 News",
            height=40,
            command=lambda: [options_window.destroy(), self.get_news_gui()]
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            options_window,
            text="🖼️ Remove Background",
            height=40,
            command=lambda: [options_window.destroy(), self.remove_bg_gui()]
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            options_window,
            text="🎨 Change Background",
            height=40,
            command=lambda: [options_window.destroy(), self.change_bg_gui()]
        ).pack(fill="x", padx=20, pady=8)

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            self.pending_image_path = file_path
            self.selected_doc_path = None
            self.show_image_preview(file_path)

    def upload_document(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Documents", "*.txt *.pdf *.docx *.csv *.py *.json *.xml *.html")]
        )
        if file_path:
            self.selected_doc_path = file_path
            self.selected_image_path = None
            self.pending_image_path = None
            self.show_doc_preview(file_path)

    def capture_camera(self):
        def camera_thread():
            cap = cv2.VideoCapture(0)
            self.add_message("Assistant", "Camera is on! Press SPACE to capture...", "#00d4ff")
            while True:
                ret, frame = cap.read()
                cv2.imshow("Camera - Press SPACE to capture", frame)
                if cv2.waitKey(1) & 0xFF == ord(' '):
                    cv2.imwrite("camera_capture.png", frame)
                    break
            cap.release()
            cv2.destroyAllWindows()
            self.selected_image_path = "camera_capture.png"
            self.pending_image_path = "camera_capture.png"
            self.root.after(0, lambda: self.show_image_preview("camera_capture.png"))

        threading.Thread(target=camera_thread, daemon=True).start()

    def capture_screenshot(self):
        self.root.iconify()
        time.sleep(1)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.png")
        self.root.deiconify()
        self.selected_image_path = "screenshot.png"
        self.pending_image_path = "screenshot.png"
        self.show_image_preview("screenshot.png")

    def get_news_gui(self):
        topic_window = ctk.CTkToplevel(self.root)
        topic_window.title("News")
        topic_window.geometry("300x150")
        topic_window.lift()
        topic_window.focus_force()
        topic_window.attributes("-topmost", True)

        ctk.CTkLabel(topic_window, text="Enter news topic:").pack(pady=10)
        topic_entry = ctk.CTkEntry(topic_window, width=200)
        topic_entry.pack(pady=5)

        def fetch_news():
            topic = topic_entry.get()
            topic_window.destroy()
            news = get_news(topic)
            self.add_message("Assistant", news, "#00d4ff")

        ctk.CTkButton(topic_window, text="Get News", command=fetch_news).pack(pady=10)

    def remove_bg_gui(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.add_message("You", "Remove background from this image", "#00ff88", image_path=file_path)
            self.add_message("Assistant", "Removing background... Please wait!", "#00d4ff")
            def process():
                result = remove_background(file_path)
                if result.endswith(".png"):
                    self.root.after(0, lambda: self.add_message(
                        "Assistant",
                        "Done! Background removed successfully! ✅",
                        "#00d4ff",
                        image_path=result
                    ))
                else:
                    self.root.after(0, lambda: self.add_message("Assistant", result, "#ff4444"))
            threading.Thread(target=process, daemon=True).start()

    def change_bg_gui(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            color_window = ctk.CTkToplevel(self.root)
            color_window.title("Choose Background Color")
            color_window.geometry("300x350")
            color_window.lift()
            color_window.focus_force()
            color_window.attributes("-topmost", True)

            ctk.CTkLabel(color_window, text="Choose background color:").pack(pady=10)

            colors = {
                "⬜ White": (255, 255, 255, 255),
                "⬛ Black": (0, 0, 0, 255),
                "🔵 Blue": (0, 0, 255, 255),
                "🔴 Red": (255, 0, 0, 255),
                "🟢 Green": (0, 255, 0, 255),
                "🟡 Yellow": (255, 255, 0, 255),
                "🟣 Purple": (128, 0, 128, 255),
                "🟠 Orange": (255, 165, 0, 255),
            }

            for color_name, color_value in colors.items():
                ctk.CTkButton(
                    color_window,
                    text=color_name,
                    height=35,
                    command=lambda cv=color_value, fp=file_path: [
                        color_window.destroy(),
                        self.process_bg_change(fp, cv)
                    ]
                ).pack(fill="x", padx=20, pady=4)

    def process_bg_change(self, file_path, color):
        self.add_message("You", "Change background color of this image", "#00ff88", image_path=file_path)
        self.add_message("Assistant", "Changing background... Please wait!", "#00d4ff")
        def process():
            result = change_background(file_path, color)
            if result.endswith(".png"):
                self.root.after(0, lambda: self.add_message(
                    "Assistant",
                    "Done! Background changed successfully! ✅",
                    "#00d4ff",
                    image_path=result
                ))
            else:
                self.root.after(0, lambda: self.add_message("Assistant", result, "#ff4444"))
        threading.Thread(target=process, daemon=True).start()

    def send_message_enter(self, event):
        if not event.state & 0x1:
            self.send_message()
            return "break"

    def send_message(self):
        user_text = self.input_box.get("1.0", "end").strip()
        if not user_text and not self.selected_image_path and not self.selected_doc_path:
            return

        self.input_box.delete("1.0", "end")

        if self.pending_image_path:
            self.add_message("You", user_text, "#00ff88", image_path=self.pending_image_path)
            self.preview_frame.pack_forget()
        elif self.selected_doc_path:
            self.add_message("You", user_text, "#00ff88", doc_name=os.path.basename(self.selected_doc_path))
            self.preview_frame.pack_forget()
        elif user_text:
            self.add_message("You", user_text, "#00ff88")

        current_image = self.selected_image_path
        current_doc = self.selected_doc_path
        self.selected_image_path = None
        self.pending_image_path = None
        self.selected_doc_path = None

        def process():
            try:
                if current_image:
                    # Detect if user wants bg action
                    action, color = detect_bg_action(user_text)

                    if action == "remove":
                        self.root.after(0, lambda: self.add_message(
                            "Assistant", "Removing background... Please wait!", "#00d4ff"
                        ))
                        result = remove_background(current_image)
                        if result.endswith(".png"):
                            self.root.after(0, lambda: self.add_message(
                                "Assistant",
                                "Done! Background removed successfully! ✅",
                                "#00d4ff",
                                image_path=result
                            ))
                        else:
                            self.root.after(0, lambda: self.add_message("Assistant", result, "#ff4444"))

                    elif action == "change":
                        if color:
                            self.root.after(0, lambda: self.add_message(
                                "Assistant", "Changing background... Please wait!", "#00d4ff"
                            ))
                            result = change_background(current_image, color)
                            if result.endswith(".png"):
                                self.root.after(0, lambda: self.add_message(
                                    "Assistant",
                                    "Done! Background changed successfully! ✅",
                                    "#00d4ff",
                                    image_path=result
                                ))
                            else:
                                self.root.after(0, lambda: self.add_message("Assistant", result, "#ff4444"))
                        else:
                            self.root.after(0, lambda: self.add_message(
                                "Assistant",
                                "Please mention the color! Example: 'change background to white'",
                                "#ff4444"
                            ))
                    else:
                        # Normal image analysis
                        question = user_text if user_text else "What do you see in this image?"
                        result = analyze_image(current_image, question)
                        self.root.after(0, lambda: self.add_message("Assistant", result, "#00d4ff"))

                    if os.path.exists("camera_capture.png"):
                        os.remove("camera_capture.png")
                    if os.path.exists("screenshot.png"):
                        os.remove("screenshot.png")

                elif current_doc:
                    question = user_text if user_text else "Please summarize this document."
                    result = analyze_document(current_doc, question)
                    self.root.after(0, lambda: self.add_message("Assistant", result, "#00d4ff"))

                else:
                    response = chat.send_message(user_text)
                    self.root.after(0, lambda: self.add_message("Assistant", response.text, "#00d4ff"))

            except Exception as e:
                self.root.after(0, lambda: self.add_message(
                    "Assistant", f"Sorry, something went wrong! {e}", "#ff4444"
                ))

        threading.Thread(target=process, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PersonalAIApp()
    app.run()
