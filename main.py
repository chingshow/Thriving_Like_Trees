import pygame
import sys
import json
import os
import time

# --- 設定常數 ---
# 遊戲尺寸: 應與背景圖片大小相同 (這裡假設為 800x600)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
DATA_FILE = 'data.json'

# 顏色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 150, 0)
LIGHT_GREY = (200, 200, 200)

# 植物種類定義 (與您的數據結構一致)
PLANT_TYPES = {
    1: "Leisure",  # 花
    2: "Work",  # 果樹
    3: "Commuting"  # 樹
}

# 成長階段 (時間單位為秒)
# STAGE_DURATIONS = {
#     1: 15 * 60,  # 900 秒 (0-15 分鐘)
#     2: 30 * 60,  # 1800 秒 (15-30 分鐘)
#     3: float('inf')  # >30 分鐘
# }
STAGE_DURATIONS = {
    1: 4,  # 900 秒 (0-15 分鐘)
    2: 3,  # 1800 秒 (15-30 分鐘)
    3: float('inf')  # >30 分鐘
}

# 網格座標 (用於 3x3 網格, 這裡假設了中心樹的位置和間隔)
# 這是根據圖片大致估計的中心點，您可能需要根據實際圖片調整
# 座標順序: 左上(0) -> 右上(2) -> 中間左(3) -> 中間右(5) -> 左下(6) -> 右下(8)
PLOT_POSITIONS = [
    (200, 150), (400, 150), (600, 150),
    (200, 300), (400, 300), (600, 300),  # 網格中心應是 (400, 300) 附近的大樹位置
    (200, 450), (400, 450), (600, 450)
]
# 這裡將中心的大樹視為背景的一部分或不可種植的固定元素，
# 故將網格繪製在周圍 8 塊，但文件說是 9 塊，
# 程式中以 9 塊 (3x3) 網格處理，並調整座標以適應圖片。
# 圖片看起來只有 8 塊土壤和一個中心大樹，如果中心大樹是固定的，那只有 8 個可種植位置。
# 但文件說有 9 塊，所以程式碼將使用 9 個位置。
# 調整後的 9 塊位置 (假設樹木圖像大小約 200x200):
PLOT_POSITIONS = [
    (250, 150), (400, 150), (550, 150),
    (250, 300), (400, 300), (550, 300),
    (250, 450), (400, 450), (550, 450)
]

# 植物選擇按鈕位置 (根據圖片右側的三個按鈕)
BUTTON_RECTS = {
    1: pygame.Rect(690, 100, 100, 100),  # 花 (Leisure)
    2: pygame.Rect(690, 250, 100, 100),  # 果樹 (Work)
    3: pygame.Rect(690, 400, 100, 100)  # 樹 (Commuting)
}

# 開始/停止按鈕位置 (圖片底部的紅色按鈕)
START_BUTTON_RECT = pygame.Rect(400 - 50, 520, 100, 50)


# --- 資料處理函式 ---

def load_data():
    """從 JSON 檔案載入資料。如果檔案不存在，則建立新的初始資料。"""
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
    """建立符合結構的初始資料。"""
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
    """將資料存入 JSON 檔案。"""
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
    """當前頁面滿時，新增一個新的 3x3 網格頁面。"""
    new_field = {
        "type": [0] * 9,
        "time": [0] * 9,
        "eventName": [""] * 9
    }
    data['trees'].append(new_field)
    save_data(data)  # 儲存新頁面


# --- 資源載入函式 ---

def load_image(filepath, size=None):
    """載入圖片並轉換以優化繪圖，可選調整大小。"""
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

