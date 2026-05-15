
    # --- THÊM MỚI: HÀM CẬP NHẬT TEXT HƯỚNG DẪN ---
    def update_guide_text():
        """
        (ĐÃ VIẾT LẠI) 
        1. Cập nhật text hướng dẫn.
        2. Kiểm tra file khởi chạy và Ẩn/Hiện nút "Khởi chạy".
        """
        global g_current_launch_path, g_all_mods_flat, g_launch_game_button, path_entry

        # 1. ẨN NÚT (Mặc định) VÀ RESET PATH
        # (Nút sẽ được hiện lại ở Bước 5 nếu file tồn tại)
        if 'g_launch_game_button' in globals():
            g_launch_game_button.pack_forget()
            
        if 'g_set_path_button' in globals():
            try:
                g_set_path_button.pack_forget()
            except tk.TclError:
                pass
        g_current_launch_path = None 

        try:
            guide_text_widget.config(state=tk.NORMAL) # Mở khóa để sửa
            guide_text_widget.delete("1.0", tk.END) # Xóa text cũ

            selected_key = selected_option.get()

            # 2. KIỂM TRA XEM CÓ CHỌN MOD KHÔNG
            if selected_key and selected_key in g_all_mods_flat:

                # 3. LẤY DATA
                selected_option_data = g_all_mods_flat[selected_key] 

                # 4. CẬP NHẬT HƯỚNG DẪN PATH
                raw_guide = selected_option_data.get("path_guide")
                if raw_guide:
                    guide_text = str(raw_guide) # Đảm bảo là string
                else:
                    guide_text = "Không có hướng dẫn cho mod này."
                guide_text_widget.insert(tk.END, guide_text)

                # 5. KIỂM TRA FILE KHỞI CHẠY (LOGIC MỚI)
                if 'game_launchers' in local_config:
                    found_launch_file = local_config['game_launchers'].get(g_current_game_name)
                    if found_launch_file:
                        print(f"Đã tìm thấy launch file do người dùng cài đặt: {found_launch_file}")


                # Ưu tiên 2: Lấy từ JSON (nếu local không có)
                if not found_launch_file:
                    mod_list = download_options.get(g_current_game_name, [])
                    for _key, mod_data in mod_list:
                        if mod_data.get("launch_file"):
                            found_launch_file = mod_data.get("launch_file")
                            print(f"Đã tìm thấy launch file từ JSON: {found_launch_file}")
                            break # Lấy file đầu tiên tìm thấy

                destination_folder = local_config.get("game_paths", {}).get(g_current_game_name, "")

                # 6. Kiểm tra file (logic không đổi, chỉ đổi tên biến)
                # Chỉ kiểm tra nếu:
                # - Tìm thấy một "launch_file"
                # - Ô đường dẫn không rỗng
                # - Đường dẫn là một thư mục có thật
                if found_launch_file and destination_folder and os.path.isdir(destination_folder):

                    full_file_path = os.path.join(destination_folder, found_launch_file)

                    # Nếu tìm thấy file...
                    if os.path.exists(full_file_path) and os.path.isfile(full_file_path):
                        print(f"Persistent Check (Page 2): Tìm thấy file khởi chạy: {full_file_path}")
                        g_current_launch_path = full_file_path
                    else:
                        # (Debug) Báo nếu đã cấu hình nhưng không tìm thấy file
                        print(f"Persistent Check (Page 2): Đã cấu hình '{found_launch_file}' nhưng không tìm thấy tại '{destination_folder}'")

            else:
                # (Nếu không có mod nào được chọn)
                guide_text_widget.insert(tk.END, "Hãy chọn một mod ở trên để xem hướng dẫn...")

        except Exception as e:
            print(f"Lỗi khi cập nhật hướng dẫn/launch button: {e}")
            guide_text_widget.delete("1.0", tk.END)
            guide_text_widget.insert(tk.END, "Lỗi khi tải hướng dẫn.")
        finally:
            guide_text_widget.config(state=tk.DISABLED)
            try:
                # --- [SỬA ĐỔI: ĐỔI THỨ TỰ PACK] ---
                
                # 1. Pack nút "Đặt đường dẫn" (⚙️) TRƯỚC 
                # -> Kết quả: Nó sẽ nằm ở NGOÀI CÙNG BÊN PHẢI
                if 'g_set_path_button' in globals():
                    g_set_path_button.pack(side=tk.RIGHT, padx=(0, 5)) 

                # 2. Pack nút "Chạy Game" (🚀) SAU
                # -> Kết quả: Nó sẽ nằm bên TRÁI nút bánh răng
                if 'g_launch_game_button' in globals():
                    g_launch_game_button.pack(side=tk.RIGHT, padx=(0, 10)) 
                    
                    # Cấu hình trạng thái (ENABLE/DISABLE)
                    if g_current_launch_path:
                        g_launch_game_button.config(state=tk.NORMAL)
                    else:
                        g_launch_game_button.config(state=tk.DISABLED)

            except Exception as e:
                print(f"Lỗi khi pack nút bên phải: {e}")
            # --- (END) THAY ĐỔI ---


    def on_game_search(event):
        """Lọc lưới game ở Trang 1 dựa trên nội dung ô tìm kiếm."""
        if not g_game_search_entry: # Nếu UI chưa sẵn sàng
            return

        search_term = g_game_search_entry.get().lower()

        # Gọi lại hàm populate, truyền vào dict đã nhóm và từ khóa
        populate_page_1_grid(download_options, search_term)

    # --- THÊM MỚI: HÀM XÓA TÌM KIẾM (BỊ THIẾU) ---
    def action_clear_game_search():
        """Xóa ô tìm kiếm và hiển thị lại tất cả game."""
        if not g_game_search_entry:
            return
        g_game_search_entry.delete(0, tk.END) # Xóa text

        # Gọi lại hàm populate với search_term rỗng
        # (Lưu ý: 'download_options' là biến toàn cục)
        populate_page_1_grid(download_options, search_term="")

    def action_delete_custom_game(game_name):
        """Xóa game custom khỏi danh sách."""
        if custom_askyesno("Xóa Game", f"Bạn có chắc chắn muốn xóa game '{game_name}' khỏi danh sách không?\n(File game trên máy sẽ KHÔNG bị xóa)."):
            try:
                # Xóa khỏi config
                if game_name in local_config['custom_games']:
                    del local_config['custom_games'][game_name]
                    save_local_config(local_config)
                    
                    # Làm mới lưới
                    action_clear_game_search()
                    custom_showinfo("Đã xóa", f"Đã xóa '{game_name}'.")
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể xóa: {e}")

    def action_change_game_image(game_name, is_custom):
        """Đổi ảnh bìa cho game (Cả Custom và Server)."""
        new_url = custom_askstring("Đổi Ảnh", f"Nhập URL hình ảnh mới cho '{game_name}':")
        
        if not new_url: return
        
        try:
            # 1. Tải ảnh về
            response = requests.get(new_url, timeout=10)
            response.raise_for_status()
            img_data = response.content
            
            # 2. Tạo tên file cache an toàn
            safe_name = "".join([c for c in game_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            img_filename = f"override_{safe_name}.png"
            local_img_path = os.path.join(g_cache_dir, img_filename)
            
            # 3. Resize và Lưu
            if not os.path.exists(g_cache_dir): os.makedirs(g_cache_dir)
            
            with Image.open(io.BytesIO(img_data)) as img:
                # Lưu bản chất lượng cao (460x215)
                img_resized = img.resize((460, 215), Image.Resampling.LANCZOS)
                img_resized.save(local_img_path, "PNG")
                
            # 4. Lưu đường dẫn vào Config
            if is_custom:
                # Nếu là game custom, cập nhật trực tiếp vào custom_games
                local_config['custom_games'][game_name]['image_local_path'] = local_img_path
            else:
                # Nếu là game server, lưu vào theme_overrides
                if 'theme_overrides' not in local_config:
                    local_config['theme_overrides'] = {}
                local_config['theme_overrides'][game_name] = local_img_path
                
            save_local_config(local_config)
            
            # 5. Xóa cache RAM cũ để nó load ảnh mới
            keys_to_remove = [k for k in root.cached_images.keys() if safe_name in k or game_name in k]
            for k in keys_to_remove:
                del root.cached_images[k]

            # 6. Làm mới giao diện
            action_clear_game_search()
            custom_showinfo("Thành công", "Đã cập nhật ảnh bìa!")

        except Exception as e:
            custom_showerror("Lỗi", f"Không thể tải ảnh: {e}")

    def action_rename_game(game_key):
        """Đổi tên hiển thị của game (Alias)."""
        # Lấy tên hiện tại (nếu đã đổi thì lấy tên đổi, chưa thì lấy tên gốc)
        current_alias = local_config.get('display_name_overrides', {}).get(game_key, game_key)
        
        new_name = custom_askstring("Đổi Tên", f"Nhập tên mới cho '{game_key}':", initialvalue=current_alias)
        
        if new_name is not None: # Nếu không bấm Cancel
            if not new_name.strip() or new_name.strip() == game_key:
                # Nếu để trống hoặc nhập trùng tên gốc -> Xóa Alias (Reset)
                if game_key in local_config['display_name_overrides']:
                    del local_config['display_name_overrides'][game_key]
            else:
                # Lưu tên mới
                local_config['display_name_overrides'][game_key] = new_name.strip()
                
            save_local_config(local_config)
            action_clear_game_search() # Làm mới giao diện

    def action_change_resolution(game_key):
        """Mở popup chọn độ phân giải cho Custom Game."""
        # 1. Tạo cửa sổ
        dialog = tk.Toplevel(root)
        dialog.title(f"Resolution - {game_key}")
        center_window_on_screen(dialog, 350, 200)
        dialog.transient(root)
        dialog.grab_set()
        
        # Theme cho titlebar
        dialog.after(10, lambda: apply_theme_to_titlebar(dialog))

        ttk.Label(dialog, text="Chọn độ phân giải khởi động (16:9):", font=("Segoe UI", 10)).pack(pady=15)

        # 2. Danh sách Resolution 16:9 phổ biến
        res_options = [
            "Mặc định (Theo Game)",
            "1280x720  (HD)",
            "1366x768  (Laptop)",
            "1600x900  (HD+)",
            "1920x1080 (Full HD)",
            "2560x1440 (2K)",
            "3840x2160 (4K)"
        ]

        # Lấy giá trị hiện tại
        current_res = "Mặc định (Theo Game)"
        if 'custom_games' in local_config and game_key in local_config['custom_games']:
            saved_res = local_config['custom_games'][game_key].get('resolution', "")
            if saved_res:
                # Tìm text khớp với saved_res (ví dụ "1920x1080")
                for opt in res_options:
                    if saved_res in opt:
                        current_res = opt
                        break

        combo = ttk.Combobox(dialog, values=res_options, state="readonly", width=30)
        combo.pack(pady=5)
        combo.set(current_res)

        def on_save():
            selection = combo.get()
            
            # Trích xuất độ phân giải (VD: Lấy "1920x1080" từ "1920x1080 (Full HD)")
            res_val = ""
            if "x" in selection:
                res_val = selection.split(" ")[0] # Lấy phần đầu tiên trước dấu cách

            # Lưu vào config
            if 'custom_games' in local_config and game_key in local_config['custom_games']:
                local_config['custom_games'][game_key]['resolution'] = res_val
                save_local_config(local_config)
                
                if res_val:
                    custom_showinfo("Đã lưu", f"Game sẽ chạy ở độ phân giải: {res_val}\n(Lưu ý: Game phải hỗ trợ tham số dòng lệnh -screen-width / -w)")
                else:
                    custom_showinfo("Đã lưu", "Đã reset về mặc định của game.")
                    
                dialog.destroy()

        ttk.Button(dialog, text="Lưu Thiết Lập", command=on_save, style="Accent.TButton").pack(pady=20)

    def action_remove_custom_image(game_key):
        """Xóa ảnh custom để quay về ảnh gốc từ Server."""
        if custom_askyesno("Khôi phục ảnh", f"Bạn muốn xóa ảnh tùy chỉnh của '{game_key}'\nvà quay lại dùng ảnh gốc từ Server?"):
            try:
                # Xóa khỏi config
                if game_key in local_config['theme_overrides']:
                    del local_config['theme_overrides'][game_key]
                    save_local_config(local_config)
                
                # Xóa cache RAM để nó load lại ảnh gốc
                # (Tìm các key cache chứa tên game và xóa)
                safe_name = "".join([c for c in game_key if c.isalnum() or c in (' ', '-', '_')]).strip()
                keys_to_del = [k for k in root.cached_images.keys() if safe_name in k]
                for k in keys_to_del:
                    del root.cached_images[k]
                    
                action_clear_game_search() # Làm mới giao diện
                custom_showinfo("Thành công", "Đã khôi phục ảnh gốc.")
                
            except Exception as e:
                custom_showerror("Lỗi", f"Lỗi khi xóa ảnh: {e}")

    # --- CẤU HÌNH STICKER / TAG ---
    GAME_TAGS_CONFIG = {
        # Tên Game chính xác : Loại Tag (HOT, GOTY, NEW, UPD, BEST)
        "The Spell Brigade": "HOT",
        "Elden Ring": "GOTY",
        "Risk of Rain 2": "UPD",
        "Clair Obscur: Expedition 33": "GOTY",
        "Black Myth: Wukong": "BEST"
    }

    # Định nghĩa màu sắc cho từng loại Tag
    TAG_COLORS = {
        "HOT":  ("#ff4d4d", "white"),   # Đỏ / Trắng
        "GOTY": ("#ffd700", "black"),   # Vàng Gold / Đen
        "NEW":  ("#4cff00", "black"),   # Xanh Neon / Đen
        "UPD":  ("#4a90e2", "white"),   # Xanh Dương / Trắng
        "BEST": ("#9b59b6", "white"),   # Tím / Trắng
        "FIX ":  ("#57606f", "white")
    }

    def get_tag_badge_icon(tag_text, height=14):
        """
        Vẽ icon nhãn dán (Badge) bằng vector.
        """
        # --- [SỬA LỖI] THÊM IMPORT VÀO ĐÂY ---
        
        # -------------------------------------

        bg_color, txt_color = TAG_COLORS.get(tag_text, ("#555555", "white"))
        
        # Tạo key cache để không phải vẽ lại nhiều lần
        cache_key = f"tag_badge_{tag_text}_{height}"
        if cache_key in root.cached_images:
            return root.cached_images[cache_key]

        # Tính toán kích thước dựa trên độ dài chữ
        width = len(tag_text) * 7 + 8 
        
        # Tạo ảnh trong suốt
        img = Image.new("RGBA", (width, height), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        # Vẽ hình chữ nhật bo góc (Badge)
        draw.rounded_rectangle((0, 0, width, height), radius=3, fill=bg_color)
        
        # Vẽ chữ
        try:
            # Cố gắng load font nhỏ
            font = ImageFont.truetype("arial.ttf", 9) # Font size 9
        except:
            # Nếu lỗi font hệ thống thì dùng font mặc định
            font = ImageFont.load_default()

        # Căn giữa chữ
        try:
            bbox = draw.textbbox((0, 0), tag_text, font=font)
            w_text = bbox[2] - bbox[0]
            h_text = bbox[3] - bbox[1]
        except:
            w_text = len(tag_text) * 5
            h_text = 8
            
        x_text = (width - w_text) / 2
        y_text = (height - h_text) / 2 - 1 

        draw.text((x_text, y_text), tag_text, fill=txt_color, font=font)
        
        tk_img = ImageTk.PhotoImage(img)
        root.cached_images[cache_key] = tk_img
        return tk_img

    def get_ctx_icon(name, color, size=20):
        """
        (V2) Tạo icon vector bằng PIL.ImageDraw.
        Hỗ trợ: edit, image, folder, delete, restore, trash, gear, download, save, disk, check, warning, question.
        """
        # Tạo key cache bao gồm cả tên, màu và kích thước
        key = f"ctx_icon_{name}_{color}_{size}"
        
        if key in root.cached_images: 
            return root.cached_images[key]
        
        # Tạo ảnh trong suốt
        img = Image.new("RGBA", (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        # Tính toán tọa độ tỉ lệ theo size
        c = size // 2 # Tâm
        s = size      # Cạnh
        
        # --- NHÓM 1: CÁC ICON CŨ (MENU) ---
        if name == "edit": # Bút chì
            p = int(s*0.2)
            draw.line((s-p, p, p, s-p), fill=color, width=2)
            draw.polygon([(p, s-p), (p-1, s-1), (p+3, s-2)], fill=color)
            
        elif name == "image": # Khung ảnh
            p = int(s*0.15)
            draw.rectangle((p, p, s-p, s-p), outline=color, width=2)
            draw.polygon([(p, s-p), (c, c), (s-p, s-p)], fill=color)
            
        elif name == "folder": # Thư mục
            p = int(s*0.1)
            draw.polygon([(p, s*0.3), (s*0.4, s*0.3), (s*0.5, s*0.4), (s-p, s*0.4), (s-p, s-p), (p, s-p)], outline=color, width=2)
            draw.line((p, s*0.45, s-p, s*0.45), fill=color, width=1)
            
        elif name == "screen": # Màn hình
            p = int(s*0.15)
            draw.rectangle((p, p, s-p, s*0.7), outline=color, width=2)
            draw.line((c, s*0.7, c, s-p), fill=color, width=2)
            draw.line((c-4, s-p, c+4, s-p), fill=color, width=2)

        elif name == "delete": # Dấu X mảnh
            p = int(s*0.25)
            draw.line((p, p, s-p, s-p), fill=color, width=2)
            draw.line((p, s-p, s-p, p), fill=color, width=2)
            
        elif name == "restore": # Mũi tên quay lại
            draw.arc((s*0.2, s*0.2, s*0.8, s*0.8), 20, 280, fill=color, width=2)
            draw.polygon([(s*0.2, s*0.3), (s*0.2, s*0.5), (s*0.05, s*0.3)], fill=color)
        
        elif name == "trash": # Thùng rác
            draw.rectangle((s*0.3, s*0.35, s*0.7, s*0.85), outline=color, width=2)
            draw.line((s*0.2, s*0.25, s*0.8, s*0.25), fill=color, width=2)
            draw.line((s*0.4, s*0.15, s*0.6, s*0.15), fill=color, width=2)

        elif name == "gear": # Bánh răng
            draw.ellipse((s*0.25, s*0.25, s*0.75, s*0.75), outline=color, width=2)
            import math
            for i in range(8):
                angle = math.radians(i * 45)
                x1 = c + (s*0.2) * math.cos(angle)
                y1 = c + (s*0.2) * math.sin(angle)
                x2 = c + (s*0.45) * math.cos(angle)
                y2 = c + (s*0.45) * math.sin(angle)
                draw.line((x1, y1, x2, y2), fill=color, width=2)

        # --- NHÓM 2: CÁC ICON MỚI (CHO DOWNLOAD CONFIRM) ---
        elif name == "download": # Mũi tên xuống + gạch ngang
            p = int(s*0.2)
            # Thân
            draw.line((c, p, c, s-p-3), fill=color, width=2)
            # Đầu mũi tên
            draw.line((c, s-p-3, c-4, s-p-7), fill=color, width=2)
            draw.line((c, s-p-3, c+4, s-p-7), fill=color, width=2)
            # Gạch đáy
            draw.line((p, s-p, s-p, s-p), fill=color, width=2)

        elif name == "save": # Đĩa mềm (Tượng trưng Tổng dung lượng)
            p = int(s*0.15)
            draw.rectangle((p, p, s-p, s-p), outline=color, width=2)
            # Thanh trượt
            draw.rectangle((p+4, p, s-p-4, p+5), fill=color)
            # Nhãn
            draw.rectangle((p+3, s-p-5, s-p-3, s-p), outline=color)

        elif name == "disk": # Ổ đĩa (Vòng tròn Pie Chart)
            p = int(s*0.15)
            draw.ellipse((p, p, s-p, s-p), outline=color, width=2)
            draw.ellipse((c-2, c-2, c+2, c+2), fill=color)

        elif name == "check": # Dấu tích V (Đậm)
            points = [(s*0.2, s*0.5), (s*0.45, s*0.75), (s*0.85, s*0.25)]
            draw.line(points, fill=color, width=3, joint="curve")

        elif name == "warning": # Tam giác chấm than
            points = [(c, s*0.1), (s*0.1, s*0.9), (s*0.9, s*0.9)]
            draw.polygon(points, outline=color, width=2)
            draw.line((c, s*0.35, c, s*0.65), fill=color, width=2)
            draw.point((c, s*0.75), fill=color)

        elif name == "question": # Dấu hỏi
            # Dùng font mặc định để vẽ dấu hỏi cho đẹp
            try:
                # Load font mặc định kích thước lớn
                from PIL import ImageFont
                # Cố gắng load font Segoe UI hoặc Arial, nếu không thì default
                try: font = ImageFont.truetype("seguiemj.ttf", int(size*0.8))
                except: font = ImageFont.load_default()
                
                # Căn giữa text
                draw.text((c, c), "?", font=font, fill=color, anchor="mm")
            except:
                # Fallback nếu lỗi font: Vẽ thủ công đơn giản
                draw.ellipse((s*0.2, s*0.1, s*0.8, s*0.6), outline=color, width=2)
                draw.line((c, s*0.6, c, s*0.8), fill=color, width=2)

        tk_img = ImageTk.PhotoImage(img)
        root.cached_images[key] = tk_img
        return tk_img

    def show_game_context_menu(target, game_key, is_custom):
        """
        Hiển thị menu ngữ cảnh (Đã thêm: Xóa file chạy).
        """
        menu = tk.Menu(root, tearoff=0)
        
        # --- 1. CÁC MỤC CƠ BẢN ---
        menu.add_command(
            label="Đổi Tên Game", 
            image=get_ctx_icon("edit", "#FFD700"), # Gold
            compound=tk.LEFT,
            command=lambda: action_rename_game(game_key)
        )
        
        menu.add_command(
            label="Đổi Ảnh (URL)", 
            image=get_ctx_icon("image", "#00FFFF"), # Cyan
            compound=tk.LEFT,
            command=lambda: action_change_game_image(game_key, is_custom)
        )
        
        # --- QUẢN LÝ FILE CHẠY ---
        menu.add_separator()
        
        # Chọn file
        menu.add_command(
            label="Chọn file khởi chạy",  # <-- Đã xóa chữ (.exe)
            image=get_ctx_icon("folder", "#F0E68C"),
            compound=tk.LEFT,
            command=action_set_game_path_from_page_2
        )

        # [MỚI] Xóa file
        menu.add_command(
            label="Xóa file chạy", 
            image=get_ctx_icon("delete", "#FFA500"), # Orange
            compound=tk.LEFT,
            command=lambda: action_clear_game_exe(game_key)
        )

        # --- KHÔI PHỤC ẢNH ---
        if not is_custom and game_key in local_config.get('theme_overrides', {}):
            menu.add_separator()
            menu.add_command(
                label="Khôi phục Ảnh Gốc", 
                image=get_ctx_icon("restore", "#FFFFFF"), 
                compound=tk.LEFT,
                command=lambda: action_remove_custom_image(game_key)
            )

        # --- MENU CHO CUSTOM GAME ---
        if is_custom:
            menu.add_separator()
            
            menu.add_command(
                label="Chỉnh Resolution (16:9)", 
                image=get_ctx_icon("screen", "#87CEFA"), # LightBlue
                compound=tk.LEFT,
                command=lambda: action_change_resolution(game_key)
            )
            
            menu.add_command(
                label="Xóa Game Khỏi List", 
                image=get_ctx_icon("delete", "#FF6347"), # Tomato (Đỏ)
                compound=tk.LEFT,
                command=lambda: action_delete_custom_game(game_key)
            )
            
        # Xử lý tọa độ (như cũ)
        try:
            x = target.x_root
            y = target.y_root
        except AttributeError:
            try:
                x = target.winfo_rootx()
                y = target.winfo_rooty() + target.winfo_height()
            except:
                x = root.winfo_pointerx()
                y = root.winfo_pointery()

        menu.post(x, y)

    def on_page_1_mouse_wheel(event):
        """Hàm cuộn CHUYÊN BIỆT cho Trang 1 (Tránh xung đột với Tab 2)."""
        global page_1_canvas
        try:
            if not page_1_canvas.winfo_exists(): return
            
            scroll_amount = 0
            if sys.platform == "win32":
                scroll_amount = int(-1 * (event.delta / 120))
            elif sys.platform == "darwin": # macOS
                scroll_amount = event.delta
            else: # Linux
                if event.num == 4: scroll_amount = -1
                elif event.num == 5: scroll_amount = 1
            
            page_1_canvas.yview_scroll(scroll_amount, "units")
        except Exception as e:
            pass

    def populate_page_1_grid(game_groups, search_term=""):
        """
        [STEAM UI CATEGORIZED] Giao diện chia 3 mục: MY GAMES, INSTALLED, LIBRARY.
        """
        global g_game_search_entry, page_1_canvas
        global g_steam_sidebar_frame, g_steam_detail_frame
        global g_selected_game_label 
        global path_entry, g_mod_buttons, g_current_selected_key, selected_option
        global g_launch_game_button 
        global g_auto_add_exclusion

        # --- 0. STYLE & CLEANUP ---
        style.configure("SteamPlay.TButton", background="#4cff00", foreground="black", font=("Segoe UI", 12, "bold"), padding=(20, 10))
        style.map("SteamPlay.TButton", background=[('active', '#66ff33'), ('disabled', '#3d4d3d')], foreground=[('disabled', '#888888')])
        style.configure("InstallMod.TButton", background="#0078d4", foreground="white", font=("Segoe UI", 11, "bold"))
        
        # Style cho Header danh mục (Mới)
        style.configure("Category.TLabel", background="#191919", foreground="#8a8a8a", font=("Segoe UI", 9, "bold"))
        style.configure("CategoryHover.TLabel", foreground="#ffffff")

        if 'g_tab1_loading_frame' in globals() and g_tab1_loading_frame:
            try: g_tab1_loading_frame.destroy()
            except: pass
        
        for widget in page_1_game_grid.winfo_children(): widget.destroy()

        # --- 1. LAYOUT CHÍNH (GRID 3:7) ---
        main_layout = tk.Frame(page_1_game_grid, bg="#191919")
        main_layout.pack(fill=tk.BOTH, expand=True)
        main_layout.columnconfigure(0, weight=3, uniform="group1") 
        main_layout.columnconfigure(1, weight=7, uniform="group1")
        main_layout.rowconfigure(0, weight=1)
        
        # === CỘT TRÁI: SIDEBAR ===
        sidebar_container = tk.Frame(main_layout, bg="#191919")
        sidebar_container.grid(row=0, column=0, sticky="nsew")

        # --- [CẬP NHẬT] FOOTER: NÚT GEMINI + STICKER ---
        sidebar_footer = tk.Frame(sidebar_container, bg="#191919", pady=10, padx=10)
        sidebar_footer.pack(side=tk.BOTTOM, fill=tk.X)

        # [MỚI] Nút Refresh Dữ Liệu
        # Style dùng chung với nút Gemini hoặc dùng Accent cho nổi bật
        global btn_refresh_data # Khai báo global để có thể điều khiển từ xa nếu cần
        btn_refresh_data = ttk.Button(
            sidebar_footer, 
            text="🔄 Làm Mới Dữ Liệu", 
            command=action_refresh_data,
            style="Accent.TButton" 
        )
        # Pack lên trên nút Gemini, cách một chút (pady)
        btn_refresh_data.pack(fill=tk.X, ipady=3, pady=(0, 5))
        # Thêm tooltip cho chuyên nghiệp
        CreateToolTip(btn_refresh_data, "Tải lại danh sách Game và Config mới nhất từ GitHub.")

        # 1. Style cho nút (Giữ nguyên)
        style.configure("Gemini.TButton", 
                        font=("Segoe UI", 11, "bold"), 
                        foreground="#00FFFF") 
        style.map("Gemini.TButton",
                foreground=[('active', '#FFFFFF'), ('pressed', '#00CCCC')],
                background=[('active', '#333333')]) 

        # 2. Tạo nút
        gemini_full_btn = ttk.Button(
            sidebar_footer,
            text="✨Google Gemini Pro",
            command=action_open_gemini_pro,
            style="Gemini.TButton"
        )
        gemini_full_btn.pack(fill=tk.X, ipady=5)

        # 3. [MỚI] TẠO STICKER "MIỄN PHÍ"
        # Dùng tk.Label thường để dễ chỉnh màu nền (bg)
        badge = tk.Label(
            sidebar_footer,
            text="MIỄN PHÍ",
            bg="#FF3333",       # Màu đỏ tươi (Red Badge)
            fg="white",         # Chữ trắng
            font=("Segoe UI", 7, "bold"), # Font nhỏ, đậm
            padx=5, pady=0,     # Đệm bên trong cho đẹp
            bd=0                # Không viền
        )
        
        # Dùng place để "dán" đè lên góc phải trên của Footer
        # relx=1.0: Sát lề phải
        # rely=0.0: Sát lề trên
        # x=-5, y=0: Dịch vào trong một chút cho cân đối
        badge.place(in_=gemini_full_btn, relx=1.0, rely=0.0, anchor="ne", x=0, y=-4)

        # Quan trọng: Click vào sticker cũng kích hoạt lệnh mở Gemini
        badge.bind("<Button-1>", lambda e: action_open_gemini_pro())
        # Cho chuột biến hình bàn tay khi trỏ vào sticker
        badge.bind("<Enter>", lambda e: badge.config(cursor="hand2"))
        
        # ----------------------------------------------

        # --- FIX SCROLL SIDEBAR (CỘT TRÁI) ---
        def on_sidebar_scroll(event):
            scroll_amount = int(-1 * (event.delta / 120)) if sys.platform == "win32" else event.delta
            list_canvas.yview_scroll(scroll_amount, "units")

        def _bind_sidebar_scroll(event):
            list_canvas.bind_all("<MouseWheel>", on_sidebar_scroll)
            list_canvas.bind_all("<Button-4>", on_sidebar_scroll)
            list_canvas.bind_all("<Button-5>", on_sidebar_scroll)

        def _unbind_sidebar_scroll(event):
            list_canvas.unbind_all("<MouseWheel>")
            list_canvas.unbind_all("<Button-4>")
            list_canvas.unbind_all("<Button-5>")

        # Chỉ kích hoạt cuộn khi chuột nằm trong vùng Sidebar Container
        sidebar_container.bind("<Enter>", _bind_sidebar_scroll)
        sidebar_container.bind("<Leave>", _unbind_sidebar_scroll)

        # Search Bar
        # Tạo Frame nền đen đóng vai trò là viền của ô tìm kiếm
        search_frame = tk.Frame(sidebar_container, bg="#191919", pady=10, padx=8)
        search_frame.pack(fill=tk.X)

        # Container cho ô nhập liệu (Mô phỏng Input field có icon)
        # bg="#252526": Màu nền của ô input (xám hơn nền sidebar một chút)
        input_container = tk.Frame(search_frame, bg="#252526")
        input_container.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3) # ipady để tăng chiều cao

        # 1. Icon Search (🔍)
        # Dùng Label để hiện icon, đặt bên trái cùng
        lbl_search_icon = tk.Label(input_container, text="🔍", bg="#252526", fg="#8a8a8a", font=("Segoe UI", 10))
        lbl_search_icon.pack(side=tk.LEFT, padx=(5, 2))

        # 2. Ô Nhập Liệu
        # borderwidth=0 để bỏ viền mặc định, hòa nhập vào container
        g_game_search_entry = tk.Entry(input_container, bg="#252526", fg="white", 
                                    insertbackground="white", # Màu con trỏ nhấp nháy
                                    relief=tk.FLAT, font=("Segoe UI", 10))
        g_game_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bind phím Enter
        g_game_search_entry.bind("<Return>", on_game_search)
        if search_term: g_game_search_entry.insert(0, search_term)

        # 3. Nút Xóa (✖) - Chỉ hiện khi có text (hoặc luôn hiện để clear)
        if search_term:
            btn_clear = tk.Label(input_container, text="✖", bg="#252526", fg="#8a8a8a", cursor="hand2")
            btn_clear.pack(side=tk.RIGHT, padx=5)
            btn_clear.bind("<Button-1>", lambda e: action_clear_game_search())
            # Hiệu ứng hover cho nút X
            btn_clear.bind("<Enter>", lambda e: btn_clear.config(fg="white"))
            btn_clear.bind("<Leave>", lambda e: btn_clear.config(fg="#8a8a8a"))

        # Nút Thêm Game (+) nằm ngoài ô search
        add_btn = tk.Button(search_frame, text="➕", command=action_add_custom_game_popup,
                            bg="#191919", fg="#4cff00", bd=0, font=("Segoe UI", 14), cursor="hand2")
        add_btn.pack(side=tk.LEFT, padx=(5, 0))
        CreateToolTip(add_btn, "Thêm Game Ngoài")
        
        # List Canvas
        list_canvas = tk.Canvas(sidebar_container, bg="#191919", highlightthickness=0)
        list_scrollbar = ttk.Scrollbar(sidebar_container, orient="vertical", command=list_canvas.yview)
        g_steam_sidebar_frame = tk.Frame(list_canvas, bg="#191919")
        
        list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        list_canvas.configure(yscrollcommand=list_scrollbar.set)
        list_canvas.create_window((0, 0), window=g_steam_sidebar_frame, anchor="nw", width=280)

        def on_sidebar_scroll(event):
            scroll_amount = int(-1 * (event.delta / 120)) if sys.platform == "win32" else event.delta
            list_canvas.yview_scroll(scroll_amount, "units")

        g_steam_sidebar_frame.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
        list_canvas.bind("<Configure>", lambda e: list_canvas.itemconfig(list_canvas.find_all()[0], width=e.width))
        list_canvas.bind_all("<MouseWheel>", on_sidebar_scroll)

        # === CỘT PHẢI: MAIN CONTENT ===
        content_container = ttk.Frame(main_layout)
        content_container.grid(row=0, column=1, sticky="nsew")

        detail_canvas = tk.Canvas(content_container, highlightthickness=0, bg="#181818")
        detail_scrollbar = ttk.Scrollbar(content_container, orient="vertical", command=detail_canvas.yview)
        g_steam_detail_frame = tk.Frame(detail_canvas, bg="#181818")
        
        detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        detail_window_id = detail_canvas.create_window((0, 0), window=g_steam_detail_frame, anchor="nw")

        g_steam_detail_frame.bind("<Configure>", lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all")))
        detail_canvas.bind("<Configure>", lambda e: detail_canvas.itemconfig(detail_window_id, width=e.width))
        # --- FIX SCROLL DETAIL (CỘT PHẢI) ---
        def on_detail_scroll(event):
            # Hàm thực hiện cuộn Canvas bên phải
            try:
                scroll_amount = int(-1 * (event.delta / 120)) if sys.platform == "win32" else event.delta
                detail_canvas.yview_scroll(scroll_amount, "units")
            except: pass

        def _bind_detail_scroll(event):
            # Khi chuột VÀO vùng phải: Bắt sự kiện cuộn cho Canvas phải
            detail_canvas.bind_all("<MouseWheel>", on_detail_scroll)
            detail_canvas.bind_all("<Button-4>", on_detail_scroll)
            detail_canvas.bind_all("<Button-5>", on_detail_scroll)

        def _unbind_detail_scroll(event):
            # Khi chuột RA KHỎI vùng phải: Gỡ bỏ sự kiện (để nhường cho bên trái)
            detail_canvas.unbind_all("<MouseWheel>")
            detail_canvas.unbind_all("<Button-4>")
            detail_canvas.unbind_all("<Button-5>")

        # Gắn sự kiện: Chỉ khi chuột nằm trong content_container thì mới cuộn được
        content_container.bind("<Enter>", _bind_detail_scroll)
        content_container.bind("<Leave>", _unbind_detail_scroll)
        # --- 2. LOGIC HIỂN THỊ CHI TIẾT ---
        # --- CÁC HÀM HỖ TRỢ GALLERY ---

        def close_trailer_player(banner_frame, hero_canvas, close_btn):
            """Đóng video player và hiện lại gallery ảnh."""
            # Xóa widget WebView2 (nếu có)
            for widget in banner_frame.winfo_children():
                if isinstance(widget, tk.Frame) and widget != hero_canvas: # WebView2 thường là Frame con
                    widget.destroy()
                if "webview" in str(widget).lower(): # Kiểm tra tên widget để chắc chắn
                    widget.destroy()
                    
            # Ẩn nút đóng
            if close_btn:
                close_btn.place_forget()
                
            # Hiện lại Canvas
            hero_canvas.pack(fill=tk.X, expand=True)

        def play_trailer_embedded(banner_frame, hero_canvas, url, close_btn):
            """Ẩn Canvas và nhúng WebView2 vào banner_frame để chạy video."""
            game_name = "Night Reign" 
            trailer_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Thay bằng link thật

            if trailer_link:
                print(f"Đang mở trailer: {game_name}")
                trailer_manager.play(trailer_link, f"Trailer: {game_name}")
            else:
                messagebox.showinfo("Thông báo", "Game này chưa có trailer!")

        def update_hero_gallery(canvas, media_list, current_index, raw_banner_pil):
            """Vẽ nội dung lên hero_canvas (Ảnh/Video Thumbnail)."""
            canvas.delete("all")
            if not media_list: return

            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width < 10: width = 800
            if height < 10: height = 450
            
            current_item = media_list[current_index]
            item_type = current_item.get("type", "image")
            
            # VẼ NỀN (IMAGE)
            display_pil = raw_banner_pil
            if display_pil:
                try:
                    img_w, img_h = display_pil.size
                    ratio = width / img_w
                    new_h = int(img_h * ratio)
                    resized_pil = display_pil.resize((width, new_h), Image.Resampling.LANCZOS)
                    if new_h > height:
                        resized_pil = resized_pil.crop((0, 0, width, height))
                    
                    # Làm tối ảnh nếu là Video để nút Play nổi hơn
                    if item_type == "video":
                        overlay = Image.new('RGBA', resized_pil.size, (0, 0, 0, 100))
                        resized_pil = resized_pil.convert('RGBA')
                        resized_pil = Image.alpha_composite(resized_pil, overlay)
                    
                    tk_img = ImageTk.PhotoImage(resized_pil)
                    canvas.image = tk_img
                    canvas.create_image(0, 0, anchor="nw", image=tk_img)
                except Exception as e:
                    pass

            # VẼ NÚT PLAY (NẾU LÀ VIDEO)
            if item_type == "video":
                cx, cy = width // 2, height // 2
                size = 40
                canvas.create_oval(cx-size, cy-size, cx+size, cy+size, outline="white", width=3)
                canvas.create_polygon(cx-10, cy-15, cx-10, cy+15, cx+15, cy, fill="white", outline="white")
                canvas.create_text(cx, cy + size + 25, text="XEM TRAILER", font=("Segoe UI", 12, "bold"), fill="white")

            # VẼ NÚT ĐIỀU HƯỚNG
            if len(media_list) > 1:
                canvas.create_text(30, height//2, text="❮", font=("Segoe UI", 30), fill="white", tags="btn_prev", activefill="#4cc2ff")
                canvas.create_text(width-30, height//2, text="❯", font=("Segoe UI", 30), fill="white", tags="btn_next", activefill="#4cc2ff")
                
                # Pagination Dots
                total_w = len(media_list) * 20
                start_x = (width - total_w) // 2
                for i in range(len(media_list)):
                    fill_color = "white" if i == current_index else "gray"
                    x = start_x + i * 20
                    canvas.create_oval(x, height-30, x+10, height-20, fill=fill_color, outline="")

        def on_hero_click(event, canvas, media_list, current_index_ref, banner_frame, close_btn):
            """Xử lý click: Điều hướng hoặc Chạy Trailer."""
            width = canvas.winfo_width()
            clicked_item = canvas.find_closest(event.x, event.y)
            tags = canvas.gettags(clicked_item)
            
            is_prev = "btn_prev" in tags or (event.x < 60)
            is_next = "btn_next" in tags or (event.x > width - 60)
            
            if len(media_list) > 1:
                if is_prev:
                    current_index_ref[0] = (current_index_ref[0] - 1) % len(media_list)
                    return "update"
                elif is_next:
                    current_index_ref[0] = (current_index_ref[0] + 1) % len(media_list)
                    return "update"

            # Click vào nội dung
            current_item = media_list[current_index_ref[0]]
            if current_item.get("type") == "video":
                url = current_item.get("url")
                if url:
                    # GỌI HÀM PLAY EMBEDDED THAY VÌ MỞ TRÌNH DUYỆT
                    play_trailer_embedded(banner_frame, canvas, url, close_btn)
            
            return None


        # (Copy lại logic thread load ảnh từ code cũ của bạn vào đây)
        def load_and_draw_on_canvas(url, next_url=None):
            global g_pil_image_cache
            try:
                # Kiểm tra canvas tồn tại
                if 'hero_canvas' not in globals() or not hero_canvas.winfo_exists(): return

                # --- LẤY KÍCH THƯỚC CANVAS ---
                cw = hero_canvas.winfo_width()
                ch = hero_canvas.winfo_height()
                if cw < 50: cw = 880 # Kích thước mặc định nếu chưa load xong
                if ch < 50: ch = 450

                # --- HÀM CON: Tải ảnh ---
                def get_pil_image(img_url):
                    if not img_url: return None
                    if img_url in g_pil_image_cache: return g_pil_image_cache[img_url]
                    try:
                        img = None
                        if img_url.startswith(("http:", "https:")):
                            res = requests.get(img_url, timeout=5)
                            img = Image.open(BytesIO(res.content))
                        elif os.path.exists(img_url):
                            img = Image.open(img_url)
                        if img: g_pil_image_cache[img_url] = img
                        return img
                    except: return None

                # 1. Tải và xử lý ẢNH NỀN CHÍNH
                pil_main = get_pil_image(url)
                tk_main = None
                if pil_main:
                    # Resize kiểu Aspect Fill
                    orig_w, orig_h = pil_main.size
                    ratio = max(cw / orig_w, ch / orig_h)
                    new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                    img_resized = pil_main.copy().resize((new_w, new_h), Image.Resampling.LANCZOS)
                    # Crop giữa
                    left, top = (new_w - cw)//2, (new_h - ch)//2
                    tk_main = ImageTk.PhotoImage(img_resized.crop((left, top, left + cw, top + ch)))

                # 2. Tải và xử lý ẢNH PREVIEW (Góc phải)
                tk_preview = None
                has_multiple_images = (next_url and next_url != url)
                
                if has_multiple_images:
                    pil_next = get_pil_image(next_url)
                    if pil_next:
                        # Thumbnail 160x90
                        pil_next_small = pil_next.copy().resize((160, 90), Image.Resampling.LANCZOS)
                        # Thêm viền trắng vào chính ảnh bitmap để đảm bảo nổi bật
                        draw = ImageDraw.Draw(pil_next_small)
                        draw.rectangle([0, 0, 159, 89], outline="white", width=3)
                        tk_preview = ImageTk.PhotoImage(pil_next_small)

                # --- 3. CẬP NHẬT UI (Main Thread) ---
                def _update_ui():
                    if not hero_canvas.winfo_exists(): return
                    hero_canvas.delete("all") # Xóa sạch cũ

                    # A. Vẽ nền (Layer dưới cùng)
                    if tk_main:
                        hero_canvas.create_image(0, 0, image=tk_main, anchor="nw", tags="bg")
                        hero_canvas.image = tk_main # Giữ tham chiếu

                    # Nếu chỉ có 1 ảnh thì dừng, không vẽ nút/preview
                    if not has_multiple_images: return

                    # B. Vẽ Nút "NEXT" (Layer UI)
                    # Vị trí Preview: Góc phải dưới, cách lề 20px
                    p_w, p_h = 160, 90
                    p_x = cw - p_w - 20
                    p_y = ch - p_h - 20

                    if tk_preview:
                        # 1. Vẽ khung nền đen mờ phía sau chữ Next
                        hero_canvas.create_rectangle(p_x, p_y - 25, p_x + p_w, p_y, 
                                                fill="#000000", stipple="gray50", outline="", tags="ui")
                        # 2. Chữ "NEXT SLIDE"
                        hero_canvas.create_text(p_x + 5, p_y - 12, text="TIẾP THEO ▶", 
                                            fill="#00ffff", font=("Arial", 9, "bold"), anchor="w", tags="ui")
                        # 3. Ảnh Preview
                        hero_canvas.create_image(p_x, p_y, image=tk_preview, anchor="nw", tags="ui")
                        hero_canvas.preview_ref = tk_preview # Giữ tham chiếu

                    # # C. Vẽ Vùng Click (Nút vô hình hoặc bán trong suốt 2 bên)
                    # # Nút Phải (Next)
                    # hero_canvas.create_rectangle(cw-100, 0, cw, ch, fill="", outline="", tags=("btn_next", "ui"))
                    # # Mũi tên phải (Visual)
                    # hero_canvas.create_text(cw-30, ch//2, text="›", font=("Arial", 50), fill="white", tags=("btn_next", "ui"))
                    
                    # # Nút Trái (Prev)
                    # hero_canvas.create_rectangle(0, 0, 100, ch, fill="", outline="", tags=("btn_prev", "ui"))
                    # # Mũi tên trái (Visual)
                    # hero_canvas.create_text(30, ch//2, text="‹", font=("Arial", 50), fill="white", tags=("btn_prev", "ui"))

                    # # D. Gắn sự kiện Click
                    # hero_canvas.tag_bind("btn_next", "<Button-1>", lambda e: manual_change_slide(1))
                    # hero_canvas.tag_bind("btn_prev", "<Button-1>", lambda e: manual_change_slide(-1))
                    
                    # Click vào Preview cũng Next luôn
                    hero_canvas.tag_bind("ui", "<Button-1>", lambda e: manual_change_slide(1))

                    # E. Đảm bảo UI nổi lên trên cùng
                    hero_canvas.tag_raise("ui")

                hero_canvas.after(0, _update_ui)

            except Exception as e:
                print(f"Lỗi vẽ canvas: {e}")
        # ------------------------------------------
        # Hàm tiếp theo là hàm bạn đã có (để ngay dưới hàm trên)
        # ------------------------------------------

        def update_slideshow_loop():
            """Vòng lặp slideshow: Tính toán logic và gọi hàm vẽ."""
            global g_slideshow_job, g_slideshow_index, g_slideshow_urls

            if not g_slideshow_urls: 
                print("Slideshow: Không có URL nào.")
                return

            # Lấy URL hiện tại
            current_url = g_slideshow_urls[g_slideshow_index]
            
            # Tính URL kế tiếp (để làm Preview)
            next_index = (g_slideshow_index + 1) % len(g_slideshow_urls)
            next_url = g_slideshow_urls[next_index]

            # Gọi hàm vẽ (Chạy luồng riêng để mượt)
            threading.Thread(target=lambda: load_and_draw_on_canvas(current_url, next_url), daemon=True).start()

            # Hẹn giờ cho lần chuyển tiếp theo (4 giây)
            # Lưu ý: Chỉ hẹn giờ nếu có nhiều hơn 1 ảnh
            if len(g_slideshow_urls) > 1:
                g_slideshow_job = root.after(2000, update_slideshow_loop)

        def manual_change_slide(direction):
            """Hàm chuyển ảnh khi bấm nút: direction = 1 (Next) hoặc -1 (Prev)"""
            global g_slideshow_job, g_slideshow_index, g_slideshow_urls
            
            # Hủy hẹn giờ tự động hiện tại để tránh xung đột
            if g_slideshow_job:
                root.after_cancel(g_slideshow_job)
                g_slideshow_job = None

            if not g_slideshow_urls: return

            # Tính index mới
            new_index = (g_slideshow_index + direction) % len(g_slideshow_urls)
            g_slideshow_index = new_index
            
            # Cập nhật ngay lập tức
            update_slideshow_loop()

        def start_game_slideshow(game_name):
            """
            Phiên bản hỗ trợ Custom Game (Theo cấu trúc JSON mới).
            Thứ tự tìm kiếm: Server JSON -> Local Config (image_local_path/original_url) -> Default.
            """
            global g_slideshow_job, g_slideshow_urls, g_slideshow_index
            global g_game_themes, local_config 
            
            # 1. Hủy job cũ
            if g_slideshow_job:
                try: root.after_cancel(g_slideshow_job)
                except: pass
                g_slideshow_job = None
                
            g_slideshow_urls = []
            g_slideshow_index = 0

            # --- LOGIC TÌM ẢNH ---
            
            # CÁCH 1: Tìm trong Server (g_game_themes) - Game có sẵn
            server_data = g_game_themes.get(game_name)
            
            if server_data:
                if isinstance(server_data, dict):
                    # Ưu tiên lấy list slideshow
                    g_slideshow_urls = server_data.get("slideshow", [])
                    # Fallback nếu list rỗng, lấy image lẻ (nếu có key này)
                    if not g_slideshow_urls and server_data.get("image"):
                        g_slideshow_urls = [server_data.get("image")]
                elif isinstance(server_data, str):
                    g_slideshow_urls = [server_data]
                    
            # CÁCH 2: Tìm trong Custom Games (Game thêm bên ngoài)
            # Cấu trúc: local_config["custom_games"][game_name]
            if not g_slideshow_urls:
                custom_games_dict = local_config.get("custom_games", {})
                
                # Kiểm tra xem game_name có nằm trong custom_games không
                if game_name in custom_games_dict:
                    game_info = custom_games_dict[game_name]
                    
                    # Ưu tiên 1: Lấy đường dẫn file nội bộ (image_local_path)
                    local_path = game_info.get("image_local_path")
                    
                    # Ưu tiên 2: Lấy URL gốc (original_url) nếu chưa tải xong local
                    original_url = game_info.get("original_url")
                    
                    # Logic chọn: Dùng local nếu file tồn tại, nếu không thì dùng URL
                    if local_path and os.path.exists(local_path):
                        g_slideshow_urls = [local_path]
                    elif original_url:
                        g_slideshow_urls = [original_url]

            # CÁCH 3: Nếu vẫn rỗng -> Dùng ảnh Mặc Định
            if not g_slideshow_urls:
                g_slideshow_urls = [DEFAULT_HERO_IMAGE]

            # -------------------------

            # Kích hoạt hiển thị
            if g_slideshow_urls:
                # Gọi ngay lập tức để hiện ảnh
                threading.Thread(target=lambda: load_and_draw_on_canvas(g_slideshow_urls[0]), daemon=True).start()
                
                # Nếu có nhiều ảnh (Game Server) thì mới loop
                if len(g_slideshow_urls) > 1:
                    g_slideshow_index = 1 
                    g_slideshow_job = root.after(2000, update_slideshow_loop)

        def update_hero_canvas_image(tk_img=None):
            """
            Hàm fallback: Xử lý khi không có ảnh để hiển thị trong slideshow.
            Vẽ một nền đen thay thế.
            """
            if 'hero_canvas' not in globals() or not hero_canvas.winfo_exists():
                return

            # Xóa nội dung cũ
            hero_canvas.delete("all")
            
            # Lấy kích thước canvas
            w = hero_canvas.winfo_width()
            h = hero_canvas.winfo_height()
            if w < 10: w = 780
            if h < 10: h = 450

            if tk_img:
                # Nếu có ảnh tĩnh được truyền vào trực tiếp
                hero_canvas.create_image(0, 0, image=tk_img, anchor="nw")
                hero_canvas.image = tk_img
            else:
                # Nếu không có ảnh (None), vẽ nền đen
                hero_canvas.create_rectangle(0, 0, w, h, fill="#1e1e1e", outline="#1e1e1e")

        # --- THAY THẾ HÀM show_steam_details ---
        def show_steam_details(game_name):
            global g_current_game_name, local_config, path_entry
            global g_mod_buttons, g_current_selected_key, selected_option
            global g_launch_game_button
            global hero_canvas
            g_current_game_name = game_name
            local_config = load_local_config()
            g_mod_buttons = {}
            selected_option.set("")

            # Xóa nội dung cũ
            for w in g_steam_detail_frame.winfo_children():
                w.destroy()

            is_custom = game_name in local_config.get('custom_games', {})
            
            # 1. Dữ liệu Theme & Media
            theme_data = g_game_themes.get(game_name)
            image_url = ""
            trailer_url = ""
            
            if isinstance(theme_data, dict):
                image_url = theme_data.get("image", "")
                trailer_url = theme_data.get("trailer", "")
            elif isinstance(theme_data, str):
                image_url = theme_data

            override_path = local_config.get('theme_overrides', {}).get(game_name)
            if is_custom:
                override_path = local_config['custom_games'][game_name].get("image_local_path")
            
            # Load Banner Image
            raw_banner_pil = None
            if override_path and os.path.exists(override_path):
                try: raw_banner_pil = Image.open(override_path)
                except: pass
            
            if not raw_banner_pil and image_url:
                try:
                    import hashlib
                    cache_key = f"{image_url}_460x215"
                    hashed_name = hashlib.sha256(cache_key.encode('utf-8')).hexdigest() + ".png"
                    cache_path = os.path.join(g_cache_dir, hashed_name)
                    if os.path.exists(cache_path):
                        raw_banner_pil = Image.open(cache_path)
                except: pass

            if not raw_banner_pil:
                try: raw_banner_pil = Image.open(resource_path("logo.png"))
                except: raw_banner_pil = Image.new('RGB', (800, 450), color='#181818')

            # Media List
            media_list = [{"type": "image", "data": raw_banner_pil}]
            if trailer_url:
                media_list.append({"type": "video", "url": trailer_url})

            gallery_state = [0] 

            # 2. Xây dựng Giao diện
            
            # --- BANNER AREA (Chứa cả Canvas và Video Player) ---
            banner_frame = tk.Frame(g_steam_detail_frame, bg="#181818", height=450)
            banner_frame.pack(fill=tk.X, anchor="n")
            banner_frame.pack_propagate(False)

            # Canvas (Hiển thị mặc định)
            hero_canvas = tk.Canvas(banner_frame, bg="#181818", highlightthickness=0)
            hero_canvas.pack(fill=tk.BOTH, expand=True)
            # Nút này sẽ được place() khi video chạy

            # --- CÁC PHẦN CÒN LẠI (PLAY BAR, CONTENT) ---
            # (Phần này giữ nguyên code cũ của bạn, tôi copy lại để đảm bảo tính toàn vẹn)

            play_bar_frame = tk.Frame(g_steam_detail_frame, bg="#252526", height=80, padx=30, pady=15)
            play_bar_frame.pack(fill=tk.X)

            full_path_to_launch = None
            current_path_folder = local_config.get("game_paths", {}).get(game_name, "")
            if not current_path_folder:
                current_path_folder = local_config.get("last_used_folder", "")

            if is_custom:
                full_path_to_launch = local_config['custom_games'][game_name].get("launch_path")
            else:
                found_launch_file = local_config.get('game_launchers', {}).get(game_name)
                if not found_launch_file and 'download_options' in globals():
                    mod_list_data = download_options.get(game_name, [])
                    for _key, mod_data in mod_list_data:
                        if mod_data.get("launch_file"):
                            found_launch_file = mod_data.get("launch_file")
                            break
                
                if found_launch_file and current_path_folder and os.path.isdir(current_path_folder):
                    full_path = os.path.join(current_path_folder, found_launch_file)
                    if os.path.exists(full_path):
                        full_path_to_launch = full_path

            g_launch_game_button = ttk.Button(play_bar_frame, text="🚀 Chạy Game ", style="Big.Accent.TButton")
            g_launch_game_button.pack(side=tk.LEFT, ipady=5, ipadx=15)
            
            if full_path_to_launch:
                g_launch_game_button.config(state=tk.NORMAL, command=lambda: action_launch_game_from_page_1(full_path_to_launch, g_launch_game_button))
            else:
                g_launch_game_button.config(state=tk.DISABLED, text="Chưa Cài Đặt")

            gear_btn = ttk.Button(play_bar_frame, image=get_ctx_icon("gear", "white"), text="", width=3)
            gear_btn.configure(command=lambda: show_game_context_menu(gear_btn, game_name, is_custom))
            gear_btn.pack(side=tk.RIGHT, padx=5)

            if full_path_to_launch or (current_path_folder and os.path.exists(current_path_folder)):
                uninstall_btn = ttk.Button(play_bar_frame, image=get_ctx_icon("trash", "#ff4d4d"), text="", width=3, style="TButton")
                uninstall_btn.configure(command=lambda: action_uninstall_game_logic(game_name))
                uninstall_btn.pack(side=tk.RIGHT, padx=(0, 5))
                CreateToolTip(uninstall_btn, "Gỡ cài đặt game")

            content_frame = tk.Frame(g_steam_detail_frame, bg="#181818", padx=30, pady=20)
            content_frame.pack(fill=tk.BOTH, expand=True)

            path_group = tk.LabelFrame(content_frame, text="📂 Vị Trí Cài Đặt", bg="#181818", fg="white", padx=10, pady=10)
            path_group.pack(fill=tk.X, pady=(0, 20))
            
            path_entry = ttk.Entry(path_group)
            path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            path_entry.insert(0, current_path_folder)
            ttk.Button(path_group, text="Chọn đường dẫn...", command=browse_for_folder).pack(side=tk.LEFT, padx=5)

            mod_group = tk.LabelFrame(content_frame, text="📦 Các bản Cài đặt / Mod", bg="#181818", fg="white", padx=10, pady=10)
            mod_group.pack(fill=tk.BOTH, expand=True)

            mod_list_data = download_options.get(game_name, [])
            if not mod_list_data:
                tk.Label(mod_group, text="Hiện không có cài đặt nào", bg="#181818", fg="gray").pack(pady=20)
            else:
                for i, (key, data) in enumerate(mod_list_data):
                    mod_name = data.get("name", key)
                    mod_ver = data.get("version", "v?")
                    installed_ver = local_config.get("installed_versions", {}).get(key, "Not installed")
                    
                    card = tk.Frame(mod_group, bg="#252526", pady=10, padx=10)
                    card.pack(fill=tk.X, pady=2)
                    
                    status_icon = "✔" if mod_ver == installed_ver else "⬇"
                    chk_btn = tk.Button(card, text=status_icon, bg="#252526", fg="white", width=4, bd=0, cursor="hand2")
                    chk_btn.pack(side=tk.LEFT, fill=tk.Y)
                    
                    info_frame = tk.Frame(card, bg="#252526", padx=10)
                    info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    tk.Label(info_frame, text=mod_name, fg="white", bg="#252526", font=("Segoe UI", 11, "bold"), anchor="w").pack(fill=tk.X)
                    ver_text = f"Version: {mod_ver}" + (f" (Installed: {installed_ver})" if installed_ver != "Not installed" else "")
                    tk.Label(info_frame, text=ver_text, fg="#8b929a", bg="#252526", font=("Segoe UI", 9), anchor="w").pack(fill=tk.X)
                    
                    g_mod_buttons[key] = (chk_btn, card)
                    def on_mod_click(k=key):
                        selected_option.set(k)
                        for mk, (mb, mc) in g_mod_buttons.items():
                            if mk == k: mc.config(bg="#3d4450"); mb.config(bg="#4cff00", fg="black")
                            else: mc.config(bg="#252526"); mb.config(bg="#3d4450", fg="white")
                    chk_btn.config(command=on_mod_click)
                    card.bind("<Button-1>", lambda e, k=key: on_mod_click(k))
                    info_frame.bind("<Button-1>", lambda e, k=key: on_mod_click(k))
                    for child in info_frame.winfo_children(): child.bind("<Button-1>", lambda e, k=key: on_mod_click(k))
                if mod_list_data: g_mod_buttons[mod_list_data[0][0]][0].invoke()

            action_bar = tk.Frame(content_frame, bg="#181818", pady=20)
            action_bar.pack(fill=tk.X)
            if 'g_auto_add_exclusion' not in globals():
                global g_auto_add_exclusion
                g_auto_add_exclusion = tk.BooleanVar(value=False)
            def_chk = ttk.Checkbutton(action_bar, text="🛡️ Auto-Exclusion (Defender)", variable=g_auto_add_exclusion, style="Switch.TCheckbutton")
            def_chk.pack(side=tk.LEFT)
            dl_btn = ttk.Button(action_bar, text="Bắt Đầu Tải Và Cài Đặt", style="Accent.TButton", command=start_download_thread)
            dl_btn.pack(side=tk.RIGHT, ipadx=20, ipady=5)
            start_game_slideshow(game_name)

        global g_show_steam_details
        g_show_steam_details = show_steam_details
        # --- 3. LOGIC SIDEBAR & SELECTION ---
        g_selected_game_label = None
        
        def on_select_game(game_name, widget_frame):
            global g_selected_game_label
            if g_selected_game_label:
                try: g_selected_game_label.config(bg="#191919")
                except: pass
            widget_frame.config(bg="#3d4450")
            g_selected_game_label = widget_frame
            show_steam_details(game_name)

        # --- HELPER: VẼ 1 ITEM GAME (ICON 16:9) ---
        def render_sidebar_item(parent_frame, game_name, is_custom):
            icon_img = None
            
            # Kích thước mục tiêu: 16:9 (Rộng 64, Cao 36)
            TARGET_SIZE = (64, 36) 

            # 1. Thử lấy từ Cache Local
            try:
                override_path = local_config.get('theme_overrides', {}).get(game_name)
                if is_custom: override_path = custom_games_data.get(game_name, {}).get("image_local_path")
                
                if override_path and os.path.exists(override_path):
                    cache_key = f"wide_{override_path}"
                    if cache_key in root.cached_images: 
                        icon_img = root.cached_images[cache_key]
                    else:
                        with Image.open(override_path) as img:
                            img_resized = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                            icon_img = ImageTk.PhotoImage(img_resized)
                            root.cached_images[cache_key] = icon_img
            except: pass
            
            # 2. Thử lấy từ URL Server
            if not icon_img and not is_custom:
                raw_data = g_game_themes.get(game_name)
                image_url = ""
                
                if isinstance(raw_data, dict):
                    slides = raw_data.get("slideshow", [])
                    if slides and len(slides) > 0:
                        image_url = slides[0]
                    elif raw_data.get("image"):
                        image_url = raw_data.get("image")
                    
                elif isinstance(raw_data, str):
                    image_url = raw_data
                    
                if image_url:
                    # Bây giờ dòng này sẽ hoạt động vì g_image_cache đã được khai báo
                    if image_url in g_image_cache: 
                        icon_img = g_image_cache[image_url]
                    else:
                        icon_img = load_image_from_url(image_url, size=TARGET_SIZE)
                        # Lưu vào cache để lần sau dùng lại
                        if icon_img:
                            g_image_cache[image_url] = icon_img

            # 3. Fallback
            if not icon_img: 
                if "default_wide" not in root.cached_images:
                    try:
                        def_pil = Image.open(resource_path("logo.png"))
                        def_resized = def_pil.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                        root.cached_images["default_wide"] = ImageTk.PhotoImage(def_resized)
                    except: pass
                icon_img = root.cached_images.get("default_wide", root.default_game_icon_small)

            # --- VẼ UI ITEM ---
            item_frame = tk.Frame(parent_frame, bg="#191919", cursor="hand2", padx=5, pady=2)
            item_frame.pack(fill=tk.X)

            # Container cho Icon (để dễ place sticker)
            icon_container = tk.Label(item_frame, image=icon_img, bg="#191919", bd=0)
            icon_container.image = icon_img 
            icon_container.pack(side=tk.LEFT)

            # --- [MỚI] LOGIC DÁN STICKER ---
            # Kiểm tra xem game này có Tag trong cấu hình không
            tag_type = None
        
            # 1. Ưu tiên tìm Tag trong Custom Game
            if is_custom:
                # (Bạn cần thêm key 'tag' vào custom_games nếu muốn hỗ trợ tag cho game ngoài)
                pass 
            
            # 2. Tìm Tag trong các Options tải
            mod_list = download_options.get(game_name, [])
            for _key, mod_data in mod_list:
                if mod_data.get("tag"):
                    tag_type = mod_data.get("tag")
                    break # Lấy tag của mod đầu tiên tìm thấy
            
            # -----------------------------------
            # --- Code MỚI (Hỗ trợ Emoji Màu) ---
            if tag_type:
                # 1. Lấy màu sắc từ cấu hình (TAG_COLORS)
                # Nếu không tìm thấy tag trong danh sách, mặc định là Xám/Trắng
                bg_color, txt_color = TAG_COLORS.get(tag_type, ("#444444", "white"))

                # 2. Tạo Label Text thay vì Image
                # Font "Segoe UI Emoji" là chìa khóa để hiện icon màu trên Windows
                badge_lbl = tk.Label(
                    item_frame, 
                    text=tag_type, 
                    font=("Segoe UI Emoji", 8, "bold"), 
                    bg=bg_color, 
                    fg=txt_color,
                    bd=0,       # Không viền
                    padx=4,     # Đệm ngang (tạo độ rộng)
                    pady=0      # Đệm dọc
                )
                
                # 3. Dán đè lên góc trái trên của icon
                badge_lbl.place(in_=icon_container, x=-2, y=-2)
                
                # (Tùy chọn) Gắn sự kiện click vào badge cũng chọn game
                badge_lbl.bind("<Button-1>", lambda e: on_select_game(game_name, item_frame))
            # -------------------------------

            display_name = local_config.get('display_name_overrides', {}).get(game_name, game_name)
            fg_col = "#a3cf06" if is_custom else "#bfbfbf"
            
            # Highlight nếu đang chọn
            bg_item = "#3d4450" if g_current_game_name == game_name else "#191919"
            if g_current_game_name == game_name:
                global g_selected_game_label
                g_selected_game_label = item_frame # Cập nhật biến toàn cục

            item_frame.config(bg=bg_item)
            icon_container.config(bg=bg_item)

            l_name = tk.Label(item_frame, text=display_name, bg=bg_item, fg=fg_col, font=("Segoe UI", 10), anchor="w")
            l_name.pack(side=tk.LEFT, padx=(10,0), fill=tk.X, expand=True)

            # Bind Events (Gắn sự kiện click cho cả sticker nếu lỡ bấm vào)
            cmd = lambda e, g=game_name, w=item_frame: on_select_game(g, w)
            
            item_frame.bind("<Button-1>", cmd)
            l_name.bind("<Button-1>", cmd)
            icon_container.bind("<Button-1>", cmd)
            
            # Hover Effect
            def on_enter(e):
                if item_frame != g_selected_game_label:
                    item_frame.config(bg="#2c2c2c")
                    icon_container.config(bg="#2c2c2c")
                    l_name.config(bg="#2c2c2c")
            
            def on_leave(e):
                if item_frame != g_selected_game_label:
                    item_frame.config(bg="#191919")
                    icon_container.config(bg="#191919")
                    l_name.config(bg="#191919")

            item_frame.bind("<Enter>", on_enter)
            item_frame.bind("<Leave>", on_leave)
            
            return item_frame

        # --- HELPER: CHECK INSTALLED (CẬP NHẬT) ---
        def is_game_installed(g_name):
            # 1. Kiểm tra phiên bản mod đã cài (Logic cũ)
            mods = game_groups.get(g_name, [])
            for key, _ in mods:
                if key in local_config.get("installed_versions", {}):
                    return True
            
            # 2. [MỚI] Kiểm tra xem đã set đường dẫn .exe chưa
            # Nếu có đường dẫn trong config -> Coi như đã cài đặt
            if 'game_paths' in local_config:
                path = local_config['game_paths'].get(g_name)
                # Chỉ cần có đường dẫn và thư mục tồn tại là tính
                if path and os.path.exists(path):
                    return True
                    
            return False
        
        # --- MAIN LOOP: PHÂN LOẠI & VẼ ---
        server_games = sorted(game_groups.keys())
        custom_games_data = local_config.get('custom_games', {})
        
        # 1. Gom tất cả tên game
        all_raw_names = sorted(list(custom_games_data.keys()) + server_games)
        
        # 2. Lọc theo search
        if search_term:
            search_term = search_term.lower()
            filtered_names = [name for name in all_raw_names if search_term in name.lower()]
        else:
            filtered_names = all_raw_names

        # 3. Chia 3 nhóm
        list_custom = []
        list_installed = []
        list_uninstalled = []

        for name in filtered_names:
            if name in custom_games_data:
                list_custom.append(name)
            elif is_game_installed(name):
                list_installed.append(name)
            else:
                list_uninstalled.append(name)

        # 4. Hàm vẽ Header + List
        # --- LOGIC ĐÓNG MỞ (COLLAPSIBLE) ---
        def toggle_section(section_frame, content_frame, arrow_label):
            """Ẩn/hiện nội dung danh mục và đổi mũi tên."""
            if content_frame.winfo_viewable():
                # Đang mở -> Đóng lại
                content_frame.pack_forget()
                arrow_label.config(text="▶")
            else:
                # Đang đóng -> Mở ra
                content_frame.pack(fill=tk.X)
                arrow_label.config(text="▼")
        
        # --- HÀM VẼ CATEGORY (FIX LỖI VỊ TRÍ) ---
        def draw_section(title, game_list, is_custom_section=False):
            if not game_list: return
            
            # 1. Tạo Container ĐỘC LẬP cho Category này (Quan trọng!)
            # Frame này sẽ giữ chỗ cố định trên Sidebar, không bị chạy lung tung
            section_container = tk.Frame(g_steam_sidebar_frame, bg="#191919")
            section_container.pack(fill=tk.X, pady=0) # Pack container vào Sidebar chính

            # Thiết lập màu sắc phù hợp
            if title == "🌟 GAME NGOÀI":
                title_color = "#FFC300"  # Vàng Gold (Đặc biệt)
            elif title == "✅ ĐÃ CÀI ĐẶT":
                title_color = "#32CD32"  # Xanh Lá (Ready)
            elif title == "❌ CHƯA CÀI ĐẶT":
                title_color = "#4A90E2"  # Xanh Dương (Mặc định/Thư viện)
            else:
                title_color = "#8a8a8a"  # Màu xám mặc định

            # 2. Header Frame (Nằm trong Container)
            header_frame = tk.Frame(section_container, bg="#191919", pady=5, cursor="hand2")
            header_frame.pack(fill=tk.X)
            
            arrow_lbl = tk.Label(header_frame, text="▼", bg="#191919", fg=title_color, font=("Segoe UI", 8))
            arrow_lbl.pack(side=tk.LEFT, padx=(5, 2))
            
            title_lbl = tk.Label(header_frame, text=f"{title} ({len(game_list)})", bg="#191919", fg=title_color, font=("Segoe UI", 9, "bold"))
            title_lbl.pack(side=tk.LEFT)

            # 3. Content Frame (Nằm trong Container, ngay dưới Header)
            content_frame = tk.Frame(section_container, bg="#191919")
            content_frame.pack(fill=tk.X) 

            # Gắn sự kiện Toggle
            cmd_toggle = lambda e: toggle_section(header_frame, content_frame, arrow_lbl)
            header_frame.bind("<Button-1>", cmd_toggle)
            arrow_lbl.bind("<Button-1>", cmd_toggle)
            title_lbl.bind("<Button-1>", cmd_toggle)
            
            # Hover Effect
            def on_enter(e):
                title_lbl.config(fg="white")
                arrow_lbl.config(fg="white")
            def on_leave(e):
                title_lbl.config(fg=title_color)
                arrow_lbl.config(fg=title_color)
            
            header_frame.bind("<Enter>", on_enter)
            header_frame.bind("<Leave>", on_leave)

            # Render Items
            for game in game_list:
                render_sidebar_item(content_frame, game, is_custom_section)


        # 5. Thực hiện vẽ theo thứ tự
        draw_section("🌟 GAME NGOÀI", list_custom, is_custom_section=True)
        draw_section("✅ ĐÃ CÀI ĐẶT", list_installed, is_custom_section=False)
        draw_section("❌ CHƯA CÀI ĐẶT", list_uninstalled, is_custom_section=False)

        # 6. Auto Select (Ưu tiên: Custom -> Installed -> Uninstalled)
        target_game = None

        # [MỚI] Ưu tiên giữ lại game đang chọn (để không bị nhảy trang khi refresh)
        if g_current_game_name and g_current_game_name in filtered_names:
            target_game = g_current_game_name
        else:
            # Nếu không có (hoặc game đang chọn bị lọc mất), chọn cái đầu tiên
            if list_custom: target_game = list_custom[0]
            elif list_installed: target_game = list_installed[0]
            elif list_uninstalled: target_game = list_uninstalled[0]

        if target_game:
            # Gọi hàm hiển thị chi tiết
            show_steam_details(target_game)

        print("Steam UI Loaded (Categorized).")


    def show_page_2_for_game(game_name):
        """
        (INSTANT SWITCH) Chuyển trang ngay lập tức, đẩy việc load dữ liệu ra sau.
        """
        global g_current_game_name, g_game_image_label, page_2_back_button
        
        # 1. Cập nhật biến cơ bản
        g_current_game_name = game_name
        
        # 2. Reset UI cơ bản (Ẩn nút, đổi tên frame)
        if 'g_launch_game_button' in globals():
            g_launch_game_button.pack_forget()
        if 'g_set_path_button' in globals():
            try: g_set_path_button.pack_forget()
            except: pass
            
        page_2_back_button.pack(side=tk.LEFT)
        options_frame.config(text=f"Các mod cho: {game_name}")
        
        # Xóa ảnh cũ tạm thời (để tránh hiện ảnh game trước)
        g_game_image_label.pack_forget() 
        
        # 3. CHUYỂN TRANG NGAY LẬP TỨC (Không chờ load dữ liệu)
        show_page(page_2_mod_list)
        
        # 4. Hẹn giờ chạy logic nặng (Load Config, Load Ảnh, Vẽ Mod)
        # 10ms là đủ để UI kịp vẽ trang mới trước khi bắt đầu xử lý nặng
        root.after(10, lambda: _deferred_page_2_logic(game_name))

    

    def _deferred_page_2_logic(game_name):
        """Hàm phụ: Chạy sau khi giao diện đã chuyển xong."""
        global local_config, path_entry
        
        # 1. Load Config
        local_config = load_local_config()
        
        # 2. Điền đường dẫn
        path_entry.delete(0, tk.END)
        last_used_folder = local_config.get("last_used_folder", "")
        specific_path = local_config.get("game_paths", {}).get(game_name, "")
        path_entry.insert(0, specific_path if specific_path else last_used_folder)

        # --- XÓA HẾT CÁC HÀM DEF Ở ĐÂY ---
        
        # 3. Vẽ danh sách mod
        update_radio_buttons_text_for_game(game_name)

    def update_mod_button_states(selected_key):
        """Cập nhật trạng thái text và STYLE của tất cả các nút chọn mod."""
        global g_mod_buttons, g_current_selected_key
        g_current_selected_key = selected_key
        
        # --- (BEGIN) THAY ĐỔI: Unpack tuple (select_button, checkmark_button) ---
        for key, (select_button, checkmark_button) in g_mod_buttons.items():
            try:
                if key == selected_key:
                    # Nút CHỌN (bên phải): Đổi thành "✓"
                    select_button.config(text="   ", style="Accent.TButton", state=tk.NORMAL)
                    
                    # Nút CHECK (bên trái): Hiện "✓" và bật
                    checkmark_button.config(text="   ", state=tk.NORMAL)
                else:
                    # Nút CHỌN (bên phải): Trả về text rỗng
                    select_button.config(text="", style="TButton", state=tk.NORMAL)
                    
                    # Nút CHECK (bên trái): Ẩn text và mờ
                    checkmark_button.config(text="", state=tk.DISABLED)
            except tk.TclError:
                pass

    def update_radio_buttons_text_for_game(game_name_to_show):
        """
        (ULTIMATE BATCH) Xóa cực nhanh và Vẽ theo lô.
        """
        global local_config, radio_buttons, g_mod_buttons, g_current_selected_key
        global content_frame, canvas

        # 1. Reset dữ liệu
        g_mod_buttons.clear()
        g_current_selected_key = None
        selected_option.set("") 
        radio_buttons = []

        style.configure("New.TLabel", foreground="red", font=('TkDefaultFont', 9, 'bold'))
        style.configure("Installed.TLabel", foreground="green")

        # --- KỸ THUẬT DỌN DẸP SIÊU TỐC ---
        # Mẹo: Ẩn frame đi trước khi destroy con của nó. 
        # Tkinter sẽ không tốn sức tính toán lại layout cho từng cái bị xóa.
        if content_frame.winfo_viewable():
            # Tạm thời gỡ khỏi canvas (chỉ là ẩn hiển thị, ko mất dữ liệu)
            # Lưu ý: content_frame nằm trong canvas window, ta dùng itemconfigure để ẩn
            canvas.itemconfigure(canvas_window_id, state='hidden')
        
        # Bây giờ xóa rất nhanh
        for widget in content_frame.winfo_children(): 
            widget.destroy()
            
        # Hiện lại frame (đang trống)
        canvas.itemconfigure(canvas_window_id, state='normal')
        # --------------------------------

        # Hiện Loading
        loading_label = ttk.Label(content_frame, text="⏳ Đang tải danh sách mod...", font=("Segoe UI", 10))
        loading_label.pack(pady=20)
        
        # Cập nhật UI ngay lập tức để người dùng thấy Loading
        content_frame.update_idletasks()

        # Chuẩn bị dữ liệu
        mod_list = download_options.get(game_name_to_show, [])
        first_key_holder = [None] 

        def create_click_handler(key_value):
            def handler(event=None):
                selected_option.set(key_value)
                update_guide_text()
                update_mod_button_states(key_value)
            return handler

        BATCH_SIZE = 8 # Vẽ 8 cái một lúc
        
        def process_mod_batch(start_index):
            end_index = min(start_index + BATCH_SIZE, len(mod_list))
            
            if start_index == 0 and loading_label.winfo_exists():
                loading_label.destroy()

            for i in range(start_index, end_index):
                key, data = mod_list[i]
                
                display_name = data.get("name", "LỖI: THIẾU TÊN")
                online_version = data.get("version")
                if not online_version: continue 

                installed_version = local_config.get("installed_versions", {}).get(key, "Chưa cài đặt")

                # Layout Row
                row_frame = ttk.Frame(content_frame, style="Card.TFrame", padding=(10, 5))
                row_frame.pack(fill=tk.X, pady=2) 
                
                # Checkbox
                checkmark_frame = ttk.Frame(row_frame)
                checkmark_frame.pack(side=tk.LEFT,padx=(0, 0))
                checkmark_button = ttk.Button(checkmark_frame, text="", style="Accent.TButton", state=tk.DISABLED)
                checkmark_button.pack(fill=tk.Y, expand=True)

                # Info
                left_frame = ttk.Frame(row_frame)
                left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
                left_frame.columnconfigure(0, weight=1) 

                right_frame = ttk.Frame(row_frame)
                right_frame.pack(side=tk.RIGHT, padx=(0, 0))

                name_label = ttk.Label(left_frame, text=display_name, font=("Segoe UI", 10, "bold"), anchor=tk.CENTER)
                name_label.grid(row=0, column=0, sticky="ew")

                all_widgets_to_bind = [row_frame, checkmark_frame, checkmark_button, left_frame, right_frame, name_label] 

                # Status
                if online_version == installed_version:
                    status_text = f"✓ Đã cài đặt ({online_version})"
                    status_label = ttk.Label(left_frame, text=status_text, style="Installed.TLabel", anchor=tk.CENTER) 
                    status_label.grid(row=1, column=0, sticky="ew", pady=(2, 0)) 
                    all_widgets_to_bind.append(status_label)
                else:
                    status_text = f"🔥 Cần cài đặt ({online_version})" if installed_version == "Chưa cài đặt" else f"🔥 Cập nhật ({online_version})"
                    new_label = ttk.Label(left_frame, text=status_text, style="New.TLabel", anchor=tk.CENTER)
                    new_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
                    all_widgets_to_bind.append(new_label)

                # Selection
                if first_key_holder[0] is None: first_key_holder[0] = key

                click_cmd = create_click_handler(key)
                select_button = ttk.Button(right_frame, text="Chọn", command=click_cmd)
                select_button.pack(fill=tk.Y, expand=True)
                
                g_mod_buttons[key] = (select_button, checkmark_button)
                all_widgets_to_bind.append(select_button)

                # Bindings
                for widget in all_widgets_to_bind:
                    try:
                        widget.bind("<MouseWheel>", on_mouse_wheel)
                        widget.bind("<Button-4>", on_mouse_wheel) 
                        widget.bind("<Button-5>", on_mouse_wheel)
                        if widget != select_button: widget.bind("<Button-1>", click_cmd)
                    except: pass

            if end_index < len(mod_list):
                root.after(5, lambda: process_mod_batch(end_index))
            else:
                content_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                
                # Auto select first
                if first_key_holder[0]:
                    selected_option.set(first_key_holder[0])
                    update_guide_text()
                    update_mod_button_states(first_key_holder[0])

        process_mod_batch(0)

        
    # def refresh_mod_list_ui():
    #     """
    #     (Hàm mới) Xóa và vẽ lại danh sách mod (Trang 2) 
    #     để cập nhật trạng thái (ví dụ: "Đã cài đặt").
    #     """
    #     global content_frame, g_current_game_name
        
    #     # Kiểm tra xem Trang 2 có đang hoạt động không
    #     if not g_current_game_name or not content_frame.winfo_exists():
    #         print("Lỗi: Không thể refresh mod list (UI không tồn tại).")
    #         return

    #     print(f"Đang làm mới danh sách mod cho: {g_current_game_name}")
        
    #     # 1. Xóa tất cả các nút mod cũ (ĐIỀU QUAN TRỌNG NHẤT)
    #     for widget in content_frame.winfo_children(): 
    #         widget.destroy()
            
    #     # 2. Gọi hàm vẽ lại các nút mod mới
    #     # (Hàm này sẽ đọc config mới và vẽ lại đúng trạng thái)
    #     update_radio_buttons_text_for_game(g_current_game_name)


    path_frame = ttk.Frame(page_2_mod_list)
    path_frame.pack(fill=tk.X, pady=(5, 10))
    path_label = ttk.Label(path_frame, text="Đường dẫn folder mod:")
    path_label.pack(side=tk.LEFT, padx=(0, 10))
    path_entry = ttk.Entry(path_frame)
    path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    path_entry.bind("<FocusOut>", lambda e: update_guide_text())

    # --- THÊM MỚI: CHECKBOX TỰ ĐỘNG EXCLUSION ---
    # Biến lưu trạng thái checkbox
    g_auto_add_exclusion = tk.BooleanVar(value=False) 

    # Tạo Checkbox
    defender_checkbox = ttk.Checkbutton(
        page_2_mod_list, 
        text="🛡️ Tự động thêm thư mục này vào Exclusion (để tránh bị xóa file)",
        variable=g_auto_add_exclusion,
        style="Switch.TCheckbutton" # Hoặc để trống nếu chưa định nghĩa style này
    )
    # Pack nó ngay trên button_frame
    defender_checkbox.pack(pady=(5, 0)) 
    CreateToolTip(defender_checkbox, "Nếu tích: App sẽ tự động thêm folder này vào danh sách loại trừ của Windows Defender\nnếu nó chưa nằm trong đó.")

    button_frame = ttk.Frame(page_2_mod_list)
    button_frame.pack(pady=15)
    browse_button = ttk.Button(button_frame, text="Tìm đường dẫn...", command=browse_for_folder)
    browse_button.pack(side=tk.LEFT, padx=10)

    start_button = ttk.Button(button_frame, text="Bắt đầu Cài đặt", 
                            command=start_download_thread, style="Accent.TButton")
    start_button.pack(side=tk.LEFT, padx=10)

    option_label = ttk.Label(page_3_progress, text = "GG", anchor=tk.W, style="White.TLabel")

    for widget in page_3_progress.winfo_children():
        widget.destroy()

    # 2. Spacer trên cùng (Đẩy nội dung xuống giữa)
    ttk.Frame(page_3_progress).pack(side=tk.TOP, expand=True)

    # 3. Ảnh GIF (Animation) - Đặt ở giữa màn hình
    g_gif_label = ttk.Label(page_3_progress, anchor=tk.CENTER)
    g_gif_label.pack(side=tk.TOP, pady=(0, 20))

    # 4. Tên Option đang tải (Ví dụ: Đang xử lý: Elden Ring...)
    option_label = ttk.Label(page_3_progress, text="Chuẩn bị...", anchor=tk.CENTER, style="White.TLabel", font=("Segoe UI", 11, "bold"))
    option_label.pack(side=tk.TOP, pady=(0, 15))

    # --- KHUNG CHỨA THANH TIẾN TRÌNH & THÔNG SỐ (GOM NHÓM) ---
    # Tạo một container để gom các thanh bar và text lại gần nhau
    progress_container = ttk.Frame(page_3_progress)
    progress_container.pack(side=tk.TOP, fill=tk.X, padx=100) # padx=100 để thanh bar không quá dài ra mép

    # A. Thanh File hiện tại
    progress_file_frame = ttk.Frame(progress_container)
    progress_file_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
    
    lbl_file_progress = ttk.Label(progress_file_frame, text="Tiến độ File hiện tại:", style="secondary.TLabel")
    lbl_file_progress.pack(anchor=tk.W)
    
    progress_bar = ttk.Progressbar(progress_file_frame, orient="horizontal", length=100, mode="indeterminate")
    progress_bar.pack(fill=tk.X, pady=(2, 0))

    # B. Thanh Tiến độ chung (Parts)
    global overall_progress_bar, overall_status_label
    progress_overall_frame = ttk.Frame(progress_container)
    progress_overall_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 5))

    overall_status_label = ttk.Label(progress_overall_frame, text="Tiến độ chung: 0/0 Part", style="White.TLabel")
    overall_status_label.pack(anchor=tk.W)

    overall_progress_bar = ttk.Progressbar(progress_overall_frame, orient="horizontal", length=100, mode="determinate")
    overall_progress_bar.pack(fill=tk.X, pady=(2, 0))

    # C. Dòng trạng thái (%, Tốc độ, ETA) - Đặt ngay dưới thanh bar
    status_frame = ttk.Frame(progress_container)
    status_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

    status_label = ttk.Label(status_frame, text="Sẵn sàng.", anchor=tk.W, style="White.TLabel")
    status_label.pack(side=tk.LEFT)
    
    eta_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
    eta_label.pack(side=tk.RIGHT)
    
    speed_label = ttk.Label(status_frame, text="", style="secondary.TLabel", anchor=tk.E, width=15)
    speed_label.pack(side=tk.RIGHT)

    # 5. Spacer dưới cùng (Cân bằng bố cục)
    ttk.Frame(page_3_progress).pack(side=tk.TOP, expand=True)
    # --- Hết Nội dung Tab 1 ---

    # --- SỬA: Tạo UI cho Tab 2 ("Upload Config") ---
    second_tab_frame = ttk.Frame(notebook, padding=(10, 10))
    notebook.add(second_tab_frame, text=" Quản Lý Option Tải ") # Đổi tên cho chuyên nghiệp

    # --- Variables ---
    current_config_data = {} 
    current_github_sha = None 
    g_currently_selected_id = None
    g_game_theme_sha = None
    g_master_game_list = []
    g_search_timer = None
    g_theme_manager_window = None

    # --- Layout Chính: Chia làm 2 cột (Trái: List, Phải: Form Editor) ---
    # PanedWindow giúp người dùng kéo thả kích thước 2 bên
    paned_window = ttk.PanedWindow(second_tab_frame, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # Khung Trái (Danh sách Option)
    left_pane = ttk.Frame(paned_window)
    paned_window.add(left_pane, weight=1)

    # Khung Phải (Form Nhập liệu)
    right_pane = ttk.Frame(paned_window)
    paned_window.add(right_pane, weight=2) # Form rộng hơn list

    # ==========================
    # 1. CỘT TRÁI: DANH SÁCH
    # ==========================
    
    # Toolbar trên cùng của cột trái
    left_toolbar = ttk.Frame(left_pane)
    left_toolbar.pack(fill=tk.X, pady=(0, 5))
    
    ttk.Label(left_toolbar, text="Danh sách Option", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

    # Treeview
    tree_frame = ttk.Frame(left_pane)
    tree_frame.pack(fill=tk.BOTH, expand=True)

    tree_scrollbar = ttk.Scrollbar(tree_frame)
    tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Chỉ hiện Tên và Game để tiết kiệm diện tích, các thông tin khác xem bên phải
    cols = ("ID", "Name", "Game") 
    options_treeview = ttk.Treeview(tree_frame, columns=cols, show='headings', yscrollcommand=tree_scrollbar.set, selectmode="browse")
    options_treeview.pack(expand=True, fill=tk.BOTH)
    tree_scrollbar.config(command=options_treeview.yview)

    options_treeview.heading("ID", text="ID")
    options_treeview.heading("Name", text="Tên Option")
    options_treeview.heading("Game", text="Game")
    
    options_treeview.column("ID", width=40, anchor=tk.CENTER, stretch=tk.NO)
    options_treeview.column("Name", width=150, anchor=tk.W)
    options_treeview.column("Game", width=100, anchor=tk.W)

    # Nút Di chuyển (Floating nhỏ gọn bên dưới)
    move_btn_frame = ttk.Frame(left_pane)
    move_btn_frame.pack(fill=tk.X, pady=5)
    
    ttk.Button(move_btn_frame, text="▲", width=3, command=lambda: action_move_option("up")).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
    ttk.Button(move_btn_frame, text="▼", width=3, command=lambda: action_move_option("down")).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

    # ==========================
    # 2. CỘT PHẢI: FORM EDITOR HIỆN ĐẠI
    # ==========================
    
    # Container cho Form (có scrollbar phòng khi màn hình bé)
    form_canvas = tk.Canvas(right_pane, highlightthickness=0)
    form_scrollbar = ttk.Scrollbar(right_pane, orient="vertical", command=form_canvas.yview)
    
    # Frame chứa nội dung thực sự
    edit_form_frame = ttk.Frame(form_canvas)
    # --- [MỚI] HÀM XỬ LÝ CUỘN CHUỘT CHO FORM ---
    def on_form_mouse_wheel(event):
        """Xử lý cuộn chuột riêng cho Form Editor."""
        if not form_canvas.winfo_exists(): return
        
        # Kiểm tra xem Form có cần cuộn không (nếu nội dung ngắn hơn khung thì không cuộn)
        if edit_form_frame.winfo_reqheight() <= form_canvas.winfo_height():
            return

        scroll_amount = 0
        if sys.platform == "win32":
            scroll_amount = int(-1 * (event.delta / 120))
        elif sys.platform == "darwin": # macOS
            scroll_amount = event.delta
        else: # Linux
            if event.num == 4: scroll_amount = -1
            elif event.num == 5: scroll_amount = 1
        
        form_canvas.yview_scroll(scroll_amount, "units")

    # --- [MỚI] HÀM GẮN SỰ KIỆN KHI CHUỘT VÀO VÙNG FORM ---
    def bind_form_scroll(event):
        """Khi chuột vào vùng Form: Gắn sự kiện lăn chuột cho TOÀN BỘ ứng dụng hướng về Form."""
        # Gắn cho Windows/MacOS
        form_canvas.bind_all("<MouseWheel>", on_form_mouse_wheel)
        # Gắn cho Linux
        form_canvas.bind_all("<Button-4>", on_form_mouse_wheel)
        form_canvas.bind_all("<Button-5>", on_form_mouse_wheel)

    def unbind_form_scroll(event):
        """Khi chuột rời vùng Form: Gỡ sự kiện (để trả lại cho các vùng khác)."""
        form_canvas.unbind_all("<MouseWheel>")
        form_canvas.unbind_all("<Button-4>")
        form_canvas.unbind_all("<Button-5>")

    # --- [QUAN TRỌNG] KÍCH HOẠT VÙNG CẢM ỨNG ---
    # Khi chuột đi vào khung Form -> Bật cuộn
    edit_form_frame.bind("<Enter>", bind_form_scroll)
    
    # Khi chuột rời khỏi khung Form -> Tắt cuộn
    # (Lưu ý: Dùng form_canvas làm mốc rời đi để bao quát hơn)
    form_canvas.bind("<Leave>", unbind_form_scroll)
    
    # Cũng bind cho chính canvas để chắc chắn bắt được
    form_canvas.bind("<Enter>", bind_form_scroll)
    form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    form_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # --- [FIX QUAN TRỌNG] ---
    # Tạo window và LƯU ID lại để dùng sau
    form_window_id = form_canvas.create_window((0, 0), window=edit_form_frame, anchor="nw")

    # Hàm 1: Khi nội dung thay đổi chiều cao -> Cập nhật thanh cuộn dọc
    def on_frame_configure(event):
        form_canvas.configure(scrollregion=form_canvas.bbox("all"))
        
        # [MỚI] Mẹo nhỏ: Thay đổi tốc độ cuộn cho mượt hơn
        # Mặc định Tkinter cuộn khá chậm
        form_canvas.configure(yscrollincrement='5') 

    edit_form_frame.bind("<Configure>", on_frame_configure)

    # Hàm 2: Khi Canvas thay đổi chiều rộng -> Ép nội dung co giãn theo
    def on_canvas_configure(event):
        # Lấy chiều rộng hiện tại của canvas
        canvas_width = event.width
        # Set chiều rộng của edit_form_frame bằng chiều rộng canvas
        form_canvas.itemconfig(form_window_id, width=canvas_width)

    edit_form_frame.bind("<Configure>", on_frame_configure)
    form_canvas.bind("<Configure>", on_canvas_configure)

    # --- Header Form ---
    header_form_frame = ttk.Frame(edit_form_frame, padding=10)
    header_form_frame.pack(fill=tk.X)
    
    form_title_label = ttk.Label(header_form_frame, text="✨ Thêm / Sửa Option", font=("Segoe UI", 12, "bold"), foreground="#4cc2ff")
    form_title_label.pack(side=tk.LEFT)
    
    # [SỬA] Gán vào biến btn_clear_header
    btn_clear_header = ttk.Button(header_form_frame, text="Làm mới (Tạo mới)", command=lambda: clear_form())
    btn_clear_header.pack(side=tk.RIGHT)

    form_widgets = {}
    def action_move_option(direction):
        """Di chuyển thứ tự option lên/xuống."""
        global current_config_data
        selected_items = options_treeview.selection()
        if not selected_items: return

        selected_key = selected_items[0]
        items_list = list(current_config_data.items())
        
        # Tìm index hiện tại
        curr_idx = -1
        for i, (k, v) in enumerate(items_list):
            if k == selected_key:
                curr_idx = i
                break
        
        if curr_idx == -1: return

        # Tính index mới
        new_idx = curr_idx - 1 if direction == "up" else curr_idx + 1
        
        if 0 <= new_idx < len(items_list):
            # Hoán đổi
            items_list[curr_idx], items_list[new_idx] = items_list[new_idx], items_list[curr_idx]
            current_config_data = dict(items_list)
            
            # Refresh UI
            populate_treeview()
            options_treeview.selection_set(selected_key)
            options_treeview.see(selected_key)
            upload_status_label.config(text="Đã thay đổi thứ tự. Nhớ 'Upload Config' để lưu!", foreground="#ffcc00")

    def action_clear_theme_form():
        """
        Xóa trắng các ô nhập liệu để chuẩn bị nhập game mới.
        Bỏ chọn item trong listbox.
        """
        # 1. Xóa nội dung trong các ô nhập
        if g_theme_name_entry:
            g_theme_name_entry.delete(0, tk.END)
        
        if 'g_theme_url_text' in globals() and g_theme_url_text.winfo_exists():
            g_theme_url_text.delete("1.0", tk.END) # <-- SỬA: Xóa Text widget

        # 2. Bỏ chọn dòng đang chọn trong Listbox (để người dùng biết đang không sửa game nào)
        if g_theme_listbox:
            g_theme_listbox.selection_clear(0, tk.END)
            
        # 3. Focus vào ô tên game để nhập ngay
        if g_theme_name_entry:
            g_theme_name_entry.focus_set()

    def open_game_theme_manager():
        """
        Mở cửa sổ quản lý Theme (Admin Dashboard).
        ĐÃ CẬP NHẬT: Thêm nút 'Nhập Mới' (Empty Form).
        """
        global g_theme_manager_window, g_theme_name_entry, g_theme_url_entry, g_theme_listbox

        if g_theme_manager_window and g_theme_manager_window.winfo_exists():
            g_theme_manager_window.lift()
            return

        g_theme_manager_window = tk.Toplevel(root)
        g_theme_manager_window.title("Quản Lý Game Theme & Trailer")
        center_window_on_screen(g_theme_manager_window, 750, 550)
        g_theme_manager_window.transient(root)
        g_theme_manager_window.grab_set()
        
        # Áp dụng theme titlebar
        g_theme_manager_window.after(10, lambda: apply_theme_to_titlebar(g_theme_manager_window))

        # Layout chính: Chia 2 cột
        main_layout = ttk.Frame(g_theme_manager_window, padding=10)
        main_layout.pack(fill=tk.BOTH, expand=True)

        # --- CỘT TRÁI: DANH SÁCH GAME ---
        left_frame = ttk.LabelFrame(main_layout, text="Danh sách Game", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        list_scroll = ttk.Scrollbar(left_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        g_theme_listbox = tk.Listbox(left_frame, yscrollcommand=list_scroll.set, font=("Segoe UI", 10), exportselection=False)
        g_theme_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=g_theme_listbox.yview)

        # --- CỘT PHẢI: FORM NHẬP LIỆU ---
        right_frame = ttk.LabelFrame(main_layout, text="Thông tin Chi tiết", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 1. Tên Game
        ttk.Label(right_frame, text="Tên Game (Chính xác):").pack(anchor=tk.W, pady=(0, 5))
        g_theme_name_entry = ttk.Entry(right_frame, width=40)
        g_theme_name_entry.pack(fill=tk.X, pady=(0, 10))

        # 2. Link Ảnh
        ttk.Label(right_frame, text="URL Hình Ảnh (Mỗi dòng 1 link, dòng 1 là ảnh chính):").pack(anchor=tk.W, pady=(0, 5))
        global g_theme_url_text # Khai báo global để dùng ở hàm save/load
        g_theme_url_text = tk.Text(right_frame, height=5, width=40, font=("Segoe UI", 9))
        g_theme_url_text.pack(fill=tk.X, pady=(0, 10))
        
        # # 3. Link Trailer
        # ttk.Label(right_frame, text="URL Trailer (Youtube/MP4):").pack(anchor=tk.W, pady=(0, 5))
        # g_theme_trailer_entry = ttk.Entry(right_frame, width=40)
        # g_theme_trailer_entry.pack(fill=tk.X, pady=(0, 10))
        # ttk.Label(right_frame, text="Gợi ý: Link Youtube hoặc file .mp4", font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W, pady=(0, 10))

        # --- BUTTONS ACTION (ĐÃ CẬP NHẬT) ---
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=20)

        # Nút Làm Sạch Form (MỚI)
        ttk.Button(btn_frame, text="✨ Nhập Mới (Làm Sạch Form)", command=action_clear_theme_form).pack(fill=tk.X, pady=(0, 10))

        # Các nút cũ
        ttk.Button(btn_frame, text="💾 Lưu / Cập Nhật", style="Accent.TButton", command=action_add_game_theme).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="❌ Xóa Game Này", style="Danger.TButton", command=action_delete_game_theme).pack(fill=tk.X, pady=5)
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # --- LOGIC SELECTION ---
        def on_theme_select_event(event):
            selection = g_theme_listbox.curselection()
            if selection:
                game_name = g_theme_listbox.get(selection[0])
                data = g_game_themes.get(game_name)
                
                # Xóa form cũ
                g_theme_name_entry.delete(0, tk.END)
                g_theme_url_text.delete("1.0", tk.END) # <-- SỬA: Xóa Text widget
                
                # Điền form mới
                g_theme_name_entry.insert(0, game_name)
                
                if isinstance(data, dict):
                    # Ưu tiên lấy list slideshow, nếu không có thì lấy 1 ảnh lẻ
                    images = data.get("slideshow", [])
                    if not images and data.get("image"):
                        images = [data.get("image")]
                    
                    # Hiển thị mỗi link 1 dòng
                    g_theme_url_text.insert("1.0", "\n".join(images)) 
                    
                elif isinstance(data, str): # Logic cũ (chỉ là chuỗi)
                    g_theme_url_text.insert("1.0", data)
                
        g_theme_listbox.bind('<<ListboxSelect>>', on_theme_select_event)

        # Load dữ liệu ban đầu
        populate_theme_listbox()

    # Giữ nguyên populate_theme_listbox nhưng đảm bảo nó gọi đúng biến toàn cục
    def populate_theme_listbox():
        if not g_theme_listbox: return
        g_theme_listbox.delete(0, tk.END)
        
        if not g_game_themes: return

        sorted_games = sorted(g_game_themes.keys())
        for game_name in sorted_games:
            g_theme_listbox.insert(tk.END, game_name)

    def toggle_edit_form_state(enable=True):
        """Khóa hoặc Mở khóa toàn bộ form nhập liệu."""
        state = "normal" if enable else "disabled"
        
        # 1. Xử lý các widget nhập liệu (Entry, Combobox, Text)
        for widget in form_widgets.values():
            try:
                # Với Text widget, state='disabled' sẽ làm xám màu và chặn nhập liệu
                widget.config(state=state)
            except: pass

        # 2. Xử lý các nút bấm hành động
        try:
            add_update_button.config(state=state)
            delete_option_btn.config(state=state)
            # Nút "Thêm Game" nhỏ bên cạnh combobox
            btn_add_game_theme.config(state=state) 
            # Nút "Chọn từ Drive"
            btn_drive_picker.config(state=state) # (Lưu ý: Cần gán biến cho nút này ở Bước 2)
            # Nút "Làm mới/Tạo mới" ở header
            btn_clear_header.config(state=state) # (Lưu ý: Cần gán biến cho nút này ở Bước 2)
        except Exception as e:
            # Bỏ qua lỗi nếu nút chưa được khởi tạo (lần chạy đầu)
            pass

    def action_add_update_option():
        """Lấy dữ liệu từ Form và Lưu vào Config (Hỗ trợ Multi-URL)."""
        global current_config_data, g_currently_selected_id

        # 1. Lấy dữ liệu từ Form Widgets
        name = form_widgets["Option Name:"].get().strip()
        
        # --- [CẬP NHẬT] Lấy URL từ Text Widget ---
        raw_urls_text = form_widgets["URL:"].get("1.0", tk.END).strip()
        # Tách dòng và làm sạch
        url_list = [line.strip() for line in raw_urls_text.splitlines() if line.strip()]
        
        # Logic xử lý ID Google Drive (nếu người dùng chỉ nhập ID)
        final_url_list = []
        for u in url_list:
            if "drive.google.com" not in u and "/" not in u and len(u) > 15:
                # Giả sử là ID
                final_url_list.append(f"https://drive.google.com/uc?id={u}")
            else:
                final_url_list.append(u)
        # -----------------------------------------

        game = form_widgets["Game:"].get().strip()
        ver = form_widgets["Version:"].get().strip()
        f_type = form_widgets["Type:"].get()
        launch_file = form_widgets["Launch File:"].get().strip()
        pwd = form_widgets["Password:"].get().strip()
        tag = form_widgets["Game Tag:"].get().strip().upper() # Luôn chuyển thành chữ HOA
        guide = form_widgets["Path Guide:"].get("1.0", tk.END).strip()
        del_list_raw = form_widgets["Delete List:"].get("1.0", tk.END).strip()
        del_list = [line.strip() for line in del_list_raw.splitlines() if line.strip()]

        # Validate
        if not name:
            custom_showwarning("Thiếu Tên", "Vui lòng nhập Tên Option.")
            return
        if not game:
            custom_showwarning("Thiếu Game", "Vui lòng chọn hoặc nhập tên Game.")
            return
        if not final_url_list:
            custom_showwarning("Thiếu Link", "Vui lòng nhập ít nhất 1 đường dẫn tải.")
            return

        # Tạo dict data mới
        new_data = {
            "name": name,
            "urls": final_url_list, # Lưu Key mới là 'urls' (list)
            "version": ver,
            "game": game,
            "type": f_type,
            "password": pwd if pwd else None,
            "launch_file": launch_file if launch_file else None,
            "tag": tag if tag in TAG_COLORS else None,
            "path_guide": guide if guide else None,
            "delete_before_extract": del_list
        }
        
        # Tương thích ngược: Lưu thêm key 'url' là link đầu tiên (để các bản tool cũ không bị crash)
        if final_url_list:
            new_data["url"] = final_url_list[0]

        # 2. Lưu vào dict chính
        target_key = None
        if g_currently_selected_id:
            target_key = g_currently_selected_id
            current_config_data[target_key] = new_data
            upload_status_label.config(text=f"Đã cập nhật: {name}", foreground="green")
        else:
            max_id = 0
            for k in current_config_data:
                if k.isdigit(): max_id = max(max_id, int(k))
            target_key = str(max_id + 1)
            current_config_data[target_key] = new_data
            upload_status_label.config(text=f"Đã thêm mới: {name} (ID: {target_key})", foreground="green")

        # 3. Refresh
        populate_treeview()
        options_treeview.selection_set(target_key)
        options_treeview.see(target_key)
    
    def action_delete_option():
        global current_config_data
        sel = options_treeview.selection()
        if not sel: return
        
        key = sel[0]
        name = current_config_data.get(key, {}).get("name", "Unknown")
        
        if custom_askyesno("Xóa Option", f"Bạn chắc chắn muốn xóa: {name}?"):
            del current_config_data[key]
            clear_form()
            populate_treeview()
            upload_status_label.config(text=f"Đã xóa: {name}", foreground="red")

    def action_load_from_github_wrapper():
        # Wrapper gọi hàm load logic chính (đã có ở phần tab 2 cũ)
        # Vì bạn đang thay thế UI, ta cần đảm bảo logic load vẫn chạy
        # Gọi lại hàm load_from_github_wrapper gốc hoặc viết lại logic gọi hàm load_json
        # Ở đây tôi viết lại logic kết nối UI mới:
        
        global current_config_data, current_github_sha
        repo = get_github_repo()
        if not repo: return
        
        content, sha = load_json_from_github_api(repo)
        if content:
            current_config_data = json.loads(content)
            current_github_sha = sha
            populate_treeview()
            clear_form()
            upload_status_label.config(text="Đã tải Config mới nhất từ GitHub.", foreground="#4cc2ff")
            toggle_edit_form_state(True)
            # Refresh cả game list cho combobox
            update_game_combobox_list()

    def action_upload_to_github_wrapper():
        global current_config_data, current_github_sha
        if not current_config_data: return
        
        repo = get_github_repo()
        if not repo: return
        
        # Hỏi PIN
        pin = custom_askstring("Bảo Mật", "Nhập mã PIN Admin để upload:", show="*")
        if pin != "2408": 
            custom_showerror("Sai PIN", "Sai mã PIN.")
            return

        success, new_sha = upload_json_to_github(repo, current_config_data, current_github_sha)
        if success:
            if new_sha: current_github_sha = new_sha
            upload_status_label.config(text="Upload thành công! Dữ liệu đã an toàn.", foreground="green")

    def update_game_combobox_list():
        """Cập nhật Dropdown Game và danh sách Master để validate."""
        global g_game_themes, current_config_data
        # [FIX 1] Khai báo biến toàn cục cần cập nhật
        global g_master_game_list 

        # 1. Lấy game từ các Option hiện có
        games = set()
        if current_config_data:
            for v in current_config_data.values():
                if isinstance(v, dict) and "game" in v:
                    games.add(v["game"])
        
        # 2. Gộp thêm game từ danh sách Theme
        if 'g_game_themes' in globals() and g_game_themes:
            games.update(g_game_themes.keys())

        # 3. Sắp xếp
        sorted_games = sorted(list(games))
        
        # [FIX 2] CẬP NHẬT DANH SÁCH MASTER (Quan trọng nhất)
        # Đây là dòng còn thiếu khiến việc validate bị lỗi
        g_master_game_list = sorted_games 

        # 4. Cập nhật vào Widget Combobox
        if "Game:" in form_widgets:
            form_widgets["Game:"].config(values=sorted_games)

    # --- Hàm Helper tạo Input Group ---
    def create_modern_input(parent, label_text, widget_key, widget_type="Entry", options=None, height=1):
        frame = ttk.Frame(parent, padding=(10, 5))
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text=label_text, style="secondary.TLabel").pack(anchor=tk.W)
        
        widget = None
        if widget_type == "Entry":
            widget = ttk.Entry(frame)
        elif widget_type == "Combobox":
            widget = ttk.Combobox(frame, values=options, state="readonly")
            if options: widget.set(options[0])
        elif widget_type == "Text":
            widget = tk.Text(frame, height=height, wrap="word", relief=tk.FLAT, bg="#2b2b2b", fg="white", insertbackground="white", padx=5, pady=5)
            # Viền giả
            border_frame = ttk.Frame(frame, style="Card.TFrame") # Giả sử có style Card
            widget.pack(fill=tk.X, pady=2)
            
        if widget_type != "Text":
            widget.pack(fill=tk.X, pady=2)
            
        form_widgets[widget_key] = widget
        return frame, widget

    # --- NHÓM 1: THÔNG TIN CƠ BẢN (Card Layout) ---
    basic_info_frame = ttk.LabelFrame(edit_form_frame, text="📁 Thông tin File & Nguồn", padding=10)
    basic_info_frame.pack(fill=tk.X, padx=10, pady=5)

    # Hàng 1: URLS (Thay thế Entry bằng Text để nhập nhiều dòng)
    url_container = ttk.Frame(basic_info_frame)
    url_container.pack(fill=tk.X, pady=5)
    
    # Label hướng dẫn
    ttk.Label(url_container, text="URLs (Mỗi dòng 1 link - Ưu tiên link Drive/Gdown):", style="secondary.TLabel").pack(anchor=tk.W)
    
    # Khung chứa Text + Scrollbar
    text_frame = ttk.Frame(url_container)
    text_frame.pack(fill=tk.X, pady=2)
    
    url_scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
    url_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Widget Text nhập nhiều dòng
    def on_url_focus_out(event):
        """
        Khi người dùng click ra ngoài ô URL:
        Tự động quét từng dòng, nếu là link Drive thì chuyển thành ID.
        """
        try:
            # 1. Lấy nội dung hiện tại
            # "1.0" nghĩa là dòng 1, ký tự 0. "end-1c" là lấy hết trừ ký tự xuống dòng cuối
            content = form_widgets["URL:"].get("1.0", "end-1c").strip()
            if not content: return

            lines = content.splitlines()
            new_lines = []
            has_change = False

            for line in lines:
                original = line.strip()
                if not original: continue

                # Thử trích xuất ID
                extracted_id = extract_gdrive_id_from_url(original)
                
                if extracted_id:
                    # Nếu tìm thấy ID, thay thế luôn
                    new_lines.append(extracted_id)
                    if extracted_id != original: # Đánh dấu là có thay đổi
                        has_change = True
                else:
                    # Nếu không phải link Drive (ví dụ link Mediafire), giữ nguyên
                    new_lines.append(original)

            # 2. Cập nhật lại giao diện (Chỉ khi có thay đổi để tránh nháy)
            if has_change:
                final_text = "\n".join(new_lines)
                form_widgets["URL:"].delete("1.0", tk.END)
                form_widgets["URL:"].insert("1.0", final_text)
                print("Auto-Extract: Đã chuyển đổi Link thành ID.")
                
        except Exception as e:
            print(f"Lỗi auto-extract: {e}")
    url_text_widget = tk.Text(text_frame, height=4, wrap="none", 
                              relief=tk.FLAT, bg="#2b2b2b", fg="white", 
                              insertbackground="white", padx=5, pady=5,
                              yscrollcommand=url_scrollbar.set)
    url_text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # --- [MỚI] GẮN SỰ KIỆN FOCUS OUT ---
    # Khi chuột click sang ô khác -> Gọi hàm lọc
    url_text_widget.bind("<FocusOut>", on_url_focus_out)
    # -----------------------------------

    url_scrollbar.config(command=url_text_widget.yview)
    
    # Lưu vào dict widget để dùng sau
    form_widgets["URL:"] = url_text_widget

    # Các nút công cụ (Paste / Chọn từ Drive)
    btn_row = ttk.Frame(url_container)
    btn_row.pack(fill=tk.X, pady=2)
    
    

    # --- GIỮ NGUYÊN HÀM NÀY ---
    def configure_gemini():
        """Thiết lập Gemini API"""
        if GEMINI_API_KEY and "DIEN_API_KEY" not in GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            return True
        return False

    # --- GIỮ NGUYÊN HÀM NÀY ---    
    def find_game_image_url_online(game_name):
        """
        (NÂNG CẤP) Tìm ảnh capsule nhỏ từ Steam Search (Tốt cho Sidebar).
        """
        try:
            # Bỏ qua các từ khóa gây nhiễu khi search
            clean_name = game_name.replace("Portable", "").replace("Repack", "").strip()
            
            import urllib.parse
            encoded_name = urllib.parse.quote(clean_name)
            search_url = f"https://store.steampowered.com/search/?term={encoded_name}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            
            response = requests.get(search_url, headers=headers, timeout=3)
            if response.status_code == 200:
                html = response.text
                
                # Ưu tiên 1: Tìm ảnh capsule nhỏ (src="...capsule_sm_120.jpg")
                # Đây là ảnh hiện trong kết quả search, rất nhẹ và phù hợp làm icon
                match_small = re.search(r'src="([^"]+capsule_sm_120\.jpg[^"]*)"', html)
                if match_small:
                    return match_small.group(1)

                # Ưu tiên 2: Nếu không thấy, tìm App ID để suy ra ảnh Header
                match_id = re.search(r'data-ds-appid="(\d+)"', html)
                if match_id:
                    app_id = match_id.group(1)
                    return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                    
        except Exception as e:
            print(f"Lỗi tìm ảnh '{game_name}': {e}")
        return None
    
    def analyze_filename_with_gemini(filename):
        """
        Gửi tên file cho Gemini để phân tích: Tên Game, Version, Nguồn, Password, VÀ FILE EXE.
        """
        if not configure_gemini():
            return None

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Cập nhật Prompt: Yêu cầu đoán thêm "launch_file"
            prompt = f"""
            Analyze this filename carefully: "{filename}"

            You are an expert in game modification and installation.
            Your task is to deduce metadata, the likely extraction password, AND THE LIKELY LAUNCH EXECUTABLE (.exe).

            Rules:
            1. Password Deduction: 
            - "LinkNeverDie" -> "linkneverdie.com"
            - "khiphach" -> "khiphach.vn"
            - "daominhha" -> "daominhha.com"
            - "GOG" -> often empty or "gog.com"
            - Else -> empty.
            2. Launch File Deduction:
            - Based on the Game Name, predict the standard .exe file name.
            - Example: "Elden Ring" -> "eldenring.exe", "League of Legends" -> "LeagueClient.exe".
            - If unsure, guess based on the game title (e.g. "GameName.exe").

            Return ONLY a JSON object with these keys:
            {{
                "game_name": "Clean name of the game",
                "version": "The version string (e.g. v1.02)",
                "file_type": "zip, rar, or exe",
                "password": "The deduced password",
                "launch_file": "The predicted executable name (e.g. game.exe)"
            }}
            """

            response = model.generate_content(prompt)
            
            text_res = response.text.strip()
            if text_res.startswith("```"):
                text_res = text_res.replace("```json", "").replace("```", "")
            
            import json
            data = json.loads(text_res)
            return data

        except Exception as e:
            print(f"Lỗi Gemini: {e}")
            return None
    # --- SỬA LẠI PHẦN NÀY ---

    def apply_ui_update_from_thread(callback, *args):
        """Hàm helper để chuyển lệnh vẽ UI về luồng chính an toàn."""
        root.after(0, callback, *args)

    def _ui_update_gemini_results(ai_data, real_filename, file_id):
        """Hàm này CHẠY TRÊN LUỒNG CHÍNH để điền thông tin vào Form."""
        global g_game_themes, g_master_game_list
        
        try:
            # 1. Điền URL/ID (Đã sửa cho Widget Text)
            url_entry = form_widgets.get("URL:")
            if url_entry:
                url_entry.delete("1.0", tk.END) # Sửa 0 thành "1.0"
                url_entry.insert("1.0", file_id) # Sửa 0 thành "1.0"

            if not ai_data:
                custom_showwarning("Gemini Error", "Gemini không trả về kết quả hợp lệ.")
                return
            
            detected_game_name = ai_data.get("game_name")

            # --- LOGIC MỚI: TỰ ĐỘNG THÊM GAME NẾU THIẾU ---
            if detected_game_name:
                # Chuẩn hóa tên (bỏ khoảng trắng thừa)
                detected_game_name = detected_game_name.strip()
                
                # Lấy danh sách hiện tại
                combobox = form_widgets.get("Game:")
                current_games = list(combobox['values']) if combobox else []
                
                # Kiểm tra xem tên game đã có trong danh sách chưa (so sánh không phân biệt hoa thường)
                found = False
                best_match = ""
                
                # Tìm khớp tương đối
                for game in current_games:
                    if game == "Thêm Game...": continue
                    if detected_game_name.lower() == game.lower():
                        best_match = game
                        found = True
                        break
                
                # NẾU CHƯA CÓ -> TỰ ĐỘNG TÌM ẢNH VÀ THÊM VÀO
                if not found:
                    print(f"Game '{detected_game_name}' chưa có trong hệ thống. Đang tự động thêm...")
                    
                    # 1. Tìm URL ảnh
                    # Lưu ý: Hàm tìm ảnh nên chạy nhanh hoặc đã chạy ở thread trước. 
                    # Tuy nhiên để đơn giản ta gọi ở đây (sẽ làm UI khựng nhẹ 1s, chấp nhận được)
                    # Hoặc lý tưởng nhất là gọi nó trong process_smart_paste_background rồi truyền vào đây.
                    # Để an toàn cho UI, tôi sẽ dùng ảnh mặc định trước, rồi tìm ảnh sau nếu cần.
                    
                    # Cách tối ưu: Gọi tìm ảnh ngay tại đây (chấp nhận khựng xíu để có ảnh ngay)
                    new_image_url = find_game_image_url_online(detected_game_name)
                    
                    if new_image_url:
                        # 2. Thêm vào g_game_themes
                        g_game_themes[detected_game_name] = new_image_url
                        
                        # 3. Cập nhật danh sách tổng (g_master_game_list)
                        if 'g_master_game_list' in globals():
                            if detected_game_name not in g_master_game_list:
                                g_master_game_list.append(detected_game_name)
                                g_master_game_list.sort()
                        
                        # 4. Cập nhật Combobox
                        new_values = sorted(list(g_game_themes.keys())) + ["Thêm Game..."]
                        if combobox:
                            combobox['values'] = new_values
                            combobox.set(detected_game_name) # Chọn luôn game mới
                        
                        # 5. (Tùy chọn) Tự động Upload Theme lên GitHub để lưu lại
                        # threading.Thread(target=upload_theme_json_thread, args=(detected_game_name,), daemon=True).start()
                        print(f"Đã tự động thêm game mới: {detected_game_name}")
                        
                        best_match = detected_game_name
                    else:
                        # Nếu không tìm thấy ảnh, vẫn điền tên vào ô nhưng không thêm vào list chính thức
                        # để người dùng tự xử lý
                        if combobox: combobox.set(detected_game_name)
                
                else:
                    # Nếu đã có thì chọn luôn
                    if combobox: combobox.set(best_match)

            # --- CÁC PHẦN KHÁC GIỮ NGUYÊN ---

            # 3. Điền Tên Option
            opt_name = ai_data.get("game_name", "")
            if ai_data.get("version"):
                opt_name += f" {ai_data['version']}"
            
            entry_opt = form_widgets.get("Option Name:")
            if entry_opt:
                entry_opt.delete(0, tk.END)
                entry_opt.insert(0, opt_name)

            # 4. Điền Version
            entry_ver = form_widgets.get("Version:")
            if entry_ver:
                entry_ver.delete(0, tk.END)
                entry_ver.insert(0, ai_data.get("version", ""))

            # 5. Điền Loại File
            ext = ai_data.get("file_type", "zip").lower()
            combo_type = form_widgets.get("Type:")
            if combo_type:
                if "rar" in ext: combo_type.set("rar")
                elif "exe" in ext: combo_type.set("exe")
                else: combo_type.set("zip")

            # 6. Điền Mật Khẩu
            detected_pass = ai_data.get("password", "")
            entry_pass = form_widgets.get("Password:")
            if entry_pass:
                entry_pass.delete(0, tk.END)
                entry_pass.insert(0, detected_pass)

            # 7. Điền Launch File (File EXE)
            detected_launch = ai_data.get("launch_file", "")
            entry_launch = form_widgets.get("Launch File:")
            if entry_launch:
                entry_launch.delete(0, tk.END)
                entry_launch.insert(0, detected_launch)

            # 8. Thông báo
            msg = f"Gemini Xong!\nGame: {ai_data.get('game_name')}\nExe: {detected_launch}\nPass: {detected_pass}"
            custom_showinfo("Thành công", msg)

        except Exception as e:
            print(f"Lỗi khi update UI: {e}")

    def process_smart_paste_background(content):
        """
        Chạy ngầm: Chỉ gọi API, KHÔNG được chạm vào widget UI.
        """
        try:
            file_id = extract_gdrive_id_from_url(content)
            
            if not file_id:
                # Nếu lỗi, gửi lệnh về UI để hiện thông báo
                apply_ui_update_from_thread(lambda: custom_showwarning("Lỗi", "Không tìm thấy ID Google Drive hợp lệ."))
                return

            # Kiểm tra Drive Service
            global drive_service
            if not drive_service:
                apply_ui_update_from_thread(lambda: custom_showinfo("Yêu cầu", "Vui lòng Đăng nhập Drive ở Tab 3 để lấy tên file gốc."))
                return

            # 1. Lấy tên file gốc từ Drive (Mạng)
            try:
                file_meta = drive_service.files().get(
                    fileId=file_id,
                    fields='name, size, fileExtension'
                ).execute()
                
                real_filename = file_meta.get('name', 'Unknown')
                print(f"File gốc trên Drive: {real_filename}")
                
                # 2. Gọi GEMINI để phân tích (Mạng - Rất nặng)
                print(f"Đang gửi tên file cho Gemini phân tích: {real_filename}")
                
                ai_data = analyze_filename_with_gemini(real_filename)
                
                # 3. Đã có dữ liệu -> Gọi hàm vẽ UI trên luồng chính
                apply_ui_update_from_thread(_ui_update_gemini_results, ai_data, real_filename, file_id)

            except Exception as e:
                print(f"Lỗi Drive/Gemini: {e}")
                apply_ui_update_from_thread(lambda: custom_showerror("Lỗi API", f"Có lỗi khi gọi API: {e}"))

        except Exception as e:
            print(f"Lỗi chung: {e}")

    def action_smart_paste():
        """Hàm kích hoạt nút Paste (Đã sửa cho Widget Text)."""
        try:
            content = root.clipboard_get().strip()
        except:
            custom_showwarning("Lỗi", "Clipboard trống hoặc không đọc được.")
            return

        print("Đang bắt đầu xử lý Smart Paste...")
        
        # --- [SỬA LỖI] Dùng index "1.0" thay vì 0 ---
        if "URL:" in form_widgets:
            form_widgets["URL:"].delete("1.0", tk.END)
            form_widgets["URL:"].insert("1.0", "Đang xử lý AI...")

        # Chạy luồng ngầm
        threading.Thread(target=process_smart_paste_background, args=(content,), daemon=True).start()

    def open_drive_picker_modal():
        """Mở popup chọn file từ Drive (dùng dữ liệu cache từ Tab 3)."""
        if not hasattr(root, 'drive_icon_zip'): # Check nếu resource chưa load
             custom_showerror("Lỗi", "Vui lòng tải danh sách file ở Tab 3 trước.")
             return

        picker = tk.Toplevel(root)
        picker.title("Chọn File từ Drive")
        center_window_on_screen(picker, 500, 400)
        picker.transient(root)
        picker.grab_set()
        
        # Tiêu đề
        ttk.Label(picker, text="Click đúp vào file để chọn:", font=("Segoe UI", 10, "bold")).pack(pady=10)

        # Listbox
        list_frame = ttk.Frame(picker, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        lb = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        lb.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=lb.yview)

        file_map = {} # Map index -> file info

        def load_list():
            try:
                # Gọi API trực tiếp cho chắc ăn
                if not drive_service:
                    lb.insert(tk.END, "Lỗi: Chưa đăng nhập Drive (Tab 3).")
                    return

                files = drive_service.files().list(
                    q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false",
                    fields='files(id, name)', orderBy='name').execute().get('files', [])
                
                for idx, f in enumerate(files):
                    lb.insert(tk.END, f"📄 {f['name']}")
                    file_map[idx] = f
            except Exception as e:
                lb.insert(tk.END, f"Lỗi tải: {e}")

        threading.Thread(target=load_list, daemon=True).start()

        def on_select(event=None):
            selection = lb.curselection()
            if not selection: return
            idx = selection[0]
            if idx in file_map:
                f = file_map[idx]
                
                # --- AUTO FILL LOGIC (ĐÃ SỬA LỖI) ---
                
                # 1. Fill ID vào ô Text Widget (Thông qua form_widgets)
                if "URL:" in form_widgets:
                    url_widget = form_widgets["URL:"]
                    url_widget.delete("1.0", tk.END)
                    url_widget.insert("1.0", f['id'])
                
                # 2. Fill Name (Auto Clean)
                if "Option Name:" in form_widgets:
                    clean_name = os.path.splitext(f['name'])[0] # Bỏ đuôi
                    clean_name = clean_name.replace("_", " ").replace("-", " ")
                    form_widgets["Option Name:"].delete(0, tk.END)
                    form_widgets["Option Name:"].insert(0, clean_name)
                
                # 3. Detect Type
                if "Type:" in form_widgets:
                    ext = os.path.splitext(f['name'])[1].lower()
                    if ".zip" in ext: form_widgets["Type:"].set("zip")
                    elif ".rar" in ext: form_widgets["Type:"].set("rar")
                    elif ".exe" in ext: form_widgets["Type:"].set("exe")
                
                picker.destroy()
                custom_showinfo("Auto-Fill", f"Đã điền thông tin từ file:\n{f['name']}")

        lb.bind("<Double-Button-1>", on_select)
        ttk.Button(picker, text="Chọn File Này", command=on_select, style="Accent.TButton").pack(pady=10)
    # (Giữ nguyên các nút chức năng cũ nhưng trỏ vào widget mới nếu cần)
    # ttk.Button(btn_row, text="📋 Paste", width=8, command=action_smart_paste).pack(side=tk.RIGHT, padx=2)
    btn_drive_picker = ttk.Button(btn_row, text="🔍 Chọn từ Drive", command=open_drive_picker_modal, style="Accent.TButton")
    btn_drive_picker.pack(side=tk.RIGHT, padx=2)
    # Hàng 2: Tên Option & Version
    row2 = ttk.Frame(basic_info_frame)
    row2.pack(fill=tk.X)
    
    # Tên Option (chiếm 70%)
    f_name, w_name = create_modern_input(row2, "Tên Hiển Thị (Option Name):", "Option Name:")
    f_name.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Version (chiếm 30%)
    f_ver, w_ver = create_modern_input(row2, "Version:", "Version:")
    f_ver.pack(side=tk.LEFT, fill=tk.X) # Không expand
    w_ver.config(width=10)

    # Hàng 3: Game & Type
    row3 = ttk.Frame(basic_info_frame)
    row3.pack(fill=tk.X)
    
    # --- Game Combobox (Kèm nút thêm nhanh) ---
    game_frame = ttk.Frame(row3, padding=(10, 5))
    game_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    ttk.Label(game_frame, text="Game:", style="secondary.TLabel").pack(anchor=tk.W)
    
    
    # Tạo một frame con để chứa Combobox và Nút nằm ngang hàng
    game_input_group = ttk.Frame(game_frame)
    game_input_group.pack(fill=tk.X, pady=2)

    global g_admin_game_combobox
    g_admin_game_combobox = ttk.Combobox(game_input_group, values=[], state="normal")
    g_admin_game_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Nút Thêm Game (+)
    btn_add_game_theme = ttk.Button(game_input_group, text="➕", width=3, 
                                  command=open_game_theme_manager, style="Accent.TButton")
    btn_add_game_theme.pack(side=tk.LEFT, padx=(5, 0))
    CreateToolTip(btn_add_game_theme, "Mở Quản lý Game (Thêm/Xóa tên Game trong danh sách)")

    # Bindings cho Combobox
    g_admin_game_combobox.bind("<<ComboboxSelected>>", lambda e: on_game_combobox_select(e))
    g_admin_game_combobox.bind("<KeyRelease>", lambda e: on_game_combobox_search(e))
    g_admin_game_combobox.bind("<FocusOut>", lambda e: on_game_combobox_validate(e))
    
    form_widgets["Game:"] = g_admin_game_combobox

    # --- Type Combobox ---
    f_type, w_type = create_modern_input(row3, "Loại File:", "Type:", "Combobox", options=["zip", "rar", "exe"])
    f_type.pack(side=tk.LEFT, padx=(5, 0))
    w_type.config(width=8)

    # --- NHÓM 2: CẤU HÌNH CÀI ĐẶT (Card Layout) ---
    install_config_frame = ttk.LabelFrame(edit_form_frame, text="⚙️ Cấu Hình Cài Đặt", padding=10)
    install_config_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # Launch File & Password
    row4 = ttk.Frame(install_config_frame)
    row4.pack(fill=tk.X)
    
    f_launch, w_launch = create_modern_input(row4, "File Khởi Chạy (.exe):", "Launch File:")
    f_launch.pack(side=tk.LEFT, fill=tk.X, expand=True)
    CreateToolTip(w_launch, "Tên file exe game (vd: EldenRing.exe).\nDùng để kiểm tra và kích hoạt nút 'Chạy Game'.")

    f_pass, w_pass = create_modern_input(row4, "Mật khẩu giải nén (nếu có):", "Password:")
    f_pass.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
    # --- [MỚI] HÀNG 5: TAG/STICKER ---
    row5 = ttk.Frame(install_config_frame)
    row5.pack(fill=tk.X)
    
    # Tạo danh sách các Tag có sẵn cho Combobox
    tag_options = sorted(list(TAG_COLORS.keys()))
    tag_options.insert(0, "") # Thêm giá trị trống (mặc định: không tag)

    f_tag, w_tag = create_modern_input(row5, "Gắn Tag (HOT/GOTY/UPD...):", "Game Tag:", "Combobox", options=tag_options)
    f_tag.pack(side=tk.LEFT, fill=tk.X, expand=True)
    w_tag.config(width=15)
    CreateToolTip(w_tag, "Gắn nhãn (sticker) lên ảnh game ở Sidebar.\nĐể trống nếu không muốn gắn Tag.")
    # Path Guide
    create_modern_input(install_config_frame, "Hướng dẫn (Hiện ở Tab 1):", "Path Guide:", "Text", height=2)

    # Delete List
    create_modern_input(install_config_frame, "Xóa file cũ trước khi cài (Mỗi dòng 1 file/folder):", "Delete List:", "Text", height=3)

    # --- ACTION BUTTONS ---
    action_btn_frame = ttk.Frame(edit_form_frame, padding=20)
    action_btn_frame.pack(fill=tk.X)

    add_update_button = ttk.Button(action_btn_frame, text="✅ Lưu / Cập Nhật Option", command=action_add_update_option, style="Accent.TButton")
    add_update_button.pack(side=tk.RIGHT, padx=5)
    
    delete_option_btn = ttk.Button(action_btn_frame, text="🗑️ Xóa Option", command=action_delete_option, style="Danger.TButton")
    delete_option_btn.pack(side=tk.RIGHT, padx=5)

    toggle_edit_form_state(False)

    # --- FOOTER: Status & Global Actions ---
    bottom_status_frame = ttk.Frame(second_tab_frame)
    bottom_status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    # Thanh trạng thái riêng cho Tab 2
    upload_status_label = ttk.Label(bottom_status_frame, text="Sẵn sàng.", anchor=tk.W)
    upload_status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=10)

    # Global Actions (Tải Config / Upload Config)
    # Tái sử dụng frame bottom_status_frame đã tạo ở ngoài
    global_actions_frame = ttk.Frame(bottom_status_frame)
    global_actions_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
    
    ttk.Button(global_actions_frame, text="☁️ Tải Config (GitHub)", command=action_load_from_github_wrapper).pack(side=tk.LEFT, padx=5)
    ttk.Button(global_actions_frame, text="💾 Upload Config (GitHub)", command=action_upload_to_github_wrapper, style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
    
    # --- LOGIC GẮN KẾT TREEVIEW VÀ FORM (Giữ nguyên logic cũ nhưng cập nhật widget reference) ---
    def populate_treeview():
        options_treeview.delete(*options_treeview.get_children())
        if not current_config_data: return
        for key, data in current_config_data.items():
            if key == "updater": continue
            # Chỉ hiển thị ID, Tên, Game trong bảng
            options_treeview.insert("", tk.END, iid=key, values=(key, data.get("name", "??"), data.get("game", "Khác")))

    def on_treeview_select(event):
        """Điền dữ liệu vào Form Hiện Đại (Hỗ trợ Multi-URL)."""
        if current_config_data: 
             toggle_edit_form_state(True)
        selected_items = options_treeview.selection()
        if not selected_items:
            clear_form()
            return

        selected_key = selected_items[0]
        global g_currently_selected_id
        g_currently_selected_id = selected_key

        if selected_key in current_config_data:
            data = current_config_data[selected_key]
            
            # Cập nhật tiêu đề
            form_title_label.config(text=f"✏️ Đang sửa: {data.get('name')} (ID: {selected_key})")
            
            # Fill Basic Info
            form_widgets["Option Name:"].delete(0, tk.END)
            form_widgets["Option Name:"].insert(0, data.get("name") or "")

            # --- [CẬP NHẬT] URL Logic (Hỗ trợ List) ---
            url_widget = form_widgets["URL:"]
            url_widget.delete("1.0", tk.END) # Xóa nội dung cũ
            
            # 1. Kiểm tra list 'urls' trước
            urls_list = data.get("urls", [])
            
            # 2. Nếu không có list, kiểm tra single 'url' (backward compatibility)
            if not urls_list:
                single_url = data.get("url")
                if single_url:
                    urls_list = [single_url]
            
            # 3. Hiển thị lên Text widget (Mỗi link 1 dòng)
            if urls_list:
                # Xử lý prefix ID cũ nếu cần (tùy chọn, ở đây ta hiển thị full link cho dễ quản lý)
                display_text = "\n".join(urls_list)
                url_widget.insert("1.0", display_text)

            # ... (Các phần dưới giữ nguyên: Version, Game, Type...) ...
            form_widgets["Version:"].delete(0, tk.END)
            form_widgets["Version:"].insert(0, data.get("version") or "")
            
            form_widgets["Game:"].set("")
            form_widgets["Game:"].insert(0, data.get("game") or "Khác")
            
            form_widgets["Type:"].set(data.get("type", "zip"))
            
            form_widgets["Launch File:"].delete(0, tk.END)
            form_widgets["Launch File:"].insert(0, data.get("launch_file") or "")
            
            form_widgets["Password:"].delete(0, tk.END)
            form_widgets["Password:"].insert(0, data.get("password") or "")
            form_widgets["Game Tag:"].set(data.get("tag") or "")
            guide_widget = form_widgets["Path Guide:"]
            guide_widget.delete("1.0", tk.END)
            if data.get("path_guide"): guide_widget.insert("1.0", data.get("path_guide"))

            delete_list_widget = form_widgets["Delete List:"]
            delete_list_widget.delete("1.0", tk.END)
            delete_items = data.get("delete_before_extract", [])
            if delete_items: delete_list_widget.insert("1.0", "\n".join(delete_items))

    options_treeview.bind('<<TreeviewSelect>>', on_treeview_select)

    def clear_form():
        if "URL:" in form_widgets:
             form_widgets["URL:"].config(state="normal")
        if "Path Guide:" in form_widgets:
             form_widgets["Path Guide:"].config(state="normal")
        if "Delete List:" in form_widgets:
             form_widgets["Delete List:"].config(state="normal")
        global g_currently_selected_id
        g_currently_selected_id = None
        form_title_label.config(text="✨ Thêm Option Mới")
        
        # Xóa nội dung tất cả widget
        form_widgets["Option Name:"].delete(0, tk.END)
        
        # [CẬP NHẬT] Xóa Text widget
        form_widgets["URL:"].delete("1.0", tk.END)
        
        form_widgets["Version:"].delete(0, tk.END)
        form_widgets["Game:"].set("") 
        form_widgets["Type:"].set("zip")
        form_widgets["Launch File:"].delete(0, tk.END)
        form_widgets["Password:"].delete(0, tk.END)
        form_widgets["Path Guide:"].delete("1.0", tk.END)
        form_widgets["Delete List:"].delete("1.0", tk.END)
        
        if options_treeview.selection():
            options_treeview.selection_remove(options_treeview.selection())

    # --- THÊM MỚI: HÀM LOGIC SEARCH (DEBOUNCED) ---
    def do_game_search():
        """Lọc danh sách dropdown (được gọi sau khi hết giờ hẹn)."""
        global g_master_game_list, g_admin_game_combobox, g_search_timer
        g_search_timer = None # Xóa timer

        current_text = g_admin_game_combobox.get().lower()

        if not current_text:
            filtered_list = g_master_game_list + ["Thêm Game..."]
        else:
            filtered_list = [game for game in g_master_game_list if current_text in game.lower()]
            filtered_list.append("Thêm Game...")

        g_admin_game_combobox['values'] = filtered_list
        g_admin_game_combobox.event_generate('<Down>')


    # --- THÊM MỚI: LOGIC SEARCH VÀ VALIDATE CHO COMBOBOX ---
    def on_game_combobox_search(event):
        """Hẹn giờ lọc danh sách (debounce) sau khi người dùng gõ."""
        global g_search_timer

        # Nếu đang có hẹn giờ cũ, hủy nó
        if g_search_timer:
            root.after_cancel(g_search_timer)

        g_search_timer = root.after(1000, do_game_search)

    def on_game_combobox_validate(event):
        """
        Xử lý khi chọn game: Kiểm tra hợp lệ và đổi màu chữ.
        """
        widget = event.widget
        val = widget.get().strip()
        
        if not val:
            return

        # Logic kiểm tra:
        # Nếu game có trong master list -> Hợp lệ (Màu trắng/Mặc định)
        # Nếu game mới tự nhập -> Cảnh báo nhẹ (Màu vàng)
        if val in g_master_game_list:
            try:
                widget.config(foreground="white") # Hoặc để trống nếu dùng theme mặc định
            except: pass 
        else:
            # Báo hiệu đây là Game Mới (sẽ được tạo mới khi Lưu)
            try:
                widget.config(foreground="#ffcc00") # Màu vàng
            except: pass
            
        # Mẹo: In ra console để debug nếu cần
        # print(f"Validate Game: {val} | Exists: {val in g_master_game_list}")



    def on_game_combobox_select(event):
        """Được gọi khi chọn item trong dropdown Game."""
        selected_game = g_admin_game_combobox.get()
        if selected_game == "Thêm Game...":
            # Mở modal quản lý
            open_game_theme_manager()
            # Xóa lựa chọn "Thêm Game..."
            g_admin_game_combobox.set("")

    

    def populate_theme_listbox():
        """Làm mới Listbox trong modal."""
        if not g_theme_listbox: return

        g_theme_listbox.delete(0, tk.END)
        sorted_games = sorted(g_game_themes.keys())
        for game_name in sorted_games:
            g_theme_listbox.insert(tk.END, game_name)

    def action_add_game_theme():
        global g_game_themes
        
        # Lấy dữ liệu
        name = g_theme_name_entry.get().strip()
        
        # --- SỬA ĐOẠN NÀY ---
        raw_text = g_theme_url_text.get("1.0", tk.END).strip()
        url_list = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Ảnh đầu tiên làm đại diện, cả list làm slideshow
        main_image = url_list[0] if url_list else ""
        # --------------------

        
        if not name or not main_image:
            custom_showerror("Thiếu thông tin", "Vui lòng nhập Tên Game và ít nhất 1 Link Ảnh.", parent=g_theme_manager_window)
            return

        # Lưu cấu trúc mới
        theme_data = {
            "slideshow": url_list,      # Danh sách đầy đủ
        }

        # --- LOGIC QUAN TRỌNG ĐÃ SỬA ---
        # Trước đây: if name in g_game_themes: báo lỗi -> return
        # Bây giờ: Chỉ cần gán thẳng vào dictionary. Nó sẽ tự động cập nhật nếu đã có.
        
        is_update = name in g_game_themes
        g_game_themes[name] = theme_data
        populate_theme_listbox()
        threading.Thread(target=upload_theme_json_thread, args=(name,), daemon=True).start()
        
        # Thông báo thành công
        action_text = "Cập nhật" if is_update else "Thêm mới"
        messagebox.showinfo("Thành công", f"Đã {action_text} game '{name}' thành công!\nDữ liệu đang được đồng bộ lên server.", parent=g_theme_manager_window)

        # (Tùy chọn) Xóa form sau khi thêm mới (nhưng giữ lại nếu cập nhật để tiện sửa tiếp)
        if not is_update:
            g_theme_name_entry.delete(0, tk.END)
            if 'g_theme_url_text' in globals() and g_theme_url_text.winfo_exists():
                g_theme_url_text.delete("1.0", tk.END)

    def action_delete_game_theme():
        """Logic cho nút 'Xóa' trong modal."""
        global g_game_themes
        try:
            selected_game = g_theme_listbox.get(g_theme_listbox.curselection())
        except tk.TclError:
            custom_showwarning("Chưa chọn", "Vui lòng chọn một game trong danh sách để xóa.", parent=g_theme_manager_window)
            return

        if custom_askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa game theme '{selected_game}'?\n(Việc này không xóa các mod option.)", parent=g_theme_manager_window):
            if selected_game in g_game_themes:
                del g_game_themes[selected_game]
                # Bắt đầu upload (không cần tên)
                threading.Thread(target=upload_theme_json_thread, 
                                args=(None,), 
                                daemon=True).start()

    def upload_theme_json_thread(newly_added_game_name=None):
        """(Chạy ngầm) Upload file game_themes.json."""
        global g_game_theme_sha

        repo = get_github_repo()
        if not repo:
            progress_queue.put(("theme_upload_failed", "Không thể kết nối repo."))
            return

        # Gửi dict g_game_themes hiện tại
        success, new_sha = upload_theme_json_to_github(repo, g_game_themes, g_game_theme_sha)

        if success and new_sha:
            progress_queue.put(("theme_upload_success", (new_sha, newly_added_game_name)))
        else:
            progress_queue.put(("theme_upload_failed", "Upload thất bại. (Xem log GitHub)"))


    add_update_button.config(command=action_add_update_option)
    # --- Hết phần sửa cho Tab 2 ---


    # --- BẮT ĐẦU CODE CHO TAB 3 ("Upload Lên Drive") ---
    third_tab_frame = ttk.Frame(notebook, padding=(10, 10))
    notebook.add(third_tab_frame, text=" Upload Lên Drive ")

    drive_storage_label = ttk.Label(third_tab_frame, text="Dung lượng Drive: Đang tải...", style="secondary.TLabel", anchor=tk.W)
    # --- Các biến và hàm cho Tab 3 ---
    # Biến này sẽ lưu danh sách các đường dẫn file đã kéo vào
    files_to_upload_list = []

    def action_browse_upload_files():
        """Thay thế cho việc kéo thả file vào Tab 3."""
        # Cho phép chọn nhiều file
        file_paths = filedialog.askopenfilenames(title="Chọn file để upload lên Drive")
        
        if file_paths:
            # Xóa danh sách cũ (giống logic kéo thả cũ)
            files_to_upload_list.clear()
            drop_target_listbox.delete(0, tk.END)
            
            for path in file_paths:
                files_to_upload_list.append(path)
                drop_target_listbox.insert(tk.END, os.path.basename(path))
                
            # Bật nút upload
            upload_files_button.config(state=tk.NORMAL)

    def handle_drop_enter(event):
        # Thay đổi giao diện khi chuột kéo file vào
        drop_target_listbox.config(background="lightblue")
        
    def handle_drop_leave(event):
        # Trả lại giao diện cũ
        drop_target_listbox.config(background=style.lookup("TListbox", "background"))

    def handle_drop(event):
        # Xử lý khi người dùng thả file
        handle_drop_leave(event) # Trả lại màu nền
        # event.data chứa một chuỗi các đường dẫn file
        # Chúng có thể được bọc trong dấu {} nếu chứa dấu cách
        
        # Xóa danh sách cũ
        files_to_upload_list.clear()
        drop_target_listbox.delete(0, tk.END)
        
        # Phân tích chuỗi file paths (hơi phức tạp)
        raw_paths = root.tk.splitlist(event.data)
        
        for file_path in raw_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path): # Chỉ chấp nhận file
                files_to_upload_list.append(file_path)
                drop_target_listbox.insert(tk.END, os.path.basename(file_path))
            else:
                print(f"Bỏ qua: {file_path} (không phải file hoặc không tồn tại)")
        
        upload_files_button.config(state=tk.NORMAL) # Bật nút upload

    def update_user_ui_on_main_thread(name, email, avatar_bytes):
        """
        Cập nhật giao diện Titlebar và Xử lý Đăng xuất.
        """
        global g_titlebar_google_frame, drive_service
        
        BG_TITLEBAR = "#1c1c1c"
        BG_HOVER = "#333333"
        FG_TEXT = "#ffffff"
        
        if 'drive_auth_button' in globals():
            drive_auth_button.config(text="Đã kết nối Drive", style="Green.TButton",state=tk.DISABLED)
            
        if g_titlebar_google_frame:
            for widget in g_titlebar_google_frame.winfo_children():
                widget.destroy()
            
            profile_frame = tk.Frame(g_titlebar_google_frame, bg=BG_TITLEBAR, cursor="hand2", padx=10, pady=2)
            profile_frame.pack(fill=tk.Y, side=tk.RIGHT)

            if avatar_bytes:
                avatar_tk = make_circle_avatar(avatar_bytes, size=(24, 24))
                root.cached_images["auto_user_avatar"] = avatar_tk 
                lbl_avt = tk.Label(profile_frame, image=avatar_tk, bg=BG_TITLEBAR, bd=0)
                lbl_avt.pack(side=tk.LEFT, padx=(0, 8))
            else:
                lbl_avt = tk.Label(profile_frame, text="👤", bg=BG_TITLEBAR, fg=FG_TEXT, font=("Segoe UI", 12))
                lbl_avt.pack(side=tk.LEFT, padx=(0, 8))

            lbl_name = tk.Label(profile_frame, text=name, bg=BG_TITLEBAR, fg=FG_TEXT, font=("Segoe UI", 9))
            lbl_name.pack(side=tk.LEFT)

            # --- LOGIC ĐĂNG XUẤT (ĐÃ SỬA) ---
            def perform_logout():
                global drive_service, g_accounts_loaded # Thêm g_accounts_loaded
                
                # 1. Xóa file token
                token_path = resource_path('token.json')
                if os.path.exists(token_path):
                    try: os.remove(token_path)
                    except: pass
                
                # 2. Reset biến toàn cục
                drive_service = None
                
                # 3. Reset giao diện Tab 3
                if 'drive_auth_button' in globals():
                    drive_auth_button.config(text="Đăng nhập Google Drive", state=tk.NORMAL, style="Accent.TButton")
                if 'upload_files_button' in globals():
                    upload_files_button.config(state=tk.DISABLED)
                    
                # 4. Reset Title Bar
                if g_titlebar_google_frame:
                    for widget in g_titlebar_google_frame.winfo_children():
                        widget.destroy()
                    
                    btn_login = tk.Button(
                        g_titlebar_google_frame,
                        text=" Đăng nhập ", 
                        bg="#4285F4", fg="white",
                        font=("Segoe UI", 9, "bold"), bd=0,
                        cursor="hand2", command=action_drive_login,
                        relief="flat"
                    )
                    btn_login.pack(ipady=4, pady=4)
                    btn_login.bind("<Enter>", lambda e: btn_login.config(bg="#357ae8"))
                    btn_login.bind("<Leave>", lambda e: btn_login.config(bg="#4285F4"))

                custom_showinfo("Đăng xuất", "Đã đăng xuất thành công.")

                # --- [FIX LỖI] LÀM MỚI TAB SHARE ACC (CHUYỂN VỀ GUEST MODE) ---
                print("Logout OK -> Reloading Accounts in Guest Mode...")
                g_accounts_loaded = False # Reset cờ để ép tải lại
                # Tải lại account (Lúc này drive_service = None nên nó sẽ tải bản Public và khóa nút)
                threading.Thread(target=load_accounts_from_drive_thread, daemon=True).start()
                # -------------------------------------------------------------

            def show_user_menu(e):
                menu = tk.Menu(root, tearoff=0)
                menu.add_command(label=f"📧 {email}", state=tk.DISABLED)
                menu.add_separator()
                menu.add_command(label="Đăng xuất", command=perform_logout)
                x = profile_frame.winfo_rootx()
                y = profile_frame.winfo_rooty() + profile_frame.winfo_height()
                menu.post(x, y)

            def on_enter(e):
                profile_frame.config(bg=BG_HOVER)
                lbl_avt.config(bg=BG_HOVER)
                lbl_name.config(bg=BG_HOVER)

            def on_leave(e):
                profile_frame.config(bg=BG_TITLEBAR)
                lbl_avt.config(bg=BG_TITLEBAR)
                lbl_name.config(bg=BG_TITLEBAR)

            for widget in [profile_frame, lbl_avt, lbl_name]:
                widget.bind("<Button-1>", show_user_menu)
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

    def try_auto_login_drive_thread():
        """(Chạy ngầm) Tự động đăng nhập User VÀ kích hoạt tải dữ liệu."""
        global drive_service
        
        token_path = resource_path('token.json')
        creds_path = resource_path('credentials.json')
        
        # --- LOGIC MỚI: Tách biệt việc Login và việc Tải Dữ Liệu ---
        
        # 1. Thử Đăng nhập (Chỉ chạy nếu có token)
        if os.path.exists(creds_path) and os.path.exists(token_path):
            try:
                print("Auto-Login: Đang kiểm tra token...")
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                
                # Làm mới token nếu hết hạn
                if not creds.valid and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                if creds.valid:
                    # Khởi tạo Drive Service
                    drive_service = build('drive', 'v3', credentials=creds)
                    print("Auto-Login: Drive Service OK.")
                    
                    # Lấy thông tin User (Avatar, Tên)
                    try:
                        user_service = build('oauth2', 'v2', credentials=creds)
                        user_info = user_service.userinfo().get().execute()
                        
                        name = user_info.get('name', 'User')
                        email = user_info.get('email', '')
                        pic_url = user_info.get('picture', '')
                        
                        # Tải ảnh avatar
                        avatar_data = None
                        if pic_url:
                            try:
                                res = requests.get(pic_url, timeout=5)
                                if res.status_code == 200:
                                    avatar_data = res.content
                            except: pass
                        
                        # Cập nhật UI Avatar
                        root.after(0, lambda: update_user_ui_on_main_thread(name, email, avatar_data))
                        
                        # Refresh list file ở Tab 3
                        root.after(0, action_refresh_drive_list) 
                        
                    except Exception as e:
                        print(f"Auto-Login Warning: Không thể lấy info user ({e})")
                else:
                    print("Auto-Login: Token không hợp lệ (Hết hạn và không refresh được).")
            except Exception as e:
                print(f"Auto-Login Error: {e}")
        else:
            print("Auto-Login: Chưa có file token (Chế độ Guest).")

        # 2. QUAN TRỌNG NHẤT: Luôn luôn gọi hàm tải dữ liệu account
        # Bất kể có đăng nhập được hay không, vẫn phải chạy hàm này để nó tải file Public
        print("Auto-Login: Gọi hàm tải Account...")
        load_accounts_from_drive_thread()

    def action_drive_login():
        """Đăng nhập và tự động làm mới giao diện Account."""
        global drive_service, g_accounts_loaded
        
        if 'drive_auth_button' in globals():
            drive_auth_button.config(text="Đang kết nối Google...", state=tk.DISABLED)
        root.update_idletasks()
        
        # 1. Xác thực
        service = authenticate_google_drive() 
        
        if service:
            print("Đăng nhập thành công.")
            
            # Cập nhật Tab 3
            if 'drive_auth_button' in globals():
                drive_auth_button.config(text="Đã kết nối Drive", style="Green.TButton")
            if files_to_upload_list and 'upload_files_button' in globals():
                upload_files_button.config(state=tk.NORMAL)
            
            action_refresh_drive_list()

            # 2. Lấy thông tin User
            try:
                token_path = resource_path('token.json')
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                user_service = build('oauth2', 'v2', credentials=creds)
                user_info = user_service.userinfo().get().execute()
                
                name = user_info.get('name', 'User')
                email = user_info.get('email', '')
                pic_url = user_info.get('picture', '')

                avatar_data = None
                if pic_url:
                    try:
                        res = requests.get(pic_url, timeout=5)
                        if res.status_code == 200:
                            avatar_data = res.content
                    except Exception as e:
                        print(f"Lỗi tải avatar: {e}")

                update_user_ui_on_main_thread(name, email, avatar_data)

                # --- [FIX LỖI] LÀM MỚI TAB SHARE ACC (CHUYỂN SANG CHẾ ĐỘ ADMIN) ---
                print("Login OK -> Reloading Accounts in Admin Mode...")
                g_accounts_loaded = False # Reset cờ để ép tải lại
                threading.Thread(target=load_accounts_from_drive_thread, daemon=True).start()
                # ------------------------------------------------------------------

            except Exception as e:
                print(f"Lỗi lấy info sau đăng nhập: {e}")
                update_user_ui_on_main_thread("User", "", None)

        else:
            if 'drive_auth_button' in globals():
                drive_auth_button.config(text="Đăng nhập Google Drive", state=tk.NORMAL)

    def show_login_selector_popup():
        """Hiển thị popup chọn phương thức đăng nhập."""
        popup = tk.Toplevel(root)
        popup.title("Đăng Nhập")
        
        # Kích thước & Căn giữa
        w, h = 350, 200
        center_window_on_screen(popup, w, h)
        popup.transient(root)
        popup.grab_set() # Chặn tương tác với cửa sổ chính
        
        # Áp dụng theme cho titlebar (nếu có)
        popup.after(10, lambda: apply_theme_to_titlebar(popup))

        # UI Content
        frame = ttk.Frame(popup, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Chọn tài khoản để tiếp tục:", font=("Segoe UI", 11)).pack(pady=(0, 20))
        
        # --- NÚT 1: GOOGLE DRIVE ---
        def on_google_click():
            popup.destroy() # Đóng popup trước
            action_drive_login() # Gọi hàm đăng nhập gốc (Tab 3)
            
        btn_google = ttk.Button(
            frame, 
            text="Google", 
            command=on_google_click, 
            style="Accent.TButton" # Nút xanh nổi bật
        )
        btn_google.pack(fill=tk.X, ipady=5, pady=5)
        
        # --- NÚT 2: (VÍ DỤ) API KEY RIÊNG ---
        # (Bạn có thể thêm nút nhập API Key thủ công ở đây sau này)
        # btn_apikey = ttk.Button(frame, text="🔑  Sử dụng API Key riêng", ...)
        # btn_apikey.pack(fill=tk.X, ipady=5, pady=5)

        # Nút Đóng
        ttk.Button(frame, text="Hủy bỏ", command=popup.destroy).pack(fill=tk.X, pady=(10, 0))

    # [QUAN TRỌNG] Gán hàm này vào biến toàn cục để Title Bar gọi được
    g_show_login_selector = show_login_selector_popup

    def action_start_upload_all():
        # Bắt đầu upload tất cả các file trong danh sách
        if not drive_service:
            custom_showwarning("Chưa Đăng Nhập", "Vui lòng đăng nhập Google Drive trước.")
            return
            
        if not files_to_upload_list:
            custom_showinfo("Không có file", "Vui lòng kéo file vào ô bên trên trước.")
            return

        # Xóa log cũ
        upload_status_listbox.delete(0, tk.END)
        
        # Vô hiệu hóa nút để tránh bấm nhiều lần
        upload_files_button.config(state=tk.DISABLED)
        drive_auth_button.config(state=tk.DISABLED)

        # Chạy upload trong thread để không treo UI
        def upload_all_thread():
            for file_path in files_to_upload_list:
                # Chúng ta gọi hàm logic trực tiếp
                # (Hoặc có thể tạo thread riêng cho từng file)
                upload_file_logic(file_path, upload_status_listbox)
            
            # Khi xong, bật lại nút
            upload_status_listbox.insert(tk.END, "--- HOÀN THÀNH TẤT CẢ ---")
            upload_status_listbox.see(tk.END)
            upload_files_button.config(state=tk.NORMAL)
            drive_auth_button.config(state=tk.NORMAL)

        threading.Thread(target=upload_all_thread, daemon=True).start()

    def action_clear_upload_list():
        files_to_upload_list.clear()
        drop_target_listbox.delete(0, tk.END)
        upload_status_listbox.delete(0, tk.END)
        upload_files_button.config(state=tk.DISABLED)

    def action_refresh_drive_list():
        """Bọc hàm tải danh sách file vào một thread (an toàn cho UI)."""
        drive_refresh_button.config(state=tk.DISABLED) # Tắt nút

        # --- SỬA LỖI: Xóa item khỏi FRAME LƯỚI, không phải TREEVIEW ---
        # Xóa list cũ và hiện loading
        for widget in drive_icon_content_frame.winfo_children():
            widget.destroy()

        loading_label = ttk.Label(drive_icon_content_frame, text="Đang tải, vui lòng chờ...")
        loading_label.pack(pady=10)
        # --- HẾT SỬA ---

        # Bắt đầu thread để tải
        root.after(100, process_queue)
        threading.Thread(target=refresh_drive_file_list_thread, daemon=True).start()

    def refresh_drive_file_list_thread():
        """(Chạy trong thread) Lấy danh sách file VÀ dung lượng từ Drive."""
        global drive_service
        if not drive_service:
            progress_queue.put(("status", "Lỗi: Vui lòng đăng nhập Drive trước."))
            progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi dữ liệu rỗng
            return

        if GOOGLE_DRIVE_FOLDER_ID == "YOUR_FOLDER_ID_GOES_HERE":
            progress_queue.put(("status", "Lỗi: GOOGLE_DRIVE_FOLDER_ID chưa được set."))
            progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi dữ liệu rỗng
            return

        try:
            # 1. Lấy danh sách file (như cũ)
            query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false"
            response_files = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                orderBy='name' # Sắp xếp theo tên
            ).execute()
            files = response_files.get('files', [])

            # 2. THÊM MỚI: Lấy thông tin dung lượng
            quota_data = drive_service.about().get(fields='storageQuota').execute()
            quota = quota_data.get('storageQuota', {})

            # 3. Gửi cả hai về queue
            progress_queue.put(("drive_data_updated", {"files": files, "quota": quota}))

        except HttpError as error:
            progress_queue.put(("status", f"Lỗi khi tải dữ liệu Drive: {error}"))
            progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi rỗng
        except Exception as e:
            progress_queue.put(("status", f"Lỗi: {e}"))
            progress_queue.put(("drive_data_updated", {"files": [], "quota": None})) # Gửi rỗng

    def action_delete_drive_file_thread(file_id, file_name):
        """(Chạy trong thread) Xóa file khỏi Google Drive."""
        global drive_service
        
        # --- THÊM MỚI: KIỂM TRA, KHÔNG CHO XÓA FILE JSON ---
        if file_name.lower().endswith(".json"):
            custom_showerror("Không thể Xóa", f"Không được phép xóa file này\nFile: {file_name}")
            progress_queue.put(("drive_log", f"Đã chặn thao tác xóa file JSON: {file_name}"))
            return # Dừng hàm ngay lập tức
        # --- HẾT THÊM MỚI ---

        if not drive_service:
            custom_showerror("Lỗi", "Chưa đăng nhập Google Drive.")
            return
        
        try:
            # 3. Thực thi (Giữ nguyên)
            drive_service.files().delete(fileId=file_id).execute()

            # 4. Báo thành công và Yêu cầu Refresh (Giữ nguyên)
            progress_queue.put(("drive_log", f"Đã xóa {file_name} thành công."))
            progress_queue.put(("refresh_drive_list", None)) # <-- Yêu cầu tải lại lưới

        except HttpError as error:
            custom_showerror("Lỗi Xóa", f"Lỗi khi xóa file: {error}")
            progress_queue.put(("drive_log", f"Lỗi khi xóa {file_name}."))
        except Exception as e:
            custom_showerror("Lỗi Xóa", f"Lỗi không xác định: {e}")
            progress_queue.put(("drive_log", f"Lỗi khi xóa {file_name}."))
    # --- Giao diện cho Tab 3 ---

    # --- THÊM MỚI: CÁC HÀM "TRỢ LÝ AI" ---
    def action_start_scan():
        """Bắt đầu quá trình quét lỗi đồng bộ."""
        global scan_loading_window, drive_service

        if not drive_service:
            custom_showerror("Lỗi", "Vui lòng đăng nhập Google Drive trước.")
            return

        # Hiển thị cửa sổ "Đang tải"
        scan_loading_window = tk.Toplevel(root)
        scan_loading_window.title("Đang Quét...")
        center_window_on_screen(scan_loading_window, 350, 100)
        scan_loading_window.transient(root) # Giữ nó luôn ở trên app chính
        scan_loading_window.grab_set() # Chặn tương tác với app chính
        loading_label = ttk.Label(scan_loading_window, text="Đang so sánh file GitHub JSON và Google Drive...")
        loading_label.pack(expand=True, padx=20, pady=20)

        # Bắt đầu luồng quét
        threading.Thread(target=scan_logic_thread, daemon=True).start()

    def scan_logic_thread():
        """(Chạy ngầm) Tải JSON, tải list Drive và so sánh."""
        global drive_service
        errors_list = []
        warnings_list = []

        try:
            # 1. Tải GitHub JSON (dùng hàm đã có của Tab 1)
            print("Scan: Đang tải config GitHub...")
            github_data = load_config_from_github()
            if not github_data:
                github_data = fallback_options # Dùng fallback nếu tải lỗi

            # 2. Tải danh sách file Google Drive
            print("Scan: Đang tải danh sách Google Drive...")
            response_files = drive_service.files().list(
                q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            drive_files = response_files.get('files', [])

            # 3. So Sánh (Phần "AI")
            print("Scan: Đang so sánh...")

            # Lấy tất cả File ID được dùng trong JSON
            json_file_ids = set()
            for key, data in github_data.items():
                if key == "updater": continue

                url_or_id = data.get("url")
                file_id = extract_gdrive_id_from_url(url_or_id) # Dùng helper

                if file_id:
                    json_file_ids.add(file_id)
                else:
                    errors_list.append(f"Option '{key}': URL không hợp lệ hoặc không phải Google Drive.")

            # Lấy tất cả File ID có trên Drive
            drive_file_map = {file['id']: file['name'] for file in drive_files}
            drive_file_ids = set(drive_file_map.keys())

            # 4. Tìm Lỗi (Có trong JSON, nhưng không có trên Drive)
            broken_ids = json_file_ids - drive_file_ids # Phép trừ tập hợp
            for broken_id in broken_ids:
                # Tìm xem item nào đang dùng ID bị hỏng này
                item_name = "[Không tìm thấy tên]"
                item_key = "[?]"
                for key, data in github_data.items():
                    if extract_gdrive_id_from_url(data.get("url")) == broken_id:
                        item_name = data.get("name", "[TÊN BỊ LỖI]")
                        item_key = key
                        break
                errors_list.append(f"Option '{item_name}' (ID: {item_key}): File ID '{broken_id}' KHÔNG TỒN TẠI trên Drive.")
            # --- HẾT SỬA ---

            # 5. Tìm Cảnh Báo (Có trên Drive, nhưng không dùng trong JSON)
            orphaned_ids = drive_file_ids - json_file_ids # Phép trừ tập hợp
            for orphaned_id in orphaned_ids:
                file_name = drive_file_map[orphaned_id]
                # Thêm dictionary thay vì string
                warnings_list.append({"name": file_name, "id": orphaned_id})

            print("Scan: Hoàn tất so sánh.")
            # Gửi báo cáo về cho queue
            progress_queue.put(("scan_report_ready", {"errors": errors_list, "warnings": warnings_list}))

        except Exception as e:
            print(f"Lỗi khi quét: {e}")
            progress_queue.put(("scan_failed", str(e)))

    def show_scan_report(errors, warnings):
        """Tạo cửa sổ Toplevel MỚI để hiển thị báo cáo TƯƠNG TÁC."""
        report_window = tk.Toplevel(root)
        report_window.title("Báo Cáo Quét Lỗi Đồng Bộ")
        center_window_on_screen(report_window, 700, 500)
        report_window.transient(root)
        report_window.grab_set()

        report_frame = ttk.Frame(report_window, padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True)

        report_text = tk.Text(report_frame, wrap="word", height=20, width=80, relief=tk.FLAT)
        report_scroll = ttk.Scrollbar(report_frame, orient="vertical", command=report_text.yview)
        report_text['yscrollcommand'] = report_scroll.set

        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- SỬA: Thêm các tag màu cho LINK ---
        report_text.tag_configure("header", font=("Segoe UI", 14, "bold"), spacing3=10)
        report_text.tag_configure("error", foreground="red", font=("Segoe UI", 10, "bold"))
        report_text.tag_configure("warning", foreground="#FFB000") # Màu vàng cam
        report_text.tag_configure("success", foreground="green")
        report_text.tag_configure("note", foreground=style.lookup("TLabel", "foreground"), lmargin1=10, lmargin2=10)

        # Tag cho link (màu xanh, gạch chân)
        report_text.tag_configure("quick_add_link", foreground="dodgerblue", underline=True, font=("Segoe UI", 9, "underline"))
        report_text.tag_configure("delete_link", foreground="#FF6347", underline=True, font=("Segoe UI", 9, "underline")) # Màu đỏ cà chua
        # --- HẾT SỬA ---

        # --- Chèn nội dung vào Text ---
        if not errors and not warnings:
            report_text.insert(tk.END, "QUÉT HOÀN TẤT\n", "header")
            report_text.insert(tk.END, "Chúc mừng! File JSON và Google Drive của bạn đã đồng bộ hoàn hảo.", "success")
        else:
            if errors:
                report_text.insert(tk.END, f"LỖI ({len(errors)}) - CẦN SỬA NGAY\n", "header")
                report_text.insert(tk.END, "(Các option này trong JSON đang trỏ đến file không tồn tại trên Drive)\n\n", "note")
                for i, err in enumerate(errors):
                    report_text.insert(tk.END, f" {i+1}. {err}\n", "error")
                report_text.insert(tk.END, "\n\n")

            if warnings:
                report_text.insert(tk.END, f"CẢNH BÁO ({len(warnings)}) - NÊN DỌN DẸP\n", "header")
                report_text.insert(tk.END, "(Các file này có trên Drive nhưng không được dùng. Bạn có thể xóa chúng, hoặc dùng 'Tạo Option Tải'.)\n\n", "note")

                # --- SỬA: Vòng lặp tạo link ---
                for i, warn_item in enumerate(warnings):
                    file_name = warn_item['name']
                    file_id = warn_item['id']

                    # 1. Chèn text cảnh báo
                    report_text.insert(tk.END, f" {i+1}. File: ", "warning")
                    report_text.insert(tk.END, f"{file_name}\n", "warning")

                    # 2. Tạo tag duy nhất cho mỗi link
                    qa_tag = f"qa_{file_id}" # Quick Add tag
                    del_tag = f"del_{file_id}" # Delete tag

                    # 3. Chèn các link
                    report_text.insert(tk.END, "      ") # Thụt lề
                    report_text.insert(tk.END, "[Tạo Option Tải]", ("quick_add_link", qa_tag))
                    report_text.insert(tk.END, "   ")
                    report_text.insert(tk.END, "[Xóa File này]", ("delete_link", del_tag))
                    report_text.insert(tk.END, "\n\n")

                    # 4. Gắn (Bind) sự kiện cho các tag duy nhất đó
                    # Dùng lambda để truyền đúng file_info (gồm name và id)
                    report_text.tag_bind(
                        qa_tag, 
                        "<Button-1>", 
                        lambda e, win=report_window, info=warn_item: handle_quick_add_click(win, info)
                    )
                    report_text.tag_bind(
                        del_tag, 
                        "<Button-1>", 
                        lambda e, win=report_window, info=warn_item: handle_delete_click(win, info)
                    )

                    # 5. Thêm hiệu ứng con trỏ chuột
                    report_text.tag_bind(qa_tag, "<Enter>", lambda e: report_text.config(cursor="hand2"))
                    report_text.tag_bind(qa_tag, "<Leave>", lambda e: report_text.config(cursor=""))
                    report_text.tag_bind(del_tag, "<Enter>", lambda e: report_text.config(cursor="hand2"))
                    report_text.tag_bind(del_tag, "<Leave>", lambda e: report_text.config(cursor=""))
                # --- HẾT SỬA ---

        report_text.config(state=tk.DISABLED) # Chỉ đọc


    # Frame trên cho các nút
    drive_button_frame = ttk.Frame(third_tab_frame)
    drive_button_frame.pack(fill=tk.X, pady=5)

    drive_auth_button = ttk.Button(drive_button_frame, text="Đăng nhập Google Drive", command=action_drive_login, style="Accent.TButton")
    drive_auth_button.pack(side=tk.LEFT, padx=5)

    upload_files_button = ttk.Button(drive_button_frame, text="📤", command=action_start_upload_all, style="Accent.TButton", state=tk.DISABLED)
    upload_files_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(upload_files_button, "Upload Tất Cả File")

    clear_upload_list_button = ttk.Button(drive_button_frame, text="🧹",  command=action_clear_upload_list, style="Danger.TButton")
    clear_upload_list_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(clear_upload_list_button, "Xóa Danh Sách Upload")

    drive_refresh_button = ttk.Button(drive_button_frame, text="🔄", command=action_refresh_drive_list)
    drive_refresh_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(drive_refresh_button, "Tải Danh Sách File (Làm mới)")

    scan_button = ttk.Button(drive_button_frame, text="🤖", command=action_start_scan)
    scan_button.pack(side=tk.LEFT, padx=5)
    CreateToolTip(scan_button, "Quét Lỗi Đồng Bộ")
    g_selected_drive_item_frame = None # Biến theo dõi item đang được chọn

    def on_drive_item_click(event, clicked_frame):
        """Xử lý khi click chuột trái vào một item trong lưới."""
        global g_selected_drive_item_frame

        # 1. Bỏ chọn item cũ (nếu có)
        if g_selected_drive_item_frame and g_selected_drive_item_frame != clicked_frame:
            try:
                # Trả về style mặc định 'Card.TFrame'
                g_selected_drive_item_frame.config(style="Card.TFrame")
            except Exception as e:
                print(f"Lỗi bỏ chọn item: {e}")

        # 2. Chọn item mới
        try:
            # Đặt style mới là "Accent.TFrame" (màu xanh accent)
            clicked_frame.config(style="Accent.TFrame") 
            g_selected_drive_item_frame = clicked_frame
        except Exception as e:
            print(f"Lỗi chọn item: {e}")
    # --- HẾT THÊM MỚI ---


    # ---HÀM TẠO NHANH OPTION ---
    def action_quick_add_option(file_name, file_id):
        """(ĐÃ VIẾT LẠI) Tự động tải config và thêm option mới với ID số."""
        global current_config_data, current_github_sha

        # --- TỰ ĐỘNG TẢI CONFIG NẾU CHƯA CÓ ---
        if current_github_sha is None:
            custom_showinfo("Thông báo", 
                                "Đây là lần 'Tạo Nhanh' đầu tiên.\n"
                                "Ứng dụng sẽ tự động tải config từ GitHub trước...")

            action_load_from_github_wrapper() 

            if current_github_sha is None:
                custom_showerror("Lỗi", "Tải config từ GitHub thất bại.\nKhông thể 'Tạo Nhanh'. Vui lòng thử lại.")
                return
        # --- HẾT TẢI TỰ ĐỘNG ---

        print(f"Thêm nhanh option cho: {file_name}")

        # 1. Tự động phát hiện loại file
        file_type = "zip" # Mặc định
        if file_name.lower().endswith(".rar"):
            file_type = "rar"
        elif file_name.lower().endswith(".exe"):
            file_type = "exe"

        # 2. Lấy tên file (bỏ đuôi) để dùng làm TÊN HIỂN THỊ
        base_name = os.path.splitext(file_name)[0]

        # 3. Tạo URL đầy đủ
        final_url = f"https://drive.google.com/uc?id={file_id}"

        # 4. KIỂM TRA TÊN BỊ TRÙNG
        existing_id = None
        for k, v in current_config_data.items():
            if v.get("name") == base_name:
                existing_id = k
                break

        target_key = None
        new_data = {
            "name": base_name, # <-- TÊN HIỂN THỊ
            "url": final_url, 
            "version": "CHƯA SET VERSION", # Placeholder
            "type": file_type,
            "password": None, 
            "delete_before_extract": [],
            "path_guide": None # Thêm key này (trống)
        }

        if existing_id:
            # --- CHẾ ĐỘ UPDATE ---
            if not custom_askyesno("Xác nhận Ghi đè", 
                f"Tên '{base_name}' đã tồn tại (ID: {existing_id}).\n"
                "Bạn có muốn ghi đè URL/Type (giữ Version cũ) không?"):
                return

            target_key = existing_id
            # Giữ lại các giá trị cũ
            old_data = current_config_data[target_key]
            new_data["version"] = old_data.get("version", "CHƯA SET VERSION")
            new_data["password"] = old_data.get("password")
            new_data["delete_before_extract"] = old_data.get("delete_before_extract", [])
            new_data["path_guide"] = old_data.get("path_guide")

            # Chỉ cập nhật
            current_config_data[target_key] = new_data

        else:
            # --- CHẾ ĐỘ THÊM MỚI ---
            # Tìm ID mới (số lớn nhất + 1)
            new_id = 0
            for key_str in current_config_data.keys():
                if key_str.isdigit():
                    new_id = max(new_id, int(key_str))

            target_key = str(new_id + 1) # Key mới
            current_config_data[target_key] = new_data

        # 6. Làm mới Treeview (Tab 2)
        try:
            populate_treeview()
            # Tự động chọn
            options_treeview.selection_set(target_key)
            options_treeview.focus(target_key)
        except Exception as e:
            print(f"Lỗi khi làm mới treeview (nền): {e}")

        # 7. Thông báo
        custom_showinfo("Đã Thêm Nhanh", 
            f"Đã thêm/cập nhật '{base_name}' (ID: {target_key}) vào config.\n\n"
            "VUI LÒNG:\n"
            "1. Chuyển qua Tab 2.\n"
            "2. (Đã tự động chọn)\n"
            "3. Nhập 'Version' và bấm 'Thêm / Cập nhật'.\n"
            "4. Bấm 'Lưu Config' để hoàn tất.")

    def handle_quick_add_click(report_window, file_info):
        """Đóng báo cáo và gọi hàm 'Tạo Nhanh Option'."""
        report_window.destroy() # Đóng cửa sổ báo cáo
        action_quick_add_option(file_info['name'], file_info['id'])

    def handle_delete_click(report_window, file_info):
        """Đóng báo cáo và gọi logic xóa (có xác nhận)."""
        report_window.destroy() # Đóng cửa sổ báo cáo

        # Chúng ta sao chép logic xác nhận an toàn (từ thread chính) ở đây
        message = f"Bạn có chắc chắn muốn XÓA VĨNH VIỄN file này\nkhỏi Google Drive không?\n\nFile: {file_info['name']}"

        if custom_askyesno("Xác nhận Xóa (Từ Trợ lý AI)", message):
            # Chỉ bắt đầu thread nếu người dùng bấm "Yes"
            threading.Thread(target=action_delete_drive_file_thread, 
                            args=(file_info['id'], file_info['name']), 
                            daemon=True).start()
        else:
            progress_queue.put(("drive_log", "Đã hủy thao tác xóa."))

    g_single_update_window = None # Biến global để theo dõi popup

    def open_single_file_updater_popup(file_info):
        """Mở popup chọn file để cập nhật (Dùng Nút bấm thay vì Kéo thả)."""
        global g_single_update_window, drive_service

        if g_single_update_window is not None:
            try: g_single_update_window.destroy()
            except: pass

        if not drive_service:
            custom_showerror("Lỗi", "Chưa đăng nhập Google Drive.")
            return

        target_name = file_info['name']
        target_ext = os.path.splitext(target_name)[1].lower() 

        # Tạo cửa sổ
        g_single_update_window = tk.Toplevel(root)
        g_single_update_window.title("Cập nhật File")
        center_window_on_screen(g_single_update_window, 400, 250) # Tăng chiều cao xíu
        g_single_update_window.transient(root)
        g_single_update_window.grab_set()

        main_frame = ttk.Frame(g_single_update_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Info
        ttk.Label(main_frame, text=f"Đang cập nhật file:\n{target_name}", justify=tk.CENTER).pack(pady=5)
        ttk.Label(main_frame, text=f"(Yêu cầu file đuôi: {target_ext})", style="secondary.TLabel").pack(pady=5)

        # --- HÀM XỬ LÝ KHI BẤM NÚT ---
        def on_browse_file():
            # Mở dialog chọn file đúng đuôi
            file_path = filedialog.askopenfilename(
                title=f"Chọn file {target_ext} thay thế",
                filetypes=[(f"{target_ext} file", f"*{target_ext}"), ("All files", "*.*")]
            )
            
            if file_path:
                # Kiểm tra đuôi lần nữa cho chắc
                local_ext = os.path.splitext(file_path)[1].lower()
                if local_ext != target_ext:
                    custom_showerror("Sai định dạng", 
                        f"File bạn chọn có đuôi {local_ext}.\nBắt buộc phải là {target_ext}.")
                    return

                # Nếu đúng, đóng popup và chạy thread upload luôn
                g_single_update_window.destroy()
                
                # Gọi thread upload (Hàm này bạn đã có sẵn trong code)
                threading.Thread(target=single_file_upload_thread, 
                                args=(file_path, file_info), 
                                daemon=True).start()

        # --- GIAO DIỆN NÚT BẤM ---
        select_frame = ttk.LabelFrame(main_frame, text="Chọn file mới từ máy")
        select_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Button(select_frame, text="📂 Chọn File...", command=on_browse_file, style="Accent.TButton").pack(fill=tk.X, padx=20, pady=20)

    def handle_single_file_drop(event, file_info, target_ext, drop_listbox, popup_window):
        """Xử lý khi file được thả vào popup cập nhật."""
        drop_listbox.delete(0, tk.END)

        raw_paths = root.tk.splitlist(event.data)
        if not raw_paths:
            drop_listbox.insert(tk.END, "Lỗi: Không thể đọc file.")
            return

        local_file_path = raw_paths[0]
        if not (os.path.exists(local_file_path) and os.path.isfile(local_file_path)):
            drop_listbox.insert(tk.END, "Lỗi: Đây không phải là file.")
            return

        # === BƯỚC VALIDATION (KIỂM TRA ĐỊNH DẠNG) ===
        dropped_ext = os.path.splitext(local_file_path)[1].lower()
        if dropped_ext != target_ext:
            drop_listbox.insert(tk.END, f"Lỗi: File phải có đuôi {target_ext}. (File bạn thả là {dropped_ext})")
            custom_showerror("Sai định dạng file",
                                f"Bạn đang cố cập nhật file '{file_info['name']}' (đuôi {target_ext}).\n\n"
                                f"File bạn vừa thả vào có đuôi {dropped_ext}.\n\n"
                                "Vui lòng thả file có cùng định dạng.",
                                parent=popup_window)
            return

        # === VALIDATION THÀNH CÔNG ===
        drop_listbox.insert(tk.END, f"Đang chuẩn bị upload: {os.path.basename(local_file_path)}")

        # Vô hiệu hóa popup
        popup_window.grab_release()
        popup_window.destroy()

        # Bắt đầu thread upload
        threading.Thread(target=single_file_upload_thread, 
                        args=(local_file_path, file_info), 
                        daemon=True).start()

    def single_file_upload_thread(local_path, file_info):
        """
        (SMOOTH & FAST) Upload tốc độ cao với thanh tiến trình cập nhật MƯỢT MÀ.
        """
        target_id = file_info['id']
        target_name = file_info['name']

        progress_queue.put(("drive_log", f"🚀 Upload '{target_name}' (Smooth Mode)..."))
        
        # --- HÀM CALLBACK ĐỂ CẬP NHẬT UI ---
        # Hàm này sẽ được gọi liên tục bên trong ProgressStream
        def update_progress_ui(current, total):
            percent = int((current / total) * 100)
            
            # Tính tốc độ (đơn giản hóa để UI mượt)
            # (Lưu ý: Tốc độ hiển thị ở đây là tốc độ ĐỌC Ổ CỨNG để đẩy lên RAM, 
            # nó tương đương tốc độ mạng nếu mạng nhanh, hoặc nhanh hơn nếu mạng chậm)
            
            progress_queue.put(("drive_upload_progress", {
                "percent": percent,
                "status_text": f"🚀 Đang tải lên: {percent}% ({format_bytes(current)} / {format_bytes(total)})",
                "speed_text": "Đang chạy...", # Có thể tính toán speed kỹ hơn nếu muốn
                "eta_text": ""
            }))

        stream = None
        try:
            global drive_service
            file_size = os.path.getsize(local_path)

            # --- CẤU HÌNH CHUNK LỚN (GIỮ NGUYÊN ĐỂ TỐI ƯU TỐC ĐỘ) ---
            # Dùng 256MB cho 8GB RAM
            chunk_size = 256 * 1024 * 1024 
            if file_size < chunk_size:
                chunk_size = file_size
            
            # Đảm bảo chia hết cho 256KB
            if chunk_size > 256 * 1024:
                chunk_size = int(chunk_size / (256 * 1024)) * (256 * 1024)

            # --- KÍCH HOẠT PROGRESS STREAM ---
            # Thay vì io.open thường, ta dùng class bọc của chúng ta.
            # Quan trọng: Không dùng buffering lớn ở đây, để hàm read() được gọi thường xuyên hơn -> UI mượt hơn.
            stream = ProgressStream(local_path, callback=update_progress_ui, mode='rb')

            media = MediaIoBaseUpload(
                stream,
                mimetype='application/octet-stream',
                chunksize=chunk_size,
                resumable=True
            )

            request = drive_service.files().update(
                fileId=target_id,
                media_body=media,
                fields='id'
            )

            # --- VÒNG LẶP UPLOAD ---
            response = None
            while response is None:
                # chunk_status sẽ là None cho đến khi hết 1 chunk lớn (256MB)
                # NHƯNG: ProgressStream vẫn đang âm thầm chạy và cập nhật UI ở nền
                chunk_status, response = request.next_chunk()
                
                # (Không cần cập nhật UI ở đây nữa vì ProgressStream đã làm rồi)

            if response:
                print(f"Upload xong ID: {target_id}")
                progress_queue.put(("drive_log", f"✅ Hoàn tất: '{target_name}'"))
                progress_queue.put(("refresh_drive_list", None))
                
                # Set 100% lần cuối cho chắc chắn
                progress_queue.put(("drive_upload_progress", {
                    "percent": 100, "status_text": "Hoàn tất!", "speed_text": "", "eta_text": ""
                }))

        except HttpError as error:
            print(f"Lỗi HttpError: {error}")
            progress_queue.put(("drive_log", f"❌ LỖI API: {error}"))
            progress_queue.put(("drive_upload_progress", {"status_text": "Lỗi Mạng!", "percent": 0}))
        except Exception as e:
            print(f"Lỗi Exception: {e}")
            progress_queue.put(("drive_log", f"❌ LỖI: {e}"))
            progress_queue.put(("drive_upload_progress", {"status_text": "Lỗi!", "percent": 0}))
        finally:
            if stream:
                stream.close()
            
            root.after(2000, lambda: progress_queue.put(("drive_upload_progress", {
                "percent": 0, "status_text": "Sẵn sàng.", "speed_text": "", "eta_text": ""
            })))

    # Frame cho ô kéo thả
    drop_target_frame = ttk.LabelFrame(third_tab_frame, text="File chờ upload", padding=(10, 10))
    drop_target_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    # --- THÊM NÚT NÀY VÀO ---
    btn_browse_tab3 = ttk.Button(drop_target_frame, text="📂 Chọn File từ máy tính...", command=action_browse_upload_files)
    btn_browse_tab3.pack(fill=tk.X, pady=(0, 5)) # Nằm trên listbox

    # --- LISTBOX (GIỮ NGUYÊN để hiển thị danh sách) ---
    drop_target_listbox = tk.Listbox(drop_target_frame, height=10, selectmode=tk.EXTENDED)
    drop_target_listbox.pack(fill=tk.BOTH, expand=True)

    # Đăng ký sự kiện kéo-thả
    drop_target_listbox.drop_target_register(DND_FILES)
    drop_target_listbox.dnd_bind('<<DropEnter>>', handle_drop_enter)
    drop_target_listbox.dnd_bind('<<DropLeave>>', handle_drop_leave)
    drop_target_listbox.dnd_bind('<<Drop>>', handle_drop)

    drive_storage_label.pack(fill=tk.X, pady=(10, 2), padx=(5,0))

    # --- THAY THẾ: Tạo giao diện lưới (grid) có thể cuộn ---
    drive_list_frame = ttk.LabelFrame(third_tab_frame, text="File hiện có trên Drive", padding=(5, 5))
    drive_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    # 1. Tạo Canvas và Scrollbar
    drive_canvas = tk.Canvas(drive_list_frame, borderwidth=0, highlightthickness=0)
    drive_scrollbar = ttk.Scrollbar(drive_list_frame, orient="vertical", command=drive_canvas.yview)
    drive_canvas.configure(yscrollcommand=drive_scrollbar.set)

    drive_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    drive_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 2. Tạo Frame nội dung BÊN TRONG Canvas
    # Frame này sẽ chứa các icon
    drive_icon_content_frame = ttk.Frame(drive_canvas, padding=(5, 5))

    # 3. Đặt Frame nội dung vào Canvas
    drive_canvas_window_id = drive_canvas.create_window((0, 0), window=drive_icon_content_frame, anchor="nw")

    # --- Các hàm helper cho việc cuộn (Tương tự Tab 1) ---
    def on_drive_content_frame_configure(event):
        """Cập nhật scroll region của canvas."""
        drive_canvas.configure(scrollregion=drive_canvas.bbox("all"))

    def on_drive_canvas_configure(event):
        """Đảm bảo frame nội dung luôn fill chiều rộng của canvas."""
        drive_canvas.itemconfig(drive_canvas_window_id, width=event.width - 4)

    # 4. Bind (gắn) các sự kiện cuộn
    drive_icon_content_frame.bind("<Configure>", on_drive_content_frame_configure)
    drive_canvas.bind("<Configure>", on_drive_canvas_configure)

    # Gắn sự kiện cuộn chuột cho tất cả
    drive_canvas.bind_all("<MouseWheel>", on_mouse_wheel) # Dùng on_mouse_wheel chung
    drive_canvas.bind_all("<Button-4>", on_mouse_wheel)
    drive_canvas.bind_all("<Button-5>", on_mouse_wheel)
    # --- HẾT THAY THẾ ---
    # --- HẾT THÊM MỚI ---
    # Frame cho log trạng thái
    upload_status_frame = ttk.LabelFrame(third_tab_frame, text="Trạng thái Upload", padding=(10, 10))
    upload_status_frame.pack(fill=tk.X, expand=False, pady=5)

    # --- THÊM MỚI: Thanh Progress Bar và Nhãn (Giống Tab 1) ---
    drive_upload_progressbar = ttk.Progressbar(upload_status_frame, orient="horizontal", length=100, mode="determinate")
    drive_upload_progressbar.pack(fill=tk.X, pady=(0, 5))

    drive_upload_labels_frame = ttk.Frame(upload_status_frame)
    drive_upload_labels_frame.pack(fill=tk.X)

    drive_upload_status_label = ttk.Label(drive_upload_labels_frame, text="Sẵn sàng upload...", anchor=tk.W, style="White.TLabel")
    drive_upload_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    drive_upload_eta_label = ttk.Label(drive_upload_labels_frame, text="", style="secondary.TLabel", anchor=tk.E, width=8)
    drive_upload_eta_label.pack(side=tk.RIGHT, padx=(10,0))

    drive_upload_speed_label = ttk.Label(drive_upload_labels_frame, text="", style="secondary.TLabel", anchor=tk.E, width=12)
    drive_upload_speed_label.pack(side=tk.RIGHT)
    # --- HẾT THÊM MỚI ---

    # Log listbox (nằm bên dưới)
    status_listbox_scrollbar = ttk.Scrollbar(upload_status_frame, orient="vertical")
    upload_status_listbox = tk.Listbox(upload_status_frame, height=8, yscrollcommand=status_listbox_scrollbar.set) # Giảm chiều cao
    status_listbox_scrollbar.config(command=upload_status_listbox.yview)

    status_listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(5,0))
    upload_status_listbox.pack(fill=tk.BOTH, expand=True, pady=(5,0))

    # --- HẾT CODE CHO TAB 3 ---
    # --- BẮT ĐẦU CODE CHO TAB 4 ("Credit") ---
    fourth_tab_frame = ttk.Frame(notebook, padding=(15, 15))
    notebook.add(fourth_tab_frame, text=" Cài Đặt & Credit ") # Đổi tên tab cho đúng ý nghĩa

    # --- 1. HEADER (Thông tin App) ---
    header_frame = ttk.Frame(fourth_tab_frame)
    header_frame.pack(fill=tk.X, pady=(0, 15))

    # Logo/Title bên trái, Info bên phải (hoặc căn giữa tùy ý, ở đây căn giữa cho đẹp)
    credit_title_label = ttk.Label(
        header_frame,
        text=f"WGZ Game Updater {CURRENT_VERSION}",
        font=("Segoe UI", 16, "bold"),
        anchor=tk.CENTER
    )
    credit_title_label.pack()

    credit_author_label = ttk.Label(
        header_frame,
        text="Dev: Mr-Mime (hoangdangnhatkha)",
        style="secondary.TLabel",
        anchor=tk.CENTER
    )
    credit_author_label.pack()
    settings_container = ttk.Frame(fourth_tab_frame)
    settings_container.pack(fill=tk.X, pady=5)
    settings_container.columnconfigure(0, weight=1)
    settings_container.columnconfigure(1, weight=1)
    setting_frame = ttk.LabelFrame(settings_container, text="⚙️ Chế Độ Hoạt Động", padding=10)
    setting_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    # Link GitHub
    def open_github(event):
        webbrowser.open_new_tab("https://github.com/hoangdangnhatkha/-WGZ-GameUpdater")

    credit_github_label = ttk.Label(
        header_frame,
        text="GitHub Repository",
        foreground="#4a90e2", cursor="hand2", font=("Segoe UI", 9, "underline"),
        anchor=tk.CENTER
    )
    credit_github_label.pack(pady=(2, 0))
    credit_github_label.bind("<Button-1>", open_github)
    credit_thanks_label = ttk.Label(
        header_frame, # Quan trọng: Pack vào header_frame
        text="Chỉ dành cho việc tải, upload và chia sẻ game của Discord WIBU's Gaming Zone",
        style="secondary.TLabel",
        font=("Segoe UI", 9, "italic"), # Chữ nghiêng cho đẹp
        anchor=tk.CENTER
    )
    credit_thanks_label.pack(pady=(5, 0))
    # --- THÊM MỚI: NÚT BẬT/TẮT BACKUP ---


    def action_clear_image_cache():
        """Xóa toàn bộ thư mục cache ảnh trên ổ cứng."""
        global g_cache_dir
        if not os.path.isdir(g_cache_dir):
            custom_showinfo("Hoàn tất", "Không tìm thấy thư mục cache ảnh (đã sạch).")
            return

        if custom_askyesno("Xác nhận Xóa Cache",
                            "Bạn có chắc chắn muốn xóa toàn bộ cache ảnh?\n"
                            "(Lần khởi động sau sẽ phải tải lại tất cả ảnh.)"):
            try:
                # Xóa toàn bộ thư mục và tạo lại
                shutil.rmtree(g_cache_dir)
                os.makedirs(g_cache_dir, exist_ok=True)
                
                # Xóa cache RAM
                root.cached_images.clear()
                
                custom_showinfo("Hoàn tất", "Đã xóa toàn bộ cache ảnh thành công.")
            except Exception as e:
                custom_showerror("Lỗi", f"Không thể xóa thư mục cache: {e}")

    # --- [TÍNH NĂNG] SỔ TAY GHI CHÚ (CLICK-THROUGH SWITCH) ---
    g_notes_window = None
    g_notes_is_ghost = False # Biến theo dõi trạng thái

    def set_window_click_through(hwnd, enable):
        """Hàm helper để bật/tắt chế độ xuyên thấu chuột."""
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enable:
                # Thêm cờ Transparent
                new_style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                print("Note: Chế độ Bóng ma (Click-Through) -> ON")
            else:
                # Gỡ bỏ cờ Transparent (giữ lại Layered để dùng Alpha)
                new_style = (style & ~WS_EX_TRANSPARENT) | WS_EX_LAYERED
                print("Note: Chế độ Chỉnh sửa -> ON")
                
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"Lỗi set style: {e}")

    def action_toggle_notes():
        """
        Quản lý Sổ tay:
        - Nếu chưa mở -> Mở lên (Chế độ sửa).
        - Nếu đang mở (Ghost) -> Chuyển về chế độ Sửa.
        - Nếu đang mở (Sửa) -> Đóng lại (Hoặc chuyển Ghost tùy ý).
        """
        global g_notes_window, g_notes_is_ghost

        # --- TRƯỜNG HỢP 1: ĐANG MỞ THÌ CHUYỂN CHẾ ĐỘ ---
        if g_notes_window is not None:
            if g_notes_is_ghost:
                # Đang là Ghost -> Chuyển thành Edit (Unlock)
                g_notes_is_ghost = False
                
                # Lấy HWND và tắt xuyên thấu
                g_notes_window.update_idletasks()
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(g_notes_window.winfo_id())
                if hwnd == 0: hwnd = g_notes_window.winfo_id()
                set_window_click_through(hwnd, False)
                
                # Thay đổi giao diện để báo hiệu
                g_notes_window.attributes('-alpha', 0.9) # Đậm hơn
                # Hiện lại thanh tiêu đề (nếu muốn logic phức tạp hơn, ở đây ta đổi màu viền)
                g_notes_window.config(bg="#4a90e2") # Viền xanh dương (Edit Mode)
                
                # Focus vào cửa sổ
                g_notes_window.lift()
                g_notes_window.focus_force()
            else:
                # Đang là Edit -> Đóng lại (Hoặc bạn có thể chọn ẩn đi)
                g_notes_window.destroy()
                g_notes_window = None
                g_notes_is_ghost = False
            return

        # --- TRƯỜNG HỢP 2: CHƯA MỞ -> TẠO MỚI ---
        try:
            g_notes_window = tk.Toplevel(root)
            g_notes_window.title("Notes")
            g_notes_window.geometry("350x250+50+150") 
            g_notes_window.overrideredirect(True)
            g_notes_window.attributes('-topmost', True)
            g_notes_window.attributes('-alpha', 0.9)
            g_notes_window.config(bg="#4a90e2") # Viền xanh (Edit Mode)

            # Padding frame (để tạo viền màu)
            padding_frame = tk.Frame(g_notes_window, bg="#4a90e2", padx=2, pady=2)
            padding_frame.pack(fill=tk.BOTH, expand=True)

            # Khung nội dung chính
            main_frame = ttk.Frame(padding_frame, style="Card.TFrame")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 1. THANH TIÊU ĐỀ
            title_bar = tk.Frame(main_frame, bg="#333", height=30)
            title_bar.pack(fill=tk.X)
            
            lbl_title = tk.Label(title_bar, text="📝 Đang Sửa (Kéo để di chuyển)", bg="#333", fg="white", cursor="fleur")
            lbl_title.pack(side=tk.LEFT, padx=5)

            # --- NÚT KHÓA (LOCK BUTTON) ---
            def lock_notes():
                global g_notes_is_ghost
                g_notes_is_ghost = True
                
                # 1. Đổi giao diện
                g_notes_window.attributes('-alpha', 0.4) # Mờ đi (Ghost)
                g_notes_window.config(bg="#333") # Mất viền xanh
                padding_frame.config(padx=0, pady=0) # Bỏ padding
                
                # 2. Kích hoạt Click-Through
                g_notes_window.update_idletasks()
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(g_notes_window.winfo_id())
                if hwnd == 0: hwnd = g_notes_window.winfo_id()
                set_window_click_through(hwnd, True)
                
                print("Đã khóa Note. Bấm nút trên App chính để Sửa lại.")

            btn_lock = tk.Label(title_bar, text=" 🔒 Xong ", bg="#28a745", fg="white", cursor="hand2", font=("Segoe UI", 9, "bold"))
            btn_lock.pack(side=tk.RIGHT, padx=2)
            btn_lock.bind("<Button-1>", lambda e: lock_notes())
            CreateToolTip(btn_lock, "Bấm vào đây để khóa Note và cho phép chuột bấm xuyên qua.\n(Để sửa lại: Bấm nút 'Sổ Tay Game' ở App chính)")

            # 2. VÙNG NỘI DUNG
            text_area = tk.Text(main_frame, bg="#222", fg="#00FF00", insertbackground="white", 
                                font=("Consolas", 10), bd=0, highlightthickness=0)
            text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text_area.images = [] 

            # --- Paste & Resize Logic (Giữ nguyên) ---
            def handle_paste(event):
                try:
                    img = ImageGrab.grabclipboard()
                    if isinstance(img, Image.Image):
                        orig_w, orig_h = img.size
                        target_w = int(orig_w * 0.7)
                        target_h = int(orig_h * 0.7)
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        
                        curr_w = g_notes_window.winfo_width()
                        curr_h = g_notes_window.winfo_height()
                        new_w = max(curr_w, target_w + 30)
                        new_h = max(curr_h, target_h + 60)
                        g_notes_window.geometry(f"{new_w}x{new_h}")
                        
                        tk_img = ImageTk.PhotoImage(img)
                        text_area.images.append(tk_img)
                        text_area.image_create(tk.INSERT, image=tk_img)
                        text_area.insert(tk.INSERT, "\n") 
                        return "break" 
                    return None
                except: pass

            text_area.bind("<Control-v>", handle_paste)
            text_area.insert("1.0", "Ctrl+V: Dán ảnh.\nBấm '🔒 Xong' để khóa & Click xuyên qua.\n")

            # --- Di chuyển cửa sổ ---
            def start_move(event):
                g_notes_window.x = event.x
                g_notes_window.y = event.y

            def do_move(event):
                deltax = event.x - g_notes_window.x
                deltay = event.y - g_notes_window.y
                x = g_notes_window.winfo_x() + deltax
                y = g_notes_window.winfo_y() + deltay
                g_notes_window.geometry(f"+{x}+{y}")

            lbl_title.bind("<ButtonPress-1>", start_move)
            lbl_title.bind("<B1-Motion>", do_move)
            title_bar.bind("<ButtonPress-1>", start_move)
            title_bar.bind("<B1-Motion>", do_move)

            # Resize Grip (Giữ nguyên)
            grip = tk.Label(main_frame, bg="#555", cursor="sizing")
            grip.place(relx=1.0, rely=1.0, x=0, y=0, anchor="se", width=15, height=15)
            def start_resize(event):
                g_notes_window.start_w = g_notes_window.winfo_width()
                g_notes_window.start_h = g_notes_window.winfo_height()
                g_notes_window.start_x = event.x_root
                g_notes_window.start_y = event.y_root
            def do_resize(event):
                delta_w = event.x_root - g_notes_window.start_x
                delta_h = event.y_root - g_notes_window.start_y
                new_w = max(g_notes_window.start_w + delta_w, 100)
                new_h = max(g_notes_window.start_h + delta_h, 100)
                g_notes_window.geometry(f"{new_w}x{new_h}")
            grip.bind("<ButtonPress-1>", start_resize)
            grip.bind("<B1-Motion>", do_resize)

        except Exception as e:
            print(f"Lỗi Notes: {e}")
            g_notes_window = None

    # --- [THÊM MỚI] TÍNH NĂNG TÂM ẢO (CROSSHAIR) ---
    g_crosshair_window = None 

    def action_toggle_crosshair():
        """
        Bật/Tắt tâm ngắm ảo.
        Sử dụng Windows API để cho phép click xuyên qua (Click-Through).
        """
        global g_crosshair_window
        
        # Import các hằng số Windows API
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020 # Cờ quan trọng nhất: Click xuyên qua
        except ImportError:
            custom_showerror("Lỗi", "Tính năng này yêu cầu thư viện ctypes (Windows).")
            return

        # Nếu đang bật -> Tắt đi
        if g_crosshair_window is not None:
            try:
                g_crosshair_window.destroy()
            except: pass
            g_crosshair_window = None
            print("Đã tắt Crosshair.")
            return

        # Nếu đang tắt -> Bật lên
        try:
            g_crosshair_window = tk.Toplevel(root)
            g_crosshair_window.title("Crosshair")
            
            # 1. Cấu hình hình học
            w, h = 30, 30
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            x = (screen_w // 2) - (w // 2)
            y = (screen_h // 2) - (h // 2)
            
            g_crosshair_window.geometry(f"{w}x{h}+{x}+{y}")
            g_crosshair_window.overrideredirect(True) 
            g_crosshair_window.attributes('-topmost', True) 
            
            # 2. Màu nền trong suốt
            bg_color = '#000001' 
            g_crosshair_window.config(bg=bg_color)
            try:
                g_crosshair_window.attributes('-transparentcolor', bg_color)
            except Exception: pass

            # 3. Vẽ Tâm
            canvas = tk.Canvas(g_crosshair_window, width=w, height=h, bg=bg_color, highlightthickness=0)
            canvas.pack()
            
            center = w // 2
            length = 8
            thickness = 2
            
            # Vẽ dấu cộng màu xanh lá (Lime)
            canvas.create_line(center - length, center, center + length + 1, center, fill="#00FF00", width=thickness)
            canvas.create_line(center, center - length, center, center + length + 1, fill="#00FF00", width=thickness)
            
            # --- [QUAN TRỌNG] KÍCH HOẠT CHẾ ĐỘ XUYÊN THẤU ---
            # Phải update idletasks để window có ID (HWND) trước khi gọi API
            g_crosshair_window.update_idletasks() 
            
            hwnd = ctypes.windll.user32.GetParent(g_crosshair_window.winfo_id())
            if hwnd == 0: # Fallback nếu không lấy được parent
                hwnd = g_crosshair_window.winfo_id()
                
            # Lấy style hiện tại
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # Thêm cờ Transparent (Xuyên thấu chuột) và Layered
            new_style = current_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
            
            # Áp dụng style mới
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
            print("Đã bật Crosshair (Click-Through Mode).")

        except Exception as e:
            print(f"Lỗi bật Crosshair: {e}")
            g_crosshair_window = None

    # --- THÊM MỚI: HÀM DỌN DẸP TEMP ---
    def action_clean_temp_files():
        """
        (PHIÊN BẢN MẠNH) Quét và xóa TOÀN BỘ file trong thư mục %TEMP% của Windows.
        Tự động bỏ qua các file đang được sử dụng (Locked files).
        """
        import shutil # Đảm bảo đã import thư viện này

        temp_dir = os.environ.get('TEMP')
        if not temp_dir or not os.path.isdir(temp_dir):
            custom_showerror("Lỗi", "Không thể tìm thấy thư mục Temp của Windows.")
            return

        # 1. Cảnh báo người dùng (Vì hành động này xóa rộng hơn)
        if not custom_askyesno("Xác nhận Dọn Sạch", 
                                f"Bạn sắp xóa TOÀN BỘ file rác trong thư mục Temp:\n{temp_dir}\n\n"
                                "Lưu ý:\n"
                                "• Hành động này sẽ giải phóng dung lượng ổ C.\n"
                                "• Các file đang được Windows/App khác sử dụng sẽ tự động được giữ lại.\n\n"
                                "Bạn có muốn tiếp tục không?"):
            return

        # 2. Bắt đầu dọn dẹp
        deleted_count = 0
        skipped_count = 0
        bytes_freed = 0
        
        print("--- Bắt đầu dọn dẹp toàn bộ Temp ---")
        
        try:
            # Lấy danh sách tất cả file/folder
            all_items = os.listdir(temp_dir)
            
            for item in all_items:
                item_path = os.path.join(temp_dir, item)
                
                try:
                    # Lấy kích thước trước khi xóa (để báo cáo)
                    current_size = 0
                    if os.path.isfile(item_path):
                        current_size = os.path.getsize(item_path)
                    
                    # XÓA FILE
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                        deleted_count += 1
                        bytes_freed += current_size
                        
                    # XÓA FOLDER (Dùng shutil.rmtree)
                    elif os.path.isdir(item_path):
                        # Tính sơ bộ size folder (nếu muốn chính xác phải duyệt đệ quy, nhưng sẽ chậm)
                        shutil.rmtree(item_path)
                        deleted_count += 1
                        
                except Exception:
                    # Nếu lỗi (PermissionDenied, FileInUse...) -> Bỏ qua
                    skipped_count += 1
                    
        except Exception as e:
            custom_showerror("Lỗi", f"Lỗi khi quét thư mục Temp: {e}")
            return

        # 3. Hiển thị kết quả
        msg = (f"Đã dọn dẹp xong!\n\n"
            f"✅ Đã xóa: {deleted_count} mục\n"
            f"🛡️ Đang sử dụng (Bỏ qua): {skipped_count} mục\n"
            f"💾 Dung lượng giải phóng: {format_bytes(bytes_freed)} (ước tính)")
            
        custom_showinfo("Dọn Dẹp Hoàn Tất", msg)

    # --- [TÍNH NĂNG MỚI] GEMINI AI PRO BROWSER ---
    def action_open_gemini_pro():
        """
        Khởi động Gemini bằng Subprocess gọi lại chính file EXE này với cờ riêng.
        Cách này ổn định nhất cho PyInstaller --onefile.
        """
        try:
            import subprocess
            
            # Lấy đường dẫn file chạy hiện tại (dù là .py hay .exe)
            current_executable = sys.executable
            
            # Nếu đang chạy code .py (Dev mode), sys.executable là python.exe
            # ta cần truyền thêm tên file script.
            cmd = [current_executable]
            if not getattr(sys, 'frozen', False):
                cmd.append(sys.argv[0]) # Thêm tên file .py
                
            # Thêm cờ hiệu lệnh
            cmd.append("--gemini")
            
            print(f"Đang khởi động Gemini subprocess: {cmd}")
            
            # Chạy tiến trình tách biệt hoàn toàn
            subprocess.Popen(
                cmd,
                creationflags=0x00000008, # DETACHED_PROCESS (Không dính dáng console cha)
                close_fds=True
            )
            
        except Exception as e:
            custom_showerror("Lỗi", f"Không thể mở Gemini: {e}")

    def on_secret_click(event):
        """Đếm số lần click vào label dung lượng."""
        global g_secret_click_count, drive_service

        

        g_secret_click_count += 1

        # Đặt lại bộ đếm sau 2 giây
        event.widget.after(2000, lambda: globals().update(g_secret_click_count=0))

        if g_secret_click_count == 3:
            if not drive_service:
                custom_showwarning("Chưa đăng nhập", "Bạn phải đăng nhập Google Drive trước.")
                return
            print("Đã kích hoạt tính năng bí mật!")
            g_secret_click_count = 0
            open_secret_uploader()

    def action_browse_secret_zip(): # Đổi tên hàm cho đúng nghĩa
        """Thay thế kéo thả cho Secret Uploader (Chế độ ZIP)."""
        file_path = filedialog.askopenfilename(
            title="Chọn file Update đã nén (.zip)",
            filetypes=[("Zip Files", "*.zip")]
        )
        
        if file_path:
            secret_drop_listbox.delete(0, tk.END)
            secret_drop_listbox.insert(tk.END, file_path)

    def open_secret_uploader():
        """Mở cửa sổ upload bí mật (Giao diện mới cho --onedir)."""
        global secret_drop_listbox, secret_zip_id_entry, secret_window

        secret_window = tk.Toplevel(root)
        secret_window.title("Secret Updater (Onedir Mode)")
        secret_window.after(10, lambda: apply_theme_to_titlebar(secret_window))
        center_window_on_screen(secret_window, 500, 300)
        secret_window.transient(root)
        secret_window.grab_set()

        main_frame = ttk.Frame(secret_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Khung kéo thả
        drop_frame = ttk.LabelFrame(main_frame, text="1. Kéo file Update (.zip) vào đây")
        drop_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Nút chọn file
        ttk.Button(drop_frame, text="📂 Chọn File .zip", command=action_browse_secret_zip).pack(fill=tk.X, padx=5, pady=5)
        
        secret_drop_listbox = tk.Listbox(drop_frame, height=3)
        secret_drop_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        secret_drop_listbox.drop_target_register(DND_FILES)
        secret_drop_listbox.dnd_bind('<<Drop>>', handle_secret_drop)

        # 2. Khung config (Chỉ cần 1 ID)
        config_frame = ttk.LabelFrame(main_frame, text="2. Cấu hình Link Drive")
        config_frame.pack(fill=tk.X, pady=5)

        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(row2, text="File ID bản Update (.zip):", width=22).pack(side=tk.LEFT)

        secret_zip_id_entry = ttk.Entry(row2)
        secret_zip_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Load ID cũ từ config (nếu có)
        secret_zip_id_entry.insert(0, local_config.get("secret_zip_id", ""))

        # 3. Nút bắt đầu
        start_button = ttk.Button(main_frame, text="🚀 Upload Ngay", 
                                command=start_secret_upload, style="Accent.TButton")
        start_button.pack(pady=10)

    def handle_secret_drop(event):
        """Xử lý khi kéo file vào cửa sổ bí mật (Chỉ nhận .zip)."""
        secret_drop_listbox.delete(0, tk.END) # Chỉ cho phép 1 file
        raw_paths = root.tk.splitlist(event.data)

        if raw_paths:
            file_path = raw_paths[0] # Lấy file đầu tiên
            if os.path.exists(file_path) and os.path.isfile(file_path) and file_path.lower().endswith(".zip"):
                secret_drop_listbox.insert(tk.END, file_path)
            else:
                secret_drop_listbox.insert(tk.END, "Lỗi: Chỉ chấp nhận file .zip")

    def start_secret_upload():
        """Bắt đầu luồng upload bí mật."""
        global scan_loading_window # Tái sử dụng cửa sổ loading

        try:
            file_path = secret_drop_listbox.get(0)
        except tk.TclError:
            custom_showerror("Lỗi", "Chưa kéo file .zip vào.", parent=secret_window)
            return

        zip_id = secret_zip_id_entry.get().strip()

        # --- Lưu ID vào config ---
        global local_config
        local_config["secret_zip_id"] = zip_id
        save_local_config(local_config)

        if not file_path or not zip_id:
            custom_showerror("Lỗi", "Thiếu file hoặc File ID.", parent=secret_window)
            return

        if not file_path.lower().endswith(".zip"):
            custom_showerror("Lỗi", "File phải là .zip.", parent=secret_window)
            return

        # Hiển thị cửa sổ "Đang tải"
        scan_loading_window = tk.Toplevel(root)
        scan_loading_window.title("Đang Upload...")
        center_window_on_screen(scan_loading_window, 350, 100)
        scan_loading_window.transient(secret_window)
        scan_loading_window.grab_set()

        global secret_loading_label
        secret_loading_label = ttk.Label(scan_loading_window, text="Đang chuẩn bị...")
        secret_loading_label.pack(expand=True, padx=20, pady=20)

        # Chạy thread mới (gọn nhẹ hơn)
        threading.Thread(target=secret_upload_thread, 
                        args=(file_path, zip_id), 
                        daemon=True).start()

    def secret_upload_thread(file_path, zip_id):
        """(Chạy ngầm) Chỉ upload file .zip lên Drive."""
        try:
            # 1. Update file ZIP lên Drive
            progress_queue.put(("secret_status", f"Đang upload: {os.path.basename(file_path)}..."))
            
            # Gọi hàm helper có sẵn (nó sẽ tự xử lý Update hoặc Create nếu ID 404)
            _secret_update_file(file_path, zip_id)

            progress_queue.put(("secret_done", "Upload thành công!"))

        except Exception as e:
            print(f"Lỗi trong secret_upload_thread: {e}")
            progress_queue.put(("secret_error", str(e)))

    def _secret_update_file(file_path, file_id):
        """Hàm helper (chạy ngầm) để upload (update) 1 file."""
        global drive_service
        try:
            print(f"Đang update File ID: {file_id} bằng file: {file_path}")
            # Dùng MediaFileUpload (không cần chunk)
            media_body = MediaFileUpload(file_path, resumable=False)

            # Gọi .update() để ghi đè file đã có
            drive_service.files().update(
                fileId=file_id,
                media_body=media_body
            ).execute()
            print(f"Update thành công File ID: {file_id}")

        except HttpError as error:
            # Nếu lỗi, thử tạo file mới (phòng trường hợp ID bị xóa)
            if error.resp.status == 404:
                print(f"Lỗi 404: File ID {file_id} không tồn tại. Đang thử tạo file mới...")
                file_metadata = {'name': os.path.basename(file_path), 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
                media_body = MediaFileUpload(file_path, resumable=False)
                new_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media_body,
                    fields='id'
                ).execute()
                print(f"TẠO FILE MỚI THAY THẾ. ID MỚI: {new_file.get('id')}")
                progress_queue.put(("secret_status", f"Cảnh báo: ID cũ {file_id} bị lỗi.\nĐã tạo file mới với ID: {new_file.get('id')}"))
            else:
                raise error # Ném lại lỗi nếu không phải 404
            
    drive_storage_label.bind("<Button-1>", on_secret_click)

    # Hàm on_backup_toggle (không đổi, chỉ copy vào đây)
    # Logic Toggle Backup
    def on_backup_toggle():
        global local_config
        is_enabled = g_backup_enabled.get()
        local_config["backup_enabled"] = is_enabled
        save_local_config(local_config)
        print(f"Backup: {is_enabled}")

    backup_checkbutton = ttk.Checkbutton(
        setting_frame,
        text="💾 Tự động sao lưu (Backup)",
        variable=g_backup_enabled,
        command=on_backup_toggle,
        style="Switch.TCheckbutton"
    )
    backup_checkbutton.pack(anchor=tk.W, pady=5)
    CreateToolTip(backup_checkbutton, "Sao lưu file cũ vào folder _BACKUPS trước khi cập nhật/cài đặt.")
    g_smart_mode_enabled = tk.BooleanVar(value=local_config.get("smart_mode_enabled", False))

    def on_smart_mode_toggle():
        global local_config
        is_enabled = g_smart_mode_enabled.get()
        local_config["smart_mode_enabled"] = is_enabled
        save_local_config(local_config)
        print(f"Smart Game Mode: {is_enabled}")

    smart_checkbutton = ttk.Checkbutton(
        setting_frame, 
        text="🚀 Smart Game Mode (Ưu tiên Game & Dọn RAM toàn hệ thống)",
        variable=g_smart_mode_enabled,
        command=on_smart_mode_toggle,
        style="Switch.TCheckbutton"
    )
    # pady=(0, 10) để tạo khoảng cách phía dưới tách biệt với các nút dọn dẹp
    smart_checkbutton.pack(anchor=tk.W, pady=5) 

    CreateToolTip(smart_checkbutton, "1. Dọn RAM cho TẤT CẢ ứng dụng đang chạy.\n"
                                    "2. Chạy Game với mức ưu tiên CPU CAO (High Priority).")

    g_auto_close = tk.BooleanVar(value=local_config.get("auto_close", False))

    def on_auto_close_toggle():
        global local_config
        local_config["auto_close"] = g_auto_close.get()
        save_local_config(local_config)
        print(f"Auto Close: {g_auto_close.get()}")

    # Tạo Checkbox
    auto_close_check = ttk.Checkbutton(
        setting_frame,
        text="👻 Tự động tắt App khi vào Game",
        variable=g_auto_close,
        command=on_auto_close_toggle,
        style="Switch.TCheckbutton"
    )
    auto_close_check.pack(anchor=tk.W, pady=5)
    CreateToolTip(auto_close_check, "Sau khi bấm 'Chạy Game', ứng dụng này sẽ tự tắt\nđể giải phóng hoàn toàn RAM cho game.")

    # --- [THÊM MỚI] NÚT GẠT HIỆU ỨNG VỤ NỔ ---
    g_chaos_effect_enabled = tk.BooleanVar(value=local_config.get("chaos_effect_enabled", False)) # Mặc định là Bật (True)

    def on_chaos_effect_toggle():
        global local_config
        local_config["chaos_effect_enabled"] = g_chaos_effect_enabled.get()
        save_local_config(local_config)
        print(f"Chaos Effect: {g_chaos_effect_enabled.get()}")

    chaos_checkbutton = ttk.Checkbutton(
        setting_frame,
        text="💥 Ảo Thuật của Uchiha Itachi ",
        variable=g_chaos_effect_enabled,
        command=on_chaos_effect_toggle,
        style="Switch.TCheckbutton"
    )
    chaos_checkbutton.pack(anchor=tk.W, pady=5)
    CreateToolTip(chaos_checkbutton, "Khi bấm 'Chạy Game', giao diện sẽ nổ tung bay tứ tán.\nTắt đi nếu bạn thích sự nghiêm túc.")

    g_auto_translator = tk.BooleanVar(value=local_config.get("auto_start_translator", False))

    def on_translator_toggle():
        global local_config
        is_enabled = g_auto_translator.get()
        
        # 1. Lưu vào config
        local_config["auto_start_translator"] = is_enabled
        save_local_config(local_config)
        
        # 2. Xử lý Bật/Tắt ngay lập tức
        if is_enabled:
            start_translator_service()
            print("Translator: ON")
        else:
            stop_translator_service()
            print("Translator: OFF")

    translator_check = ttk.Checkbutton(
        setting_frame,
        text="🔮 Bật/Tắt Chức Năng Dịch Game ENG-VN (HotKey: Alt + ~)",
        variable=g_auto_translator,
        command=on_translator_toggle,
        style="Switch.TCheckbutton"
    )
    translator_check.pack(anchor=tk.W, pady=5)
    CreateToolTip(translator_check, "Tự động bật công cụ dịch (Alt + ~) khi mở App.\nNếu tắt, công cụ sẽ đóng ngay lập tức.")
    # --- Cột Phải: Công Cụ & Bảo Trì ---
    tools_frame = ttk.LabelFrame(settings_container, text="🛠️ Công Cụ & Bảo Trì", padding=10)
    tools_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    # --- CẤU HÌNH LƯỚI ĐỂ CÁC NÚT BẰNG NHAU TUYỆT ĐỐI ---
    # uniform="btn_group": Ép buộc 2 cột này phải có cùng kích thước, bất kể nội dung text dài ngắn.
    tools_frame.columnconfigure(0, weight=1, uniform="btn_group")
    tools_frame.columnconfigure(1, weight=1, uniform="btn_group")
    # Cho phép giãn chiều cao nếu cần (tùy chọn)
    tools_frame.rowconfigure(0, weight=1)
    tools_frame.rowconfigure(1, weight=1)

    # Hàng 1 (Row 0)
    clean_temp_button = ttk.Button(tools_frame, text="Dọn %TEMP%", command=action_clean_temp_files)
    clean_temp_button.grid(row=0, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(clean_temp_button, "Xóa file .zip/.rar tạm tải về.")

    clear_img_cache_button = ttk.Button(tools_frame, text="Xóa Cache Ảnh", command=action_clear_image_cache)
    clear_img_cache_button.grid(row=0, column=1, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(clear_img_cache_button, "Tải lại ảnh bìa game nếu bị lỗi.")

    # Hàng 2 (Row 1)
    snapshot_btn = ttk.Button(tools_frame, text="📋 Kiểm Tra Cấu Hình", command=action_copy_system_info)
    snapshot_btn.grid(row=1, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(snapshot_btn, "Copy thông tin CPU/RAM/GPU để nhờ hỗ trợ.")

    global update_app_button
    update_app_button = ttk.Button(tools_frame, text="Kiểm tra Update App", command=action_manual_check_for_updates)
    update_app_button.grid(row=1, column=1, sticky="nsew", padx=2, pady=2, ipady=5)

    crosshair_btn = ttk.Button(tools_frame, text="🎯 Bật/Tắt Tâm Ảo", command=action_toggle_crosshair)
    crosshair_btn.grid(row=2, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(crosshair_btn, "Hiển thị tâm ngắm (Crosshair) màu xanh giữa màn hình.\nHỗ trợ bắn không cần ngắm (No-scope) trong game.")

    open_data_btn = ttk.Button(tools_frame, text="📂 Mở Data Folder", command=action_open_data_folder)
    open_data_btn.grid(row=2, column=1, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(open_data_btn, "Mở thư mục chứa settings.json và file log.")

    notes_btn = ttk.Button(tools_frame, text="📝 Note Dán Màn Hình", command=action_toggle_notes)
    notes_btn.grid(row=3, column=0, sticky="nsew", padx=2, pady=2, ipady=5)
    CreateToolTip(notes_btn, "Hiện tờ giấy ghi chú trong suốt trên màn hình game.\nDùng để ghi mật khẩu, nhiệm vụ...")


    # --- 3. PATH SETTINGS (Đường dẫn) ---
    path_settings_frame = ttk.LabelFrame(fourth_tab_frame, text="🔗 Liên Kết Launcher (Tự động tìm thấy)", padding=10)
    path_settings_frame.pack(fill=tk.X, pady=10)

    # Dùng Grid để căn thẳng hàng
    path_settings_frame.columnconfigure(1, weight=1)


    def action_save_path_settings():
        """Lấy đường dẫn từ Entry và lưu vào config."""
        global local_config
        
        try:
            # 1. Lấy giá trị từ các ô Entry
            # (Thêm kiểm tra 'in globals()' để tránh lỗi nếu UI chưa tạo)
            if 'g_steam_path_entry' in globals():
                steam_path = g_steam_path_entry.get()
                local_config["steam_path"] = steam_path
                print(f"Đã lưu Steam Path: {steam_path}")
                
            if 'g_riot_path_entry' in globals():
                riot_path = g_riot_path_entry.get()
                local_config["riot_path"] = riot_path
                print(f"Đã lưu Riot Path: {riot_path}")

            # 2. Lưu file settings.json
            save_local_config(local_config)
            
        except Exception as e:
            print(f"Lỗi khi lưu cài đặt đường dẫn: {e}")


    def action_launch_rustdesk():
        """
        Hiển thị hộp thoại tùy chỉnh (Custom Dialog) để chọn chế độ chạy RustDesk.
        Có áp dụng Theme cho Titlebar.
        """
        # 1. Tạo biến lưu kết quả
        selection_result = [None] 

        # 2. Tạo cửa sổ Dialog
        dialog = tk.Toplevel(root)
        dialog.title("Tùy chọn Hỗ trợ")
        
        # --- [MỚI] ÁP DỤNG THEME CHO TITLE BAR ---
        # Gọi hàm apply_theme_to_titlebar cho cửa sổ con này
        # Dùng .after(10) để đảm bảo cửa sổ đã khởi tạo xong trước khi tô màu
        dialog.after(10, lambda: apply_theme_to_titlebar(dialog))
        # -----------------------------------------
        
        # Kích thước và căn giữa
        dialog_width = 320
        dialog_height = 180
        center_window_on_screen(dialog, dialog_width, dialog_height)
        
        dialog.transient(root) 
        dialog.grab_set()      
        dialog.resizable(False, False)

        # Frame nội dung
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Tiêu đề
        lbl = ttk.Label(
            frame, 
            text="Bạn muốn khởi động RustDesk như thế nào?", 
            wraplength=280, 
            justify=tk.CENTER,
            font=("Segoe UI", 10)
        )
        lbl.pack(pady=(0, 15))

        # --- Hàm xử lý chọn ---
        def on_choose_discord():
            selection_result[0] = True
            dialog.destroy() 

        def on_choose_local():
            selection_result[0] = False
            dialog.destroy() 

        # --- Nút bấm ---
        btn_discord = ttk.Button(
            frame, 
            text="🚀 Gửi ID lên Discord (Nhờ Admin)", 
            command=on_choose_discord, 
            style="Accent.TButton"
        )
        btn_discord.pack(fill=tk.X, pady=5)

        btn_local = ttk.Button(
            frame, 
            text="📂 Chỉ mở RustDesk (Không gửi)", 
            command=on_choose_local
        )
        btn_local.pack(fill=tk.X, pady=5)

        # --- CHỜ NGƯỜI DÙNG CHỌN ---
        root.wait_window(dialog)

        # 3. Xử lý kết quả
        if selection_result[0] is None:
            return

        send_to_discord = selection_result[0]
        discord_name = "Ẩn danh"

        # 4. Nếu chọn Gửi Discord -> Mới hỏi tên
        if send_to_discord:
            import getpass
            pc_user = getpass.getuser()
            discord_name = custom_askstring(
                "Xác nhận danh tính", 
                "Nhập tên để còn biết ai chứ mày: ",
                initialvalue=pc_user,
                parent=root
            )
            if not discord_name: 
                return 

        # 5. Bắt đầu chạy Thread
        if 'g_anydesk_button' in globals():
            g_anydesk_button.config(state=tk.DISABLED, text="Đang mở RustDesk...")
        
        threading.Thread(target=launch_rustdesk_thread, args=(send_to_discord, discord_name), daemon=True).start()

    def apply_anydesk_connection_fix():
        """
        Sửa file config của AnyDesk để tắt 'Direct Connection' (Kết nối trực tiếp).
        Giúp sửa lỗi Connecting/Disconnected liên tục.
        """
        try:
            # AnyDesk lưu config ở %APPDATA%\AnyDesk\user.conf hoặc system.conf
            appdata = os.getenv('APPDATA')
            conf_dir = os.path.join(appdata, "AnyDesk")
            
            # Đảm bảo thư mục tồn tại
            if not os.path.exists(conf_dir):
                os.makedirs(conf_dir, exist_ok=True)
                
            # Chúng ta sẽ sửa file user.conf (file này ghi đè cài đặt hệ thống)
            conf_file = os.path.join(conf_dir, "user.conf")
            
            print(f"Đang cấu hình AnyDesk tại: {conf_file}")
            
            lines = []
            # 1. Đọc nội dung cũ nếu file tồn tại
            if os.path.exists(conf_file):
                try:
                    with open(conf_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"Lỗi đọc config cũ: {e}")

            # 2. Xóa dòng cấu hình cũ (nếu có) để tránh trùng lặp
            # Key cần tìm: ad.anynet.direct_connection
            new_lines = [line for line in lines if "ad.anynet.direct_connection" not in line]
            
            # 3. Thêm dòng cấu hình mới (0 = Disable, 1 = Enable)
            new_lines.append("ad.anynet.direct_connection=0\n")
            
            # 4. Ghi lại file
            with open(conf_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
                
            print("--> Đã tắt 'Direct Connection' trong config thành công.")
            return True

        except Exception as e:
            print(f"Lỗi khi sửa config AnyDesk: {e}")
            return False

    def launch_rustdesk_thread(send_to_discord, discord_name):
        """
        (RUSTDESK FULL: AUTO INSTALL + SERVICE FIX)
        1. Kiểm tra nếu chưa cài -> Tự động cài vào Program Files.
        2. Cài đặt và Bật Service để lấy ID/Pass ổn định.
        3. Dùng cơ chế 'Fire and Forget' để tránh treo App.
        """
        CREATE_NO_WINDOW = 0x08000000 
        rustdesk_id = None
        temp_password = "WGZSupport2025" 
        
        # Định nghĩa các đường dẫn
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        installed_dir = os.path.join(program_files, "RustDesk")
        installed_exe = os.path.join(installed_dir, "RustDesk.exe")
        
        # --- HÀM HELPER: CHẠY LỆNH AN TOÀN ---
        def run_command_safe(cmd_list, wait_time=5):
            """Chạy lệnh với timeout để tránh treo App."""
            try:
                print(f"Executing: {' '.join(cmd_list)}")
                process = subprocess.Popen(
                    cmd_list, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )
                try:
                    stdout, stderr = process.communicate(timeout=wait_time)
                    return True
                except subprocess.TimeoutExpired:
                    print(f"Lệnh tốn quá {wait_time}s (có thể đang chạy ngầm). Bỏ qua...")
                    return True 
            except Exception as e:
                print(f"Lỗi lệnh: {e}")
                return False
        # -------------------------------------

        try:
            # --- BƯỚC 1: TẮT RUSTDESK CŨ ---
            print("Đang đóng RustDesk cũ...")
            run_command_safe(["taskkill", "/F", "/IM", "RustDesk.exe"], wait_time=2)
            time.sleep(1)

            # --- BƯỚC 2: TÌM FILE GỐC (PORTABLE) ---
            portable_exe = resource_path("RustDesk.exe")
            if not os.path.exists(portable_exe):
                portable_exe = "RustDesk.exe" 
            
            if not os.path.exists(portable_exe) and not os.path.exists(installed_exe):
                progress_queue.put(("anydesk_error", "Không tìm thấy file RustDesk.exe gốc để cài đặt."))
                return

            # --- BƯỚC 3: KIỂM TRA & CÀI ĐẶT (NẾU CẦN) ---
            target_exe = portable_exe 

            if os.path.exists(installed_exe):
                print("Phát hiện RustDesk đã được cài đặt.")
                target_exe = installed_exe
            else:
                print("Chưa cài đặt. Đang kích hoạt bộ cài...")
                if os.path.exists(portable_exe):
                    # 1. Chạy lệnh cài đặt nhưng KHÔNG đợi (Popen không communicate ngay)
                    print(f"Executing Install: {portable_exe} --install --silent")
                    install_proc = run_command_safe([portable_exe, "--install", "--silent"], wait_time=0)
                    
                    # 2. Vòng lặp kiểm tra file (Polling) thay vì Wait
                    # Quét mỗi 1 giây, tối đa 20 giây. Hễ thấy file là dừng.
                    print("Đang đợi file xuất hiện trong Program Files...")
                    install_success = False
                    for i in range(60):
                        if os.path.exists(installed_exe):
                            print(f"--> File đã xuất hiện sau {i+1} giây!")
                            install_success = True
                            break
                        time.sleep(1)
                    
                    if install_success:
                        # Chờ thêm 2s để file được ghi hoàn tất
                        time.sleep(2)
                        target_exe = installed_exe
                        print("Cài đặt hoàn tất (Smart Check).")
                        
                        # (Tùy chọn) Kill tiến trình cài đặt nếu nó còn treo
                        try: install_proc.kill() 
                        except: pass
                    else:
                        print("Cài đặt quá lâu hoặc thất bại. Dùng bản Portable.")
                        target_exe = portable_exe

            # --- BƯỚC 4: XỬ LÝ SERVICE (TỐI ƯU HÓA) ---
            print(f"Đang cấu hình Service cho: {target_exe}")
            
            # 1. Kiểm tra xem Service đã tồn tại chưa (để tránh bị timeout 10s vô ích)
            service_exists = False
            try:
                # Lệnh "sc query RustDesk" trả về 0 nếu service tồn tại, 1060 nếu không có
                check_svc = subprocess.run(
                    ["sc", "query", "RustDesk"], 
                    capture_output=True, 
                    text=True, 
                    creationflags=CREATE_NO_WINDOW
                )
                if check_svc.returncode == 0:
                    service_exists = True
                    print("Service 'RustDesk' đã tồn tại. Bỏ qua bước cài đặt.")
            except: pass

            # 2. Chỉ cài đặt nếu chưa có
            if not service_exists:
                # Tăng timeout lên 15s cho chắc chắn
                run_command_safe([target_exe, "--install-service"], wait_time=15)
                time.sleep(1)

            # 3. Đảm bảo đường dẫn Service trỏ đúng vào file exe hiện tại (Quan trọng khi update)
            # Nếu file exe thay đổi vị trí, lệnh này sẽ cập nhật lại đường dẫn cho Service
            try:
                subprocess.run(
                    ["sc", "config", "RustDesk", f"binPath= \"{target_exe}\""],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW
                )
            except: pass

            # 4. Bật Service (Timeout 5s)
            # Dùng 'sc start' đôi khi nhanh hơn 'net start'
            run_command_safe(["sc", "start", "RustDesk"], wait_time=5)
            time.sleep(2)

            # --- BƯỚC 5: KHỞI ĐỘNG GIAO DIỆN ---
            print("Mở giao diện RustDesk...")
            subprocess.Popen([target_exe])

            # --- BƯỚC 6: CHỜ GUI VÀ LẤY ID ---
            print("⏳ Đang đợi cửa sổ App...")
            for i in range(20): 
                if gw.getWindowsWithTitle('RustDesk'):
                    break
                time.sleep(0.5)

            print("⏳ Đang lấy ID...")
            # Hàm lấy ID nội bộ
            def get_id_local():
                # Thử lệnh cmd trước
                try:
                    proc = subprocess.Popen([target_exe, "--get-id"], stdout=subprocess.PIPE, text=True, creationflags=CREATE_NO_WINDOW)
                    out, _ = proc.communicate(timeout=3)
                    val = out.strip().replace(" ", "")
                    if val.isdigit() and len(val) > 6: return val
                except: pass
                
                # Thử đọc file config
                paths = [
                    os.path.join(os.getenv('APPDATA'), 'RustDesk', 'config'),
                    os.path.join(os.getenv('LOCALAPPDATA'), 'RustDesk', 'config'),
                    os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), 'RustDesk', 'config') # Thêm ProgramData
                ]
                for d in paths:
                    for f in ['RustDesk.toml', 'RustDesk2.toml']:
                        full = os.path.join(d, f)
                        if os.path.exists(full):
                            try:
                                with open(full, 'r', encoding='utf-8') as file:
                                    match = re.search(r'id\s*=\s*[\'"]?(\d+)[\'"]?', file.read())
                                    if match: return match.group(1)
                            except: pass
                return None

            # Vòng lặp chờ ID
            for i in range(15):
                rustdesk_id = get_id_local()
                if rustdesk_id: break
                time.sleep(1)
                print(f"Đang chờ ID... {i}/15")

            # --- BƯỚC 7: XỬ LÝ KẾT QUẢ ---
            if rustdesk_id:
                print(f"✅ ID: {rustdesk_id}")
                
                # Đặt mật khẩu
                print("Đang đặt mật khẩu...")
                run_command_safe([target_exe, "--password", temp_password], wait_time=3)

                # Gửi thông báo
                install_status = "Installed & Service Running" if target_exe == installed_exe else "Portable Mode (Service Fix)"
                
                if send_to_discord and "YOUR_ID" not in DISCORD_WEBHOOK_URL:
                    try:
                        content_ping = ""
                        embed = {
                            "title": "🚀 Hỗ trợ RustDesk",
                            "color": 65280, 
                            "fields": [
                                { "name": "👤 User", "value": f"**{discord_name}**", "inline": True },
                                { "name": "🆔 ID", "value": f"```{rustdesk_id}```", "inline": True },
                                { "name": "🔑 Pass", "value": f"```{temp_password}```", "inline": True },
                                { "name": "💻 Status", "value": install_status, "inline": False }
                            ],
                            "footer": { "text": "WGZ Updater" }
                        }
                        requests.post(DISCORD_WEBHOOK_URL, json={
                            "content": content_ping, "username": "Bot RustDesk", "embeds": [embed]
                        }, timeout=5)
                        progress_queue.put(("anydesk_id_sent_to_discord", rustdesk_id))
                    except:
                        progress_queue.put(("anydesk_id_retrieved_locally", rustdesk_id))
                else:
                    progress_queue.put(("anydesk_id_retrieved_locally", rustdesk_id))
            else:
                progress_queue.put(("anydesk_error", "Không lấy được ID. Vui lòng kiểm tra lại RustDesk."))

        except Exception as e:
            print(f"Lỗi RustDesk: {e}")
            progress_queue.put(("anydesk_error", str(e)))
        
        finally:
            progress_queue.put(("anydesk_done", None))


    # --- THÊM MỚI: CÀI ĐẶT ĐƯỜNG DẪN STEAM ---
    ttk.Label(path_settings_frame, text="Steam Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
    global g_steam_path_entry
    g_steam_path_entry = ttk.Entry(path_settings_frame)
    g_steam_path_entry.grid(row=0, column=1, sticky="ew")
    g_steam_path_entry.bind("<FocusOut>", lambda e: action_save_path_settings())

    def browse_steam_exe():
        file_selected = filedialog.askopenfilename(title="Tìm steam.exe", filetypes=[("Executable", "steam.exe")])
        if file_selected:
            g_steam_path_entry.delete(0, tk.END)
            g_steam_path_entry.insert(0, file_selected)
            action_save_path_settings()

    ttk.Button(path_settings_frame, text="...", width=3, command=browse_steam_exe).grid(row=0, column=2, padx=(5, 0))

    # -- Riot --
    ttk.Label(path_settings_frame, text="Riot Client:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
    global g_riot_path_entry
    g_riot_path_entry = ttk.Entry(path_settings_frame)
    g_riot_path_entry.grid(row=1, column=1, sticky="ew", pady=(10, 0))
    g_riot_path_entry.bind("<FocusOut>", lambda e: action_save_path_settings())

    def browse_riot_exe():
        file_selected = filedialog.askopenfilename(title="Tìm RiotClientServices.exe", filetypes=[("Executable", "RiotClientServices.exe")])
        if file_selected:
            g_riot_path_entry.delete(0, tk.END)
            g_riot_path_entry.insert(0, file_selected)
            action_save_path_settings()

    ttk.Button(path_settings_frame, text="...", width=3, command=browse_riot_exe).grid(row=1, column=2, padx=(5, 0), pady=(10, 0))


    # --- 4. SUPPORT SECTION ---
    support_frame = ttk.LabelFrame(fourth_tab_frame, text="🆘 Hỗ Trợ Kỹ Thuật", padding=10)
    support_frame.pack(fill=tk.X, pady=(0, 10))

    support_layout = ttk.Frame(support_frame)
    support_layout.pack(fill=tk.X)

    ttk.Label(support_layout, text="Gặp lỗi khó? Yêu cầu hỗ trợ từ xa.", style="secondary.TLabel").pack(side=tk.LEFT)

    global g_anydesk_button
    g_anydesk_button = ttk.Button(
        support_layout,
        text="🚀 Hỗ Trợ Từ Xa", # <--- Đổi tên hiển thị
        command=action_launch_rustdesk,    # <--- Đổi hàm gọi
        style="Accent.TButton"
    )
    g_anydesk_button.pack(side=tk.RIGHT)
    CreateToolTip(g_anydesk_button, "Mở RustDesk để Admin điều khiển máy hỗ trợ sửa lỗi.")

    # --- CREDITS FOOTER ---
    footer_label = ttk.Label(fourth_tab_frame, text="WIBU's Gaming Zone © 2025", style="secondary.TLabel", font=("Segoe UI", 8))
    footer_label.pack(side=tk.BOTTOM, pady=5)
    # --- Hàm cho luồng tải config ban đầu ---

    

    def load_config_thread():
        """(ĐÃ SỬA) Tải cả config mod VÀ config theme."""
        global fallback_options

        # 1. Tải config Mod (như cũ)
        mod_config = load_config_from_github()
        if not mod_config:
            mod_config = fallback_options

        # 2. Tải config Theme (MỚI)
        theme_config = {}
        try:
            # (Chúng ta dùng lại link raw của file config, chỉ thay tên file)
            theme_url = "https://raw.githubusercontent.com/hoangdangnhatkha/-WGZ-GameUpdater/refs/heads/main/game_themes.json"
            cache_buster = f"?_={int(time.time())}"
            full_theme_url = theme_url + cache_buster

            print(f"Đang tải config theme: {full_theme_url}")
            response = requests.get(full_theme_url, timeout=10)
            response.raise_for_status()
            theme_config = response.json()
            print("Tải config theme thành công.")

        except Exception as e:
            print(f"Lỗi khi tải game_themes.json (sẽ dùng icon mặc định): {e}")
            theme_config = {} # Dùng dict rỗng nếu lỗi

        # 3. Gộp 2 kết quả và gửi về 1 message
        combined_data = {
            "mods": mod_config,
            "themes": theme_config
        }
        progress_queue.put(("config_loaded", combined_data))

    def preload_all_images_thread(themes, mods):
        """
        Tải trước ảnh Sidebar và Card Game để app mượt hơn.
        [CẬP NHẬT] Sử dụng get_thumbnail_from_theme để tránh Crash.
        """
        try:
            print("--- Bắt đầu Preload Ảnh (Background Thread) ---")

            # --- [MỚI] TẢI LOGO STEAM VÀ RIOT ---
            # Link ảnh online (Wikipedia/Wikimedia ổn định)
            steam_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png"
            riot_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/archive/c/cb/20230128010443%21Riot_Games_2022_wordmark.svg/120px-Riot_Games_2022_wordmark.svg.png"

            # 1. Tải icon Steam (Size nhỏ 64x64 cho Header Tab 2)
            root.steam_icon_small = load_image_from_url(steam_url, size=(89, 89))
            root.riot_icon_small = load_image_from_url(riot_url, size=(89, 89))
            root.steam_icon_tiny = load_image_from_url(steam_url, size=(32, 32))
            root.riot_icon_tiny = load_image_from_url(riot_url, size=(32, 32))
                        
            # 2. Preload ảnh cho Lưới Game (Từ danh sách Mods)
            if mods:
                # Gom nhóm mod theo game để không tải trùng
                unique_games = {}
                for mod_data in mods.values():
                    g_name = mod_data.get("game")
                    if g_name and g_name not in unique_games:
                        unique_games[g_name] = True
                        
                        # Ưu tiên lấy ảnh từ Theme nếu có
                        if themes and g_name in themes:
                            url = get_thumbnail_from_theme(themes[g_name])
                        else:
                            # Nếu không, lấy ảnh từ mod config (nếu có key 'image')
                            url = mod_data.get("image")
                        
                        if url:
                            # Tải size lớn cho Card (192x89)
                            load_image_from_url(url, size=(192, 89), only_cache=True)

            print("--- Preload Hoàn Tất! ---")
            
            # Gửi tín hiệu về Main Thread để vẽ lại giao diện (nếu cần)
            progress_queue.put(("all_images_preloaded", mods))

        except Exception as e:
            print(f"Lỗi trong Preload Thread: {e}")
            
    root.update_idletasks()


    status_label_splash.config(text="Đang tải thư viện: Google Drive & GitHub...")
    splash.update()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    status_label.configure(text="Đang tải config phiên bản...", style="White.TLabel")
    progress_bar.start(10)
    start_button.config(state=tk.DISABLED)
    browse_button.config(state=tk.DISABLED)
    root.after(100, process_queue)
    threading.Thread(target=load_config_thread, daemon=True).start()
    threading.Thread(target=auto_find_paths_thread, daemon=True).start()

    if local_config.get("auto_start_translator", False):
        print("Config bật: Tự động chạy Translator...")
        # Chạy trong thread để không làm chậm khởi động app chính
        threading.Thread(target=start_translator_service, daemon=True).start()
    # Hủy splash screen
    splash.destroy()
    sv_ttk.set_theme("dark")
    # Hiển thị cửa sổ chính
    root.deiconify()
    root.after(10, lambda: set_appwindow(root))
    # Đưa cửa sổ chính lên trên cùng
    root.after(10, lambda: apply_theme_to_titlebar(root))

    root.title("[WGZ] Game Updater")
    root.attributes('-topmost', 1) 
    root.focus_force()
    root.attributes('-topmost', 0)
    print("Đang kết nối Server Online...")
    # threading.Thread(target=start_socket_service, daemon=True).start()
    root.after(1000, lambda: show_new_feature_banner(
        root, 
        "✨ TÍNH NĂNG MỚI: DỊCH GAME", 
        "Dịch trực tiếp mọi nội dung trên màn hình (Skill, Item, Cốt truyện) từ tiếng Anh sang tiếng Việt \n\nHãy mở tính năng này ở Cài Đặt & Credit.\n\n👉 Sau khi mở dùng phím tắt: Alt + ~ ", 
    ))
    root.mainloop()