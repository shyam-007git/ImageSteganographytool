import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from capacity import get_usage
from encoder import encode_image
from decoder import decode_image
from emailer import send_email

# ── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT       = "#4f8ef7"
ACCENT_HOVER = "#2d6be4"
SUCCESS      = "#2ecc71"
WARNING      = "#f39c12"
DANGER       = "#e74c3c"
BG_CARD      = "#1e2130"
BG_MAIN = ("#f5f5f5", "#151722")   # (light, dark)
BG_CARD = ("#ffffff", "#1e2130")
TEXT_DIM = ("#555555", "#8892a4")



# ── Helpers ───────────────────────────────────────────────────────────────────
def _bar_color(percent: float) -> str:
    if percent < 60:
        return SUCCESS
    if percent < 85:
        return WARNING
    return DANGER


# ── Main App ──────────────────────────────────────────────────────────────────
class SteganographyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔐 Steganography Tool v2")
        self.geometry("720x720")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        self.encode_image_path: str | None = None
        self.decode_image_path: str | None = None

        self._build_header()
        self._build_tabs()
        self.hash_file_path: str | None = None
    def _reset_app(self):
        # Reset stored paths
        self.encode_image_path = None
        self.decode_image_path = None

        # ── Encode Tab Reset ──
        self.enc_img_label.configure(
            text="No image selected — click Browse",
            text_color=TEXT_DIM
        )
        self.enc_preview.configure(image=None, text="")
        self.enc_preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.message_box.delete("1.0", "end")
        self.enc_password.delete(0, "end")
        self.email_entry.delete(0, "end")

        self.cap_bar.set(0)
        self.cap_label.configure(text="")

        self.enc_status.configure(text="")


        # ── Decode Tab Reset ──
        self.dec_img_label.configure(
            text="No image selected — click Browse",
            text_color=TEXT_DIM
        )
        self.dec_preview.configure(image=None, text="")
        self.dec_preview_placeholder.configure(text="Image preview will appear here")
        self.dec_preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.dec_password.delete(0, "end")

        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")

        self.integrity_label.configure(text="")
        self.hash_file_path = None
        self.hash_label.configure(
            text="No hash file selected — click Browse",
            text_color=TEXT_DIM
        )
        self.hash_input.delete(0, "end")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🔐  Steganography Tool",
            font=ctk.CTkFont(family="Courier", size=22, weight="bold"),
            text_color=ACCENT,
        ).pack(side="left", padx=24, pady=15)
        self.refresh_btn = ctk.CTkButton(
            header,
            text="♻️ Refresh",
            width=100,
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color=ACCENT,
            text_color=ACCENT,
            hover_color="#dbe0ef",
            command=self._reset_app
        )
        self.refresh_btn.pack(side="right", padx=10)

        # Dark / light toggle
        self.theme_btn = ctk.CTkButton(
            header,
            text="☀ Light",
            width=90,
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color=ACCENT,
            text_color=ACCENT,
            hover_color="#dbe0ef",
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="right", padx=24)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        container = ctk.CTkScrollableFrame(self, fg_color=BG_MAIN)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs = ctk.CTkTabview(container, fg_color=BG_MAIN,
                                segmented_button_fg_color=BG_CARD,
                                segmented_button_selected_color=ACCENT,
                                segmented_button_selected_hover_color=ACCENT_HOVER)

        self.tabs.pack(fill="both", expand=True)
            
        self.tabs.add("  Encode  ")
        self.tabs.add("  Decode  ")
        self._build_encode_tab()
        self._build_decode_tab()

    # ── Encode Tab ────────────────────────────────────────────────────────────
    def _build_encode_tab(self):
        tab = self.tabs.tab("  Encode  ")
        tab.configure(fg_color=BG_MAIN)

        # Image picker
        self._section_label(tab, "📁  Cover Image")
        img_row = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=12)
        img_row.pack(fill="x", pady=(4, 10))

        self.enc_img_label = ctk.CTkLabel(
            img_row, text="No image selected — click Browse",
            text_color=TEXT_DIM, anchor="w"
        )
        self.enc_img_label.pack(side="left", padx=14, pady=10, fill="x", expand=True)

        ctk.CTkButton(
            img_row, text="Browse", width=90,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self._browse_encode_image
        ).pack(side="right", padx=10, pady=8)

        # Image preview
        self.enc_preview = ctk.CTkLabel(
            tab, text="", fg_color=BG_CARD, corner_radius=12,
            width=680, height=160
        )
        self.enc_preview.pack(fill="x", pady=(0, 10))
        self.enc_preview_placeholder = ctk.CTkLabel(
            self.enc_preview, text="Image preview will appear here",
            text_color=TEXT_DIM
        )
        self.enc_preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # Capacity bar
        cap_row = ctk.CTkFrame(tab, fg_color="transparent")
        cap_row.pack(fill="x", pady=(0, 6))
        self._section_label(cap_row, "📊  Payload Capacity", pack_side="left")
        self.cap_label = ctk.CTkLabel(cap_row, text="", text_color=TEXT_DIM,
                                       font=ctk.CTkFont(size=12))
        self.cap_label.pack(side="right")

        self.cap_bar = ctk.CTkProgressBar(tab, height=8, corner_radius=4,
                                           progress_color=SUCCESS)
        self.cap_bar.set(0)
        self.cap_bar.pack(fill="x", pady=(0, 12))

        # Secret message
        self._section_label(tab, "✉️  Secret Message")
        self.message_box = ctk.CTkTextbox(
            tab, height=100, corner_radius=10,
            fg_color=BG_CARD, border_color=ACCENT, border_width=1,
            font=ctk.CTkFont(size=13)
        )
        self.message_box.pack(fill="x", pady=(4, 10))
        self.message_box.bind("<KeyRelease>", self._on_message_type)

        # Password
        self._section_label(tab, "🔑  Encryption Password")
        self.enc_password = ctk.CTkEntry(
            tab, placeholder_text="Enter a strong password",
            show="•", height=40, corner_radius=10,
            fg_color=BG_CARD, border_color=ACCENT, border_width=1
        )
        self.enc_password.pack(fill="x", pady=(4, 10))

        # Receiver email
        self._section_label(tab, "📧  Receiver Email  (optional — leave blank to skip)")
        self.email_entry = ctk.CTkEntry(
            tab, placeholder_text="receiver@example.com",
            height=40, corner_radius=10,
            fg_color=BG_CARD, border_color=ACCENT, border_width=1
        )
        self.email_entry.pack(fill="x", pady=(4, 14))

        # Encode button
        self.enc_btn = ctk.CTkButton(
            tab, text="🔒  Encode Image",
            height=46, corner_radius=12,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._run_encode
        )
        self.enc_btn.pack(fill="x")

        # Status
        self.enc_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=13))
        self.enc_status.pack(pady=8)
    def _browse_hash_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Hash Files", "*.hash"), ("Text Files", "*.txt")]
        )
        if path:
            self.hash_file_path = path
            name = path.split("/")[-1].split("\\")[-1]
            self.hash_label.configure(text=name, text_color="white")
     # ── Decode Tab 
     
    def _build_decode_tab(self):
        tab = self.tabs.tab("  Decode  ")
        tab.configure(fg_color=BG_MAIN)

        # Image picker
        self._section_label(tab, "📁  Encoded Image")
        img_row = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=12)
        img_row.pack(fill="x", pady=(4, 10))

        self.dec_img_label = ctk.CTkLabel(
            img_row, text="No image selected — click Browse",
            text_color=TEXT_DIM, anchor="w"
        )
        self.dec_img_label.pack(side="left", padx=14, pady=10, fill="x", expand=True)

        ctk.CTkButton(
            img_row, text="Browse", width=90,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self._browse_decode_image
        ).pack(side="right", padx=10, pady=8)
        # ── Hash File ──
        self._section_label(tab, "🔐  Hash File (optional)")

        hash_row = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=12)
        hash_row.pack(fill="x", pady=(4, 10))

        self.hash_label = ctk.CTkLabel(
            hash_row,
            text="No hash file selected — click Browse",
            text_color=TEXT_DIM,
            anchor="w"
        )
        self.hash_label.pack(side="left", padx=14, pady=10, fill="x", expand=True)

        ctk.CTkButton(
            hash_row,
            text="Browse",
            width=90,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._browse_hash_file
        ).pack(side="right", padx=10, pady=8)


        # ── OR Paste Hash ──
        self._section_label(tab, "📋  Paste Hash (optional)")

        self.hash_input = ctk.CTkEntry(
            tab,
            placeholder_text="Paste SHA-256 hash here...",
            height=40,
            corner_radius=10,
            fg_color=BG_CARD,
            border_color=ACCENT,
            border_width=1
        )
        self.hash_input.pack(fill="x", pady=(4, 10))

        # Image preview
        self.dec_preview = ctk.CTkLabel(
            tab, text="", fg_color=BG_CARD, corner_radius=12,
            width=680, height=160
        )
        self.dec_preview.pack(fill="x", pady=(0, 10))
        self.dec_preview_placeholder = ctk.CTkLabel(
            self.dec_preview, text="Image preview will appear here",
            text_color=TEXT_DIM
        )
        self.dec_preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # Password
        self._section_label(tab, "🔑  Decryption Password")
        self.dec_password = ctk.CTkEntry(
            tab, placeholder_text="Enter the password used during encoding",
            show="•", height=40, corner_radius=10,
            fg_color=BG_CARD, border_color=ACCENT, border_width=1
        )
        self.dec_password.pack(fill="x", pady=(4, 14))

        # Decode button
        self.dec_btn = ctk.CTkButton(
            tab, text="🔓  Decode Message",
            height=46, corner_radius=12,
            fg_color="#1a7a4a", hover_color="#0f5233",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._run_decode
        )
        self.dec_btn.pack(fill="x")

        # Integrity status
        self.integrity_label = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=13))
        self.integrity_label.pack(pady=(8, 4))

        # Result box
        self._section_label(tab, "📄  Decoded Message")
        self.result_box = ctk.CTkTextbox(
            tab, height=180, corner_radius=10,
            fg_color=BG_CARD, border_color="#2a3050", border_width=1,
            font=ctk.CTkFont(size=13), state="disabled"
        )
        self.result_box.pack(fill="x", pady=(4, 0))

    # ── UI Helpers ────────────────────────────────────────────────────────────
    def _section_label(self, parent, text: str, pack_side="top"):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_DIM, anchor="w"
        ).pack(side=pack_side, anchor="w", pady=(4, 0))

    def _set_preview(self, path: str, preview_widget: ctk.CTkLabel,
                     placeholder: ctk.CTkLabel):
        try:
            img = Image.open(path)
            img.thumbnail((680, 160))
            photo = ctk.CTkImage(img, size=img.size)
            placeholder.place_forget()
            preview_widget.configure(image=photo, text="")
            preview_widget._image = photo          # prevent GC
        except Exception:
            pass

    # ── Browse ────────────────────────────────────────────────────────────────
    def _browse_encode_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
        )
        if path:
            self.encode_image_path = path
            name = path.split("/")[-1].split("\\")[-1]
            self.enc_img_label.configure(text=name, text_color="white")
            self._set_preview(path, self.enc_preview, self.enc_preview_placeholder)
            self._on_message_type()          # refresh capacity

    def _browse_decode_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("PNG Files", "*.png")]
        )
        if path:
            self.decode_image_path = path
            name = path.split("/")[-1].split("\\")[-1]
            self.dec_img_label.configure(text=name, text_color="white")
            self._set_preview(path, self.dec_preview, self.dec_preview_placeholder)

    # ── Live Capacity ─────────────────────────────────────────────────────────
    def _on_message_type(self, event=None):
        if not self.encode_image_path:
            return
        message = self.message_box.get("1.0", "end").strip()
        try:
            used, capacity, percent = get_usage(message, self.encode_image_path)
        except Exception:
            return

        self.cap_bar.set(percent / 100)
        self.cap_bar.configure(progress_color=_bar_color(percent))
        self.cap_label.configure(
            text=f"{used} / {capacity} chars  ({percent}%)",
            text_color=_bar_color(percent)
        )

    # ── Encode ────────────────────────────────────────────────────────────────
    def _run_encode(self):
        if not self.encode_image_path:
            messagebox.showerror("Error", "Please select a cover image.")
            return
        message = self.message_box.get("1.0", "end").strip()
        password = self.enc_password.get().strip()
        if not message:
            messagebox.showerror("Error", "Please enter a secret message.")
            return
        if not password:
            messagebox.showerror("Error", "Please enter an encryption password.")
            return

        self.enc_btn.configure(state="disabled", text="⏳  Encoding…")
        self.enc_status.configure(text="", text_color=TEXT_DIM)
        threading.Thread(
            target=self._encode_thread,
            args=(message, password, self.email_entry.get().strip()),
            daemon=True
        ).start()

    def _encode_thread(self, message: str, password: str, email: str):
        try:
            output = encode_image(self.encode_image_path, message, password)
            status_text = f"✅  Saved → {output}"

            if email:
                send_email(email, output)
                status_text += f"  |  📧 Emailed to {email}"

            self.after(0, lambda: self._encode_done(status_text, success=True))
        except Exception as exc:
            self.after(0, lambda: self._encode_done(str(exc), success=False))

    def _encode_done(self, text: str, success: bool):
        self.enc_btn.configure(state="normal", text="🔒  Encode Image")
        color = SUCCESS if success else DANGER
        self.enc_status.configure(text=text, text_color=color)
        if success:
            messagebox.showinfo("Success", "Image encoded successfully!")
        else:
            messagebox.showerror("Error", text)

    