def draw_text(surface, text, font, color, x, y, center=False):
    """繪製文字到螢幕。"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
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
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)

        # 載入資源
        self.background_img = load_image('./image/background.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.start_button_img = load_image('./image/start_button.png', (100, 50))
        # 載入植物選擇按鈕圖 (這裡只是佔位，您需要替換成實際圖片)
        self.plant_select_imgs = {
            1: load_image('./image/flower_icon.png', (80, 80)),
            2: load_image('./image/orange_icon.png', (80, 80)),
            3: load_image('./image/tree_icon.png', (80, 80)),
        }

        # 遊戲狀態
        self.state = 'GARDEN_VIEW'  # 'GARDEN_VIEW', 'INPUT_NAME'

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

        # 文字輸入框
        self.input_box = TextInputBox(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 40, self.font_medium)

        # 頁面切換按鈕 (假設)
        self.prev_page_rect = pygame.Rect(50, SCREEN_HEIGHT // 2, 50, 50)
        self.next_page_rect = pygame.Rect(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2, 50, 50)

    def handle_input(self):
        """處理 Pygame 事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.is_timing:
                    # 如果正在計時，則在退出前停止計時並保存 (可選)
                    self.stop_timer(event_name="未命名活動")
                save_data(self.data)
                pygame.quit()
                sys.exit()

            if self.state == 'GARDEN_VIEW':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

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
                                print("請先選擇植物種類。")
                        else:
                            self.state = 'INPUT_NAME'  # 停止計時並進入輸入名稱狀態

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
                    self.input_box.text = ''  # 清空輸入框

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
        """停止計時，計算持續時間，並更新資料。"""
        self.is_timing = False
        end_time = time.time()
        self.current_duration = int(end_time - self.start_time)

        # 更新資料
        current_field = self.data['trees'][-1]

        # 只有在有選擇植物且有位置時才更新
        if self.selected_plant_type != 0 and self.planting_index != -1:
            # 確保是在最新的田地進行種植
            if current_field['type'][self.planting_index] == 0:
                current_field['type'][self.planting_index] = self.selected_plant_type
                current_field['time'][self.planting_index] = self.current_duration
                current_field['eventName'][self.planting_index] = event_name

                # 儲存資料
                save_data(self.data)
                print(f"Timer stopped. Duration: {self.current_duration}s. Saved as '{event_name}'")
            else:
                print("Error: Plot was unexpectedly not empty.")
        else:
            print("Timer stopped, but no plant selected or no index found. Data not saved.")

        # 重置計時和選擇狀態
        self.current_duration = 0
        self.selected_plant_type = 0
        self.planting_index = -1

    def update(self):
        """更新遊戲邏輯，例如計時器。"""
        if self.is_timing:
            self.current_duration = int(time.time() - self.start_time)
            # 在計時中，當前種植的位置也會顯示正在成長的植物
            # (但在停止前不寫入 data.json)

    def draw(self):
        """繪製所有遊戲元素。"""
        self.screen.blit(self.background_img, (0, 0))

        # --- 繪製園丁網格 (當前頁面) ---
        current_field = self.data['trees'][self.current_field_index]

        for i in range(9):
            x, y = PLOT_POSITIONS[i]
            plant_type = current_field['type'][i]
            plant_time = current_field['time'][i]
            event_name = current_field['eventName'][i]

            duration_to_display = plant_time
            is_growing_now = False

            # 正在計時且是當前種植位置
            if self.is_timing and self.planting_index == i and self.current_field_index == len(self.data['trees']) - 1:
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
                label_text = ""
                if is_growing_now:
                    label_text = f"{PLANT_TYPES.get(plant_type, 'N/A')}: {format_time(duration_to_display)} (GROWING...)"
                else:
                    label_text = f"{PLANT_TYPES.get(plant_type, 'N/A')}: {event_name} - {format_time(duration_to_display)}"

                draw_text(self.screen, label_text, self.font_small, BLACK, x, y - 60, center=True)

        # --- 繪製植物選擇按鈕 ---
        for plant_type, rect in BUTTON_RECTS.items():
            # 繪製按鈕框
            pygame.draw.rect(self.screen, LIGHT_GREY, rect)
            # 繪製圖標
            icon_rect = self.plant_select_imgs[plant_type].get_rect(center=rect.center)
            self.screen.blit(self.plant_select_imgs[plant_type], icon_rect)
            # 如果被選中，繪製高亮邊框
            if self.selected_plant_type == plant_type:
                pygame.draw.rect(self.screen, GREEN, rect, 3)
            # 繪製類別名稱
            draw_text(self.screen, PLANT_TYPES[plant_type], self.font_small, BLACK, rect.centerx, rect.bottom + 5,
                      center=True)

        # --- 繪製計時器 ---
        timer_text = format_time(self.current_duration) if self.is_timing else "00:00:00"
        # 繪製計時器 (圖片右上角數字時鐘)
        draw_text(self.screen, timer_text, self.font_large, BLACK, 750, 40, center=True)

        # --- 繪製開始/停止按鈕 ---
        # 繪製圖片 (或紅色矩形)
        pygame.draw.rect(self.screen, (255, 0, 0), START_BUTTON_RECT)
        draw_text(self.screen, "STOP" if self.is_timing else "START", self.font_medium, WHITE,
                  START_BUTTON_RECT.centerx, START_BUTTON_RECT.centery, center=True)

        # --- 繪製頁面切換按鈕 ---
        draw_text(self.screen, "<", self.font_large, BLACK, self.prev_page_rect.centerx, self.prev_page_rect.centery,
                  center=True)
        draw_text(self.screen, ">", self.font_large, BLACK, self.next_page_rect.centerx, self.next_page_rect.centery,
                  center=True)
        page_info = f"Garden {self.current_field_index + 1}/{len(self.data['trees'])}"
        draw_text(self.screen, page_info, self.font_small, BLACK, SCREEN_WIDTH // 2, 50, center=True)

        # --- 繪製輸入名稱畫面 ---
        if self.state == 'INPUT_NAME':
            # 遮罩背景
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))  # 半透明黑色
            self.screen.blit(s, (0, 0))

            draw_text(self.screen, "Input Activity Name:", self.font_large, WHITE, SCREEN_WIDTH // 2,
                      SCREEN_HEIGHT // 2 - 50, center=True)
            self.input_box.draw(self.screen)
            draw_text(self.screen, "(Press Enter to Save)", self.font_small, WHITE, SCREEN_WIDTH // 2,
                      SCREEN_HEIGHT // 2 + 60, center=True)

        pygame.display.flip()

    def run(self):
        """遊戲主循環。"""
        running = True
        while running:
            self.handle_input()
            if self.state == 'GARDEN_VIEW':
                self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == '__main__':
    # 創建一個空的 image 資料夾以便運行
    if not os.path.exists('image'):
        os.makedirs('image')
        # 創建佔位符圖片
        print("Creating placeholder images in 'image/' folder. Please replace them with actual assets.")
        size = (100, 100)
        # 植物佔位符 (plant1_1.png, plant1_2.png, etc.)
        for t in range(1, 4):
            for s in range(1, 4):
                surf = pygame.Surface(size, pygame.SRCALPHA)
                surf.fill(((t - 1) * 80, (s - 1) * 80, 50, 200))  # 不同的顏色佔位
                draw_text(surf, f'{t}-{s}', pygame.font.Font(None, 30), WHITE, size[0] // 2, size[1] // 2, center=True)
                pygame.image.save(surf, f'./image/plant{t}_{s}.png')
        # 背景和按鈕佔位符
        pygame.image.save(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA), './image/background.png')
        pygame.image.save(pygame.Surface((100, 50), pygame.SRCALPHA), './image/start_button.png')
        pygame.image.save(pygame.Surface((80, 80), pygame.SRCALPHA), './image/flower_icon.png')
        pygame.image.save(pygame.Surface((80, 80), pygame.SRCALPHA), './image/orange_icon.png')
        pygame.image.save(pygame.Surface((80, 80), pygame.SRCALPHA), './image/tree_icon.png')

    # 確保 data.json 存在
    if not os.path.exists(DATA_FILE):
        save_data(create_initial_data())

    game = ThrivingLikeTrees()
    game.run()