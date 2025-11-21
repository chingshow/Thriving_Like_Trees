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
LIGHT_GREY = (200, 200, 200)

FLOWER = (232, 101, 135)
FRUIT = (255, 180, 2)
TREE = (100, 175, 30)


# 植物種類定義 (與您的數據結構一致)
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
    1: 4,  # 900 秒 (0-15 分鐘)
    2: 6,  # 1800 秒 (15-30 分鐘)
    3: float('inf')  # >30 分鐘
}

PLOT_POSITIONS = [
    (355, 145), (480, 145), (605, 145),
    (355, 270), (480, 270), (605, 270),
    (355, 395), (480, 395), (605, 395)
]

# 植物選擇按鈕位置 (根據圖片右側的三個按鈕)
BUTTON_RECTS = {
    1: pygame.Rect(855, 155, 80, 80),  # 花 (Leisure)
    2: pygame.Rect(855, 240, 80, 80),  # 果樹 (Work)
    3: pygame.Rect(855, 325, 80, 80)  # 樹 (Commuting)
}

# 開始/停止按鈕位置 (圖片底部的紅色按鈕)
START_BUTTON_RECT = pygame.Rect(425, 475, 100, 50)

home_button_rect = pygame.Rect(-6.5, 477, 320, 100)


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


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
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
        image = pygame.image.load(filepath).convert_alpha()  # 使用 convert_alpha 支援透明度
        if size:
            image = pygame.transform.scale(image, size)
        return image
    except pygame.error as e:
        print(f"Error loading image {filepath}: {e}")
        # 如果圖片遺失，回傳一個紅色方塊作為佔位符
        placeholder = pygame.Surface(size if size else (100, 100), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0, 128))
        return placeholder


def get_plant_sprite(plant_type, duration):
    """根據植物種類和持續時間回傳對應的圖片。"""
    # 判斷成長階段
    if duration < STAGE_DURATIONS[1]:
        stage = 1  # 0-15 分鐘: Stage 1: Seeding
    elif duration < STAGE_DURATIONS[2]:
        stage = 2  # 15-30 分鐘: Stage 2: Growing
    else:
        stage = 3  # >30 分鐘: Stage 3: Fully grown

    # 構造檔案路徑: ./image/plant{type}_{stage}.png
    filepath = f'./image/plant{plant_type}_{stage}.png'
    # 這裡假設所有植物圖片大小一致，例如 100x100
    return load_image(filepath, (100, 100))


# --- Pygame 輔助函式 ---

def draw_text(surface, text, font, color, x, y, center=False, bg_color=None, padding=5):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()

    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)

    # 如果有背景顏色，先繪製背景矩形
    if bg_color is not None:
        bg_rect = text_rect.inflate(padding * 1.5, padding * 1.5)
        pygame.draw.rect(surface, bg_color, bg_rect)

    # 繪製文字
    surface.blit(text_surface, text_rect)
    return text_rect


def format_time(total_seconds):
    """將秒數轉換成 HH:MM:SS 格式。"""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# --- 文字輸入框 (用於輸入 eventName) ---

class TextInputBox:
    """一個簡單的 Pygame 文字輸入框。"""

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
            # 如果點擊輸入框
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    # 按 Enter 結束輸入
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # 重新渲染文字
                self.text_surface = self.font.render(self.text, True, BLACK)
                # 調整輸入框寬度
                self.rect.w = max(200, self.text_surface.get_width() + 10)
        return None

    def draw(self, screen):
        # 繪製輸入框和文字
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, BLACK, self.rect, 2)  # 邊框


# --- 主遊戲類別 ---

