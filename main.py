import pygame
import sys
import json
import os
import time

# --- 設定常數 ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60
DATA_FILE = 'data.json'

# 顏色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 150, 0)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
LIGHT_GREY = (200, 200, 200)
DARK_GREY = (100, 100, 100)

FLOWER = (232, 101, 135)
FRUIT = (255, 180, 2)
TREE = (100, 175, 30)

# 植物種類定義
PLANT_TYPES = {
    1: "Leisure",  # 花
    2: "Work",  # 果樹
    3: "Commuting"  # 樹
}

PLANT_COLORS = {
    1: FLOWER,
    2: FRUIT,
    3: TREE
}

STAGE_DURATIONS = {
    1: 4,  # 模擬 Demo 用：極短時間 (實際應為 900)
    2: 6,  # 模擬 Demo 用：極短時間 (實際應為 1800)
    3: float('inf')
}
# 為了 Demo 效果，我把上面的時間改得很短。
# 如果你需要真實時間 15分鐘/30分鐘，請改回：
# STAGE_DURATIONS = { 1: 900, 2: 1800, 3: float('inf') }


PLOT_POSITIONS = [
    (355, 145), (480, 145), (605, 145),
    (355, 270), (480, 270), (605, 270),
    (355, 395), (480, 395), (605, 395)
]

# 植物選擇按鈕位置
BUTTON_RECTS = {
    1: pygame.Rect(855, 155, 80, 80),
    2: pygame.Rect(855, 240, 80, 80),
    3: pygame.Rect(855, 325, 80, 80)
}

# 開始/停止按鈕位置
START_BUTTON_RECT = pygame.Rect(425, 475, 100, 50)
home_button_rect = pygame.Rect(-6.5, 477, 320, 100)

# --- DEV 工具按鈕位置 ---
DEV_TOGGLE_RECT = pygame.Rect(100, 10, 50, 30)  # 左上角開關
DEV_MENU_BG_RECT = pygame.Rect(100, 45, 200, 100)  # 選單背景
DEV_RESET_RECT = pygame.Rect(110, 55, 180, 35)  # 重置按鈕
DEV_ADD_TIME_RECT = pygame.Rect(110, 100, 180, 35)  # 加時按鈕


# --- 資料處理函式 ---

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error decoding JSON. Creating new file.")
            return create_initial_data()
    else:
        return create_initial_data()


def create_initial_data():
    new_field = {
        "type": [0] * 9,
        "time": [0] * 9,
        "eventName": [""] * 9
    }
    return {
        "name": "UserName",
        "trees": [new_field]
    }


def save_data(data, filename=DATA_FILE):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_current_planting_index(data):
    """找到當前頁面中第一個空的種植位置 (type=0)。"""
    current_field = data['trees'][-1]
    try:
        return current_field['type'].index(0)  # 找到第一個 0 的索引
    except ValueError:
        # 如果找不到 0，表示當前頁面已滿
        return -1


def create_new_field(data):
    new_field = {
        "type": [0] * 9,
        "time": [0] * 9,
        "eventName": [""] * 9
    }
    data['trees'].append(new_field)
    save_data(data)  # 儲存新頁面


# --- 資源載入函式 ---

def load_image(filepath, size=None):
    try:
        image = pygame.image.load(filepath).convert_alpha()
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except pygame.error as e:
        print(f"Error loading image {filepath}: {e}")
        placeholder = pygame.Surface(size if size else (100, 100), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0, 128))
        return placeholder


def get_plant_sprite(plant_type, duration):
    """根據植物種類和持續時間回傳對應的圖片。"""
    if duration < STAGE_DURATIONS[1]:
        stage = 1
    elif duration < STAGE_DURATIONS[2]:
        stage = 2
    else:
        stage = 3

    filepath = f'./image/plant{plant_type}_{stage}.png'
    return load_image(filepath, (100, 100))


# --- Pygame 輔助函式 ---

def draw_text(surface, text, font, color, x, y, center=False, bg_color=None, padding=5):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()

    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)

    if bg_color is not None:
        bg_rect = text_rect.inflate(padding * 1.5, padding * 1.5)
        pygame.draw.rect(surface, bg_color, bg_rect)

    surface.blit(text_surface, text_rect)
    return text_rect


def format_time(total_seconds):
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# --- 文字輸入框 ---

class TextInputBox:
    def __init__(self, x, y, w, h, font, default_text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.color_inactive = LIGHT_GREY
        self.color_active = WHITE
        self.color = self.color_inactive
        self.text = default_text
        self.active = False
        self.text_surface = self.font.render(self.text, True, BLACK)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.text_surface = self.font.render(self.text, True, BLACK)
                self.rect.w = max(200, self.text_surface.get_width() + 10)
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, BLACK, self.rect, 2)