# ── Decode ────────────────────────────────────────────────────────────────
    
    def _run_decode(self):
        if not self.decode_image_path:
            messagebox.showerror("Error", "Please select an encoded image.")
            return
        password = self.dec_password.get().strip()
        if not password:
            messagebox.showerror("Error", "Please enter the decryption password.")
            return

        self.dec_btn.configure(state="disabled", text="⏳  Decoding…")
        self.integrity_label.configure(text="")
        threading.Thread(
            target=self._decode_thread, args=(password,), daemon=True
        ).start()
    def _decode_thread(self, password: str):
        try:
            # 🔓 Decode message first
            message = decode_image(self.decode_image_path, password)

            integrity_ok = None  # default = skipped

            # 🔐 Optional integrity check
            try:
                stored_hash = None

                if self.hash_file_path:
                    with open(self.hash_file_path, "r") as f:
                        stored_hash = f.read().strip()

                else:
                    hash_value = self.hash_input.get().strip()
                    if hash_value:
                        stored_hash = hash_value

                if stored_hash:
                    if len(stored_hash) != 64:
                        raise ValueError("Invalid hash format.")

                    from integrity import verify_integrity
                    integrity_ok = verify_integrity(
                        stored_hash,
                        self.decode_image_path
                    )

            except:
                integrity_ok = None  # don't break decoding

            self.after(0, lambda: self._decode_done(message, integrity_ok))

        except Exception as exc:
            self.after(0, lambda: self._decode_error(str(exc)))
            

    def _decode_done(self, message: str, integrity_ok: bool | None):
        self.dec_btn.configure(state="normal", text="🔓  Decode Message")

        if integrity_ok is True:
            self.integrity_label.configure(
                text="✅ Integrity verified — image is safe.",
                text_color=SUCCESS
            )

        elif integrity_ok is False:
            self.integrity_label.configure(
                text="⚠️ Image may have been modified!",
                text_color=WARNING
            )

        else:
            self.integrity_label.configure(
                text="ℹ️ Integrity check skipped.",
                text_color=TEXT_DIM
            )

        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", message)
        self.result_box.configure(state="disabled")        
  

    def _decode_error(self, error: str):
        self.dec_btn.configure(state="normal", text="🔓  Decode Message")
        self.integrity_label.configure(text=f"❌  {error}", text_color=DANGER)
        messagebox.showerror("Error", error)

    # ── Theme Toggle ──────────────────────────────────────────────────────────
    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="🌙 Dark")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="☀ Light")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SteganographyApp()
    app.mainloop()