class ThrivingLikeTrees:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Thriving like Trees")
        self.clock = pygame.time.Clock()

        # 嘗試尋找系統中文字體，避免中文顯示亂碼
        font_path = "C:/Windows/Fonts/msyh.ttc"  # 微軟雅黑
        if not os.path.exists(font_path):
            font_path = pygame.font.get_default_font()  # fallback

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
        # 載入植物選擇按鈕圖 (這裡只是佔位，您需要替換成實際圖片)
        self.plant_select_imgs = {
            1: load_image('./image/flower_icon.png', (80, 80)),
            2: load_image('./image/orange_icon.png', (80, 80)),
            3: load_image('./image/tree_icon.png', (80, 80)),
        }

        # 遊戲狀態: 'HOME', 'GARDEN_VIEW', 'INPUT_NAME'
        self.state = 'HOME'

        # 資料
        self.data = load_data()
        self.current_field_index = len(self.data['trees']) - 1  # 當前顯示的田地索引

        # 計時器變數
        self.is_timing = False
        self.start_time = 0
        self.current_duration = 0

        # 種植變數
        self.selected_plant_type = 0  # 1: 花, 2: 果樹, 3: 樹
        self.planting_index = -1  # 當前種植的位置索引

        # 提示文字
        self.warning_text = ""
        self.warning_time = 0

        # 文字輸入框
        self.input_box = TextInputBox(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 40, self.font_medium)

        # 頁面切換按鈕 (假設)
        self.prev_page_rect = pygame.Rect(200, SCREEN_HEIGHT // 2, 50, 50)
        self.next_page_rect = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT // 2, 50, 50)

        # 主頁按鈕 (左下角)
        self.home_button_rect = pygame.Rect(0, 480, 320, 100)

        # 進入遊戲按鈕 (在主頁中央)
        self.enter_game_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 100, 100, 50)

    def show_warning(self, text, duration=2):
        """顯示臨時警告文字 (預設 2 秒後消失)"""
        self.warning_text = text
        self.warning_time = time.time() + duration

    def handle_input(self):
        """處理 Pygame 事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 如果在計時中退出，嘗試儲存（這裡設為未命名）
                if self.is_timing:
                    # 強制停止計時並計算時間
                    self.current_duration = int(time.time() - self.start_time)
                    self.stop_timer(event_name="Event")
                save_data(self.data)
                pygame.quit()
                sys.exit()

            if self.state == 'HOME':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # 進入遊戲按鈕
                    if self.enter_game_button_rect.collidepoint(mouse_pos):
                        self.state = 'GARDEN_VIEW'
                        self.current_field_index = len(self.data['trees']) - 1

            elif self.state == 'GARDEN_VIEW':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # 主頁按鈕 (左下角)
                    if self.home_button_rect.collidepoint(mouse_pos):
                        if self.is_timing:
                            # 如果還在計時就回首頁，強制結算
                            self.current_duration = int(time.time() - self.start_time)
                            self.stop_timer(event_name="未命名活動")
                        self.state = 'HOME'
                        self.selected_plant_type = 0

                    # 1. 選擇植物種類
                    for plant_type, rect in BUTTON_RECTS.items():
                        if rect.collidepoint(mouse_pos):
                            self.selected_plant_type = plant_type
                            print(f"Selected Plant Type: {PLANT_TYPES[plant_type]} ({plant_type})")
                            break

                    # 2. 開始/停止按鈕
                    if START_BUTTON_RECT.collidepoint(mouse_pos):
                        if not self.is_timing:
                            if self.selected_plant_type != 0:
                                self.start_timer()
                            else:
                                self.show_warning("請先選擇植物種類", duration=2)
                        else:
                            # --- 修改點 1: 按下 Stop 時立刻停止計時邏輯 ---
                            self.is_timing = False  # 停止計時旗標
                            # 立刻鎖定當前的持續時間，不再隨時間增加
                            self.current_duration = int(time.time() - self.start_time)

                            self.state = 'INPUT_NAME'  # 進入輸入名稱狀態
                            self.input_box.text = ''  # 清空輸入框
                            self.input_box.active = True  # 自動聚焦

                    # 3. 頁面切換
                    if self.prev_page_rect.collidepoint(mouse_pos) and self.current_field_index > 0:
                        self.current_field_index -= 1
                    if self.next_page_rect.collidepoint(mouse_pos) and self.current_field_index < len(
                            self.data['trees']) - 1:
                        self.current_field_index += 1

            elif self.state == 'INPUT_NAME':
                # 處理文字輸入框事件
                event_name = self.input_box.handle_event(event)
                if event_name is not None:
                    # 按 Enter 後保存並返回花園頁面
                    self.stop_timer(event_name)
                    self.state = 'GARDEN_VIEW'

    def start_timer(self):
        """開始計時，並找到種植位置。"""
        self.planting_index = get_current_planting_index(self.data)

        if self.planting_index == -1:
            # 頁面已滿，新增頁面
            create_new_field(self.data)
            self.current_field_index = len(self.data['trees']) - 1
            self.planting_index = 0

        self.is_timing = True
        self.start_time = time.time()
        print(f"Timer started for {PLANT_TYPES[self.selected_plant_type]}. Planting at index {self.planting_index}")

    def stop_timer(self, event_name):
        """
        保存數據。
        注意：這裡不再計算時間，因為在 handle_input 按下 Stop 時已經鎖定在 self.current_duration 了。
        """

        # 更新資料
        current_field = self.data['trees'][-1]

        # 只有在有選擇植物且有位置時才更新
        if self.selected_plant_type != 0 and self.planting_index != -1:
            # 確保是在最新的田地進行種植
            if current_field['type'][self.planting_index] == 0:
                current_field['type'][self.planting_index] = self.selected_plant_type
                # 使用已經鎖定的 self.current_duration
                current_field['time'][self.planting_index] = self.current_duration
                current_field['eventName'][self.planting_index] = event_name

                # 儲存資料
                save_data(self.data)
                print(f"Data saved. Duration: {self.current_duration}s. Name: '{event_name}'")
            else:
                print("Error: Plot was unexpectedly not empty.")
        else:
            print("Timer stopped, but no plant selected or no index found. Data not saved.")

        # 重置計時和選擇狀態
        self.current_duration = 0
        self.selected_plant_type = 0
        self.planting_index = -1
        # self.is_timing 已經在 handle_input 設為 False 了

    def update(self):
        """更新遊戲邏輯，例如計時器。"""
        # 只有當 is_timing 為 True 時才更新時間
        # 當按下 Stop 進入 INPUT_NAME 狀態後，is_timing 會變成 False，時間就會鎖定
        if self.is_timing:
            self.current_duration = int(time.time() - self.start_time)

    def draw(self):
        """繪製所有遊戲元素。"""
        if self.state == 'HOME':
            self.draw_home()
        elif self.state == 'GARDEN_VIEW':
            self.draw_garden()
        elif self.state == 'INPUT_NAME':
            self.draw_garden()  # 先畫花園 (讓背景和植物保持顯示)
            self.draw_input_name()  # 再疊上輸入框

        pygame.display.flip()

    def draw_home(self):
        """繪製主頁"""
        self.screen.blit(self.home_img, (0, 0))

        # 進入遊戲按鈕
        button_img = self.start_button_img
        self.screen.blit(button_img, self.enter_game_button_rect)

    def draw_garden(self):
        """繪製花園頁面"""
        self.screen.blit(self.background_img, (0, 0))

        # --- 繪製園丁網格 (當前頁面) ---
        current_field = self.data['trees'][self.current_field_index]

        # 判斷是否應該顯示「正在種植」的狀態
        # 條件：正在計時(is_timing) 或者 正在輸入名稱(INPUT_NAME)
        is_active_session = self.is_timing or (self.state == 'INPUT_NAME')

        for i in range(9):
            x, y = PLOT_POSITIONS[i]
            plant_type = current_field['type'][i]
            plant_time = current_field['time'][i]
            event_name = current_field['eventName'][i]

            duration_to_display = plant_time
            is_growing_now = False

            # 正在計時(或等待輸入)且是當前種植位置
            if is_active_session and self.planting_index == i and self.current_field_index == len(
                    self.data['trees']) - 1:
                duration_to_display = self.current_duration
                plant_type = self.selected_plant_type
                is_growing_now = True

            # 繪製植物
            if plant_type != 0:
                plant_sprite = get_plant_sprite(plant_type, duration_to_display)
                # 將圖片中心放在網格位置
                rect = plant_sprite.get_rect(center=(x, y))
                self.screen.blit(plant_sprite, rect)

                # 繪製植物身上的 label
                label_text_1 = ""
                label_text_2 = ""
                if is_growing_now:
                    label_text_1 = f"{PLANT_TYPES.get(plant_type, 'N/A')}: {format_time(duration_to_display)}"
                    label_text_2 = "(GROWING...)" if self.is_timing else "(PAUSED)"  # 等待輸入時顯示 PAUSED
                else:
                    label_text_1 = f"{PLANT_TYPES.get(plant_type, 'N/A')}: {event_name}"
                    label_text_2 = f"{format_time(duration_to_display)}"

                draw_text(self.screen, label_text_1, self.font_smallMedium, BLACK, x + (i % 3 - 1) * 30, y - 80, center=True, bg_color=PLANT_COLORS.get(plant_type))
                draw_text(self.screen, label_text_2, self.font_small, BLACK, x + (i % 3 - 1) * 30, y - 60, center=True, bg_color=PLANT_COLORS.get(plant_type))

        # --- 繪製植物選擇按鈕 ---
        for plant_type, rect in BUTTON_RECTS.items():
            # 繪製按鈕框
            pygame.draw.circle(self.screen, (255, 247, 214), (rect.x + rect.width / 2, rect.y + rect.width / 2), 40)
            # 繪製圖標
            icon_rect = self.plant_select_imgs[plant_type].get_rect(center=rect.center)
            self.screen.blit(self.plant_select_imgs[plant_type], icon_rect)
            # 如果被選中，繪製高亮邊框
            if self.selected_plant_type == plant_type:
                pygame.draw.rect(self.screen, GREEN, rect, 3)

        # --- 繪製計時器 ---
        # 修改點 2: 如果在計時中 OR 在輸入名稱狀態，都顯示 current_duration
        timer_text = format_time(self.current_duration) if is_active_session else "00:00:00"
        draw_text(self.screen, timer_text, self.font_large, BLACK, 800, 40, center=True, bg_color=LIGHT_GREY)

        # --- 繪製開始/停止按鈕 ---
        if is_active_session:
            button_img = self.stop_button_img
        else:
            button_img = self.start_button_img

        self.screen.blit(button_img, START_BUTTON_RECT)

        # --- 繪製頁面切換按鈕 ---
        draw_text(self.screen, "<", self.font_large, BLACK, self.prev_page_rect.centerx, self.prev_page_rect.centery,
                  center=True, bg_color=LIGHT_GREY)
        draw_text(self.screen, ">", self.font_large, BLACK, self.next_page_rect.centerx, self.next_page_rect.centery,
                  center=True, bg_color=LIGHT_GREY)
        page_info = f"Garden {self.current_field_index + 1}/{len(self.data['trees'])}"
        draw_text(self.screen, page_info, self.font_medium, BLACK, SCREEN_WIDTH // 2, 25, center=True, bg_color=WHITE)

        # --- 繪製主頁按鈕 (左下角) ---
        button_img = self.home_button_img
        self.screen.blit(button_img, home_button_rect)

        # --- 繪製警告提示文字 ---
        if self.warning_text and time.time() < self.warning_time:
            # 遮罩背景
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            self.screen.blit(s, (0, 0))

            # 繪製提示文字
            draw_text(self.screen, self.warning_text, self.font_large, (255, 100, 100),
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True, bg_color=(255, 255, 200))

    def draw_input_name(self):
        """繪製輸入名稱畫面"""
        # 遮罩背景
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))  # 半透明黑色
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