# --- 主遊戲類別 ---

class ThrivingLikeTrees:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Thriving like Trees")
        self.clock = pygame.time.Clock()

        font_path = "C:/Windows/Fonts/msyh.ttc"
        if not os.path.exists(font_path):
            font_path = pygame.font.get_default_font()

        self.font_small = pygame.font.Font(font_path, 12)
        self.font_smallMedium = pygame.font.Font(font_path, 16)
        self.font_medium = pygame.font.Font(font_path, 24)
        self.font_large = pygame.font.Font(font_path, 36)

        # 載入資源
        self.background_img = load_image('./image/background.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.home_img = load_image('./image/Home.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.start_button_img = load_image('./image/start_button.png', (100, 50))
        self.home_button_img = load_image('./image/home_button.png', (100, 50))
        self.stop_button_img = load_image('./image/stop_button.png', (100, 50))
        self.plant_select_imgs = {
            1: load_image('./image/flower_icon.png', (80, 80)),
            2: load_image('./image/orange_icon.png', (80, 80)),
            3: load_image('./image/tree_icon.png', (80, 80)),
        }

        self.state = 'HOME'
        self.data = load_data()
        self.current_field_index = len(self.data['trees']) - 1

        self.is_timing = False
        self.start_time = 0
        self.current_duration = 0

        self.selected_plant_type = 0
        self.planting_index = -1

        self.warning_text = ""
        self.warning_time = 0

        self.input_box = TextInputBox(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 40, self.font_medium)

        self.prev_page_rect = pygame.Rect(200, SCREEN_HEIGHT // 2, 50, 50)
        self.next_page_rect = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT // 2, 50, 50)
        self.home_button_rect = pygame.Rect(0, 480, 320, 100)
        self.enter_game_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 100, 100, 50)

        # --- DEV MENU 狀態 ---
        self.show_dev_menu = False

    def show_warning(self, text, duration=2):
        self.warning_text = text
        self.warning_time = time.time() + duration

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.is_timing:
                    self.current_duration = int(time.time() - self.start_time)
                    self.stop_timer(event_name="Event")
                save_data(self.data)
                pygame.quit()
                sys.exit()

            if self.state == 'HOME':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if self.enter_game_button_rect.collidepoint(mouse_pos):
                        self.state = 'GARDEN_VIEW'
                        self.current_field_index = len(self.data['trees']) - 1

            elif self.state == 'GARDEN_VIEW':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # --- DEV MENU 邏輯 ---
                    # 1. 切換選單開關
                    if DEV_TOGGLE_RECT.collidepoint(mouse_pos):
                        self.show_dev_menu = not self.show_dev_menu
                        return  # 點擊選單按鈕後不處理其他點擊

                    # 2. 如果選單開啟，處理選單按鈕
                    if self.show_dev_menu:
                        # 功能 A: 備份並重置
                        if DEV_RESET_RECT.collidepoint(mouse_pos):
                            self.backup_and_reset_data()
                            self.show_dev_menu = False  # 關閉選單
                            self.show_warning("Data Reset & Backed up!", 3)
                            return

                        # 功能 B: 增加 15 分鐘
                        if DEV_ADD_TIME_RECT.collidepoint(mouse_pos):
                            if self.is_timing:
                                # 透過將「開始時間」往前推 900 秒，等於「經過時間」增加了 900 秒
                                self.start_time -= 900
                                self.update()  # 立即更新一次時間
                                print("DEV: Added 15 mins")
                            else:
                                self.show_warning("Start timer first!", 1)
                            return

                    # --- 正常遊戲邏輯 ---

                    # 主頁按鈕
                    if self.home_button_rect.collidepoint(mouse_pos):
                        if self.is_timing:
                            self.current_duration = int(time.time() - self.start_time)
                            self.stop_timer(event_name="未命名活動")
                        self.state = 'HOME'
                        self.selected_plant_type = 0

                    # 選擇植物
                    for plant_type, rect in BUTTON_RECTS.items():
                        if rect.collidepoint(mouse_pos):
                            self.selected_plant_type = plant_type
                            break

                    # 開始/停止按鈕
                    if START_BUTTON_RECT.collidepoint(mouse_pos):
                        if not self.is_timing:
                            if self.selected_plant_type != 0:
                                # --- 修改點 1: 自動跳轉到最新頁面 ---
                                latest_page_idx = len(self.data['trees']) - 1
                                if self.current_field_index != latest_page_idx:
                                    print(f"Auto-jumping to latest field: {latest_page_idx}")
                                    self.current_field_index = latest_page_idx
                                # ----------------------------------
                                self.start_timer()
                            else:
                                self.show_warning("Choose plant type before start planting.", duration=2)
                        else:
                            self.is_timing = False
                            self.current_duration = int(time.time() - self.start_time)
                            self.state = 'INPUT_NAME'
                            self.input_box.text = ''
                            self.input_box.active = True

                    # 頁面切換
                    if self.prev_page_rect.collidepoint(mouse_pos) and self.current_field_index > 0:
                        self.current_field_index -= 1
                    if self.next_page_rect.collidepoint(mouse_pos) and self.current_field_index < len(
                            self.data['trees']) - 1:
                        self.current_field_index += 1

            elif self.state == 'INPUT_NAME':
                event_name = self.input_box.handle_event(event)
                if event_name is not None:
                    self.stop_timer(event_name)
                    self.state = 'GARDEN_VIEW'

    def backup_and_reset_data(self):
        """備份當前資料並重置"""
        # 1. 產生備份檔名 (data_20231027_103001.json)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"data_{timestamp}.json"

        # 2. 儲存備份
        save_data(self.data, backup_filename)
        print(f"Backup saved to {backup_filename}")

        # 3. 重置數據
        self.data = create_initial_data()
        save_data(self.data)  # 覆寫原本的 data.json

        # 4. 重置遊戲狀態
        self.current_field_index = 0
        self.is_timing = False
        self.current_duration = 0
        self.selected_plant_type = 0
        self.planting_index = -1
        print("Data reset to initial state.")

    def start_timer(self):
        self.planting_index = get_current_planting_index(self.data)
        if self.planting_index == -1:
            create_new_field(self.data)
            self.current_field_index = len(self.data['trees']) - 1
            self.planting_index = 0

        self.is_timing = True
        self.start_time = time.time()
        print(f"Timer started. Index: {self.planting_index}")

    def stop_timer(self, event_name):
        current_field = self.data['trees'][-1]
        if self.selected_plant_type != 0 and self.planting_index != -1:
            if current_field['type'][self.planting_index] == 0:
                current_field['type'][self.planting_index] = self.selected_plant_type
                current_field['time'][self.planting_index] = self.current_duration
                current_field['eventName'][self.planting_index] = event_name
                save_data(self.data)
                print(f"Saved: {event_name}, Time: {self.current_duration}")
            else:
                print("Error: Plot not empty.")
        else:
            print("Error: No plant/index selected.")

        self.current_duration = 0
        self.selected_plant_type = 0
        self.planting_index = -1

    def update(self):
        if self.is_timing:
            self.current_duration = int(time.time() - self.start_time)

    def draw(self):
        if self.state == 'HOME':
            self.draw_home()
        elif self.state == 'GARDEN_VIEW':
            self.draw_garden()
            # 繪製開發者選單 (最上層)
            if self.show_dev_menu:
                self.draw_dev_menu()
            else:
                # 只畫一個小按鈕
                pygame.draw.rect(self.screen, DARK_GREY, DEV_TOGGLE_RECT)
                draw_text(self.screen, "DEV", self.font_small, WHITE, DEV_TOGGLE_RECT.centerx, DEV_TOGGLE_RECT.centery,
                          center=True)

        elif self.state == 'INPUT_NAME':
            self.draw_garden()
            self.draw_input_name()

        pygame.display.flip()

    def draw_dev_menu(self):
        """繪製開發者選單"""
        # 背景
        pygame.draw.rect(self.screen, DARK_GREY, DEV_MENU_BG_RECT)
        pygame.draw.rect(self.screen, WHITE, DEV_MENU_BG_RECT, 2)  # 邊框

        # Toggle 按鈕 (保持顯示以便關閉)
        pygame.draw.rect(self.screen, RED, DEV_TOGGLE_RECT)
        draw_text(self.screen, "X", self.font_small, WHITE, DEV_TOGGLE_RECT.centerx, DEV_TOGGLE_RECT.centery,
                  center=True)

        # Reset 按鈕
        pygame.draw.rect(self.screen, BLUE, DEV_RESET_RECT)
        draw_text(self.screen, "Backup & Reset", self.font_smallMedium, WHITE, DEV_RESET_RECT.centerx,
                  DEV_RESET_RECT.centery, center=True)

        # Add Time 按鈕
        color = GREEN if self.is_timing else LIGHT_GREY  # 只有計時中才亮起
        pygame.draw.rect(self.screen, color, DEV_ADD_TIME_RECT)
        draw_text(self.screen, "+15 Mins (Grow)", self.font_smallMedium, WHITE, DEV_ADD_TIME_RECT.centerx,
                  DEV_ADD_TIME_RECT.centery, center=True)

    def draw_home(self):
        self.screen.blit(self.home_img, (0, 0))
        self.screen.blit(self.start_button_img, self.enter_game_button_rect)

    def draw_garden(self):
        self.screen.blit(self.background_img, (0, 0))
        current_field = self.data['trees'][self.current_field_index]
        is_active_session = self.is_timing or (self.state == 'INPUT_NAME')

        for i in range(9):
            x, y = PLOT_POSITIONS[i]
            plant_type = current_field['type'][i]
            plant_time = current_field['time'][i]
            event_name = current_field['eventName'][i]
            duration_to_display = plant_time
            is_growing_now = False

            if is_active_session and self.planting_index == i and self.current_field_index == len(
                    self.data['trees']) - 1:
                duration_to_display = self.current_duration
                plant_type = self.selected_plant_type
                is_growing_now = True

            if plant_type != 0:
                plant_sprite = get_plant_sprite(plant_type, duration_to_display)
                rect = plant_sprite.get_rect(center=(x, y))
                self.screen.blit(plant_sprite, rect)

                label_text_1 = ""
                label_text_2 = ""
                if is_growing_now:
                    label_text_1 = f"{PLANT_TYPES.get(plant_type, 'N/A')}: {format_time(duration_to_display)}"
                    label_text_2 = "(GROWING...)" if self.is_timing else "(PAUSED)"
                else:
                    label_text_1 = f"{PLANT_TYPES.get(plant_type, 'N/A')}: {event_name}"
                    label_text_2 = f"{format_time(duration_to_display)}"

                draw_text(self.screen, label_text_1, self.font_smallMedium, BLACK, x + (i % 3 - 1) * 30, y - 80,
                          center=True, bg_color=PLANT_COLORS.get(plant_type))
                draw_text(self.screen, label_text_2, self.font_small, BLACK, x + (i % 3 - 1) * 30, y - 60, center=True,
                          bg_color=PLANT_COLORS.get(plant_type))

        for plant_type, rect in BUTTON_RECTS.items():
            pygame.draw.circle(self.screen, (255, 247, 214), (rect.x + rect.width / 2, rect.y + rect.width / 2), 40)
            icon_rect = self.plant_select_imgs[plant_type].get_rect(center=rect.center)
            self.screen.blit(self.plant_select_imgs[plant_type], icon_rect)
            if self.selected_plant_type == plant_type:
                pygame.draw.rect(self.screen, GREEN, rect, 3)

        timer_text = format_time(self.current_duration) if is_active_session else "00:00:00"
        draw_text(self.screen, timer_text, self.font_large, BLACK, 800, 40, center=True, bg_color=LIGHT_GREY)

        if is_active_session:
            button_img = self.stop_button_img
        else:
            button_img = self.start_button_img

        self.screen.blit(button_img, START_BUTTON_RECT)

        draw_text(self.screen, "<", self.font_large, BLACK, self.prev_page_rect.centerx, self.prev_page_rect.centery,
                  center=True, bg_color=LIGHT_GREY)
        draw_text(self.screen, ">", self.font_large, BLACK, self.next_page_rect.centerx, self.next_page_rect.centery,
                  center=True, bg_color=LIGHT_GREY)
        page_info = f"Garden {self.current_field_index + 1}/{len(self.data['trees'])}"
        draw_text(self.screen, page_info, self.font_medium, (255, 100, 100), SCREEN_WIDTH // 2, 25, center=True, bg_color=(255, 255, 200))

        self.screen.blit(self.home_button_img, home_button_rect)

        if self.warning_text and time.time() < self.warning_time:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            self.screen.blit(s, (0, 0))
            draw_text(self.screen, self.warning_text, self.font_large, (255, 100, 100),
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True, bg_color=(255, 255, 200))

    def draw_input_name(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))
        draw_text(self.screen, "Input Activity Name:", self.font_large, WHITE, SCREEN_WIDTH // 2,
                  SCREEN_HEIGHT // 2 - 50, center=True)
        self.input_box.draw(self.screen)
        draw_text(self.screen, "(Press Enter to Save)", self.font_small, WHITE, SCREEN_WIDTH // 2,
                  SCREEN_HEIGHT // 2 + 60, center=True)

    def run(self):
        running = True
        while running:
            self.handle_input()
            if self.state == 'GARDEN_VIEW':
                self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == '__main__':
    if not os.path.exists('image'):
        os.makedirs('image')
    if not os.path.exists(DATA_FILE):
        save_data(create_initial_data())
    game = ThrivingLikeTrees()
    game.run()