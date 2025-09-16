import pandas as pd
import os
from datetime import datetime

# Пути к файлам базы данных
INGREDIENTS_FILE = 'ingredients.xlsx'
ROLLS_FILE = 'rolls.xlsx'
ROLL_RECIPES_FILE = 'roll_recipes.xlsx'
ORDERS_FILE = 'orders.xlsx'
EMPLOYEES_FILE = 'employees.xlsx'
ATTENDANCE_FILE = 'attendance.xlsx'
STOCK_HISTORY_FILE = 'stock_history.xlsx'
SETS_FILE = 'sets.xlsx'
SET_COMPOSITION_FILE = 'set_composition.xlsx'

# Статусы заказов
ORDER_STATUSES = [
    'Принят',
    'Готовится',
    'Готов',
    'Отправлен',
    'Доставлен'
]

def init_db():
    if not os.path.exists(INGREDIENTS_FILE):
        df = pd.DataFrame(columns=['id', 'name', 'quantity', 'unit', 'price_per_unit'])
        df.to_excel(INGREDIENTS_FILE, index=False)
    if not os.path.exists(ROLLS_FILE):
        df = pd.DataFrame(columns=['id', 'name', 'sale_price'])
        df.to_excel(ROLLS_FILE, index=False)
    if not os.path.exists(ROLL_RECIPES_FILE):
        df = pd.DataFrame(columns=['roll_id', 'ingredient_id', 'amount_per_roll'])
        df.to_excel(ROLL_RECIPES_FILE, index=False)
    if not os.path.exists(ORDERS_FILE):
        df = pd.DataFrame(columns=['id', 'roll_id', 'set_id', 'quantity', 'order_time', 'total_price', 'cost_per_roll', 'status', 'comment', 'order_type'])
        df.to_excel(ORDERS_FILE, index=False)
    if not os.path.exists(EMPLOYEES_FILE):
        df = pd.DataFrame([
            {'id': 1, 'name': 'Админ', 'login': 'admin', 'password': 'admin123', 'role': 'admin'},
            {'id': 2, 'name': 'Шеф-повар', 'login': 'chef', 'password': '123345', 'role': 'chef'},
            {'id': 3, 'name': 'Сотрудник', 'login': 'staff', 'password': '123456', 'role': 'staff'},
            {'id': 4, 'name': 'Бухгалтер', 'login': 'accountant', 'password': '123789', 'role': 'accountant'}
        ])
        df.to_excel(EMPLOYEES_FILE, index=False)
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['employee_id', 'name', 'role', 'date', 'time', 'mark_type'])
        df.to_excel(ATTENDANCE_FILE, index=False)
    if not os.path.exists(STOCK_HISTORY_FILE):
        df = pd.DataFrame(columns=['date', 'ingredient_id', 'ingredient_name', 'operation', 'amount', 'comment'])
        df.to_excel(STOCK_HISTORY_FILE, index=False)
    if not os.path.exists(SETS_FILE):
        df = pd.DataFrame(columns=['id', 'name', 'cost_price', 'retail_price', 'set_price', 'discount_percent', 'gross_profit', 'margin_percent'])
        df.to_excel(SETS_FILE, index=False)
    if not os.path.exists(SET_COMPOSITION_FILE):
        df = pd.DataFrame(columns=['set_id', 'roll_id', 'roll_name'])
        df.to_excel(SET_COMPOSITION_FILE, index=False)

def fill_test_data():
    import numpy as np
    # Ингредиенты
    ingredients = [
        {'id': 1, 'name': 'Рис', 'quantity': 10, 'unit': 'кг', 'price_per_unit': 100},
        {'id': 2, 'name': 'Лосось', 'quantity': 5, 'unit': 'кг', 'price_per_unit': 800},
        {'id': 3, 'name': 'Сыр сливочный', 'quantity': 3, 'unit': 'кг', 'price_per_unit': 500},
        {'id': 4, 'name': 'Огурец', 'quantity': 2, 'unit': 'кг', 'price_per_unit': 120},
        {'id': 5, 'name': 'Нори', 'quantity': 100, 'unit': 'лист', 'price_per_unit': 20},
        {'id': 6, 'name': 'Крабовые палочки', 'quantity': 2, 'unit': 'кг', 'price_per_unit': 300},
        {'id': 7, 'name': 'Авокадо', 'quantity': 1, 'unit': 'кг', 'price_per_unit': 400},
        {'id': 8, 'name': 'Икра масаго', 'quantity': 0.5, 'unit': 'кг', 'price_per_unit': 1500},
        {'id': 9, 'name': 'Угорь', 'quantity': 1, 'unit': 'кг', 'price_per_unit': 1200},
        {'id': 10, 'name': 'Кунжут', 'quantity': 0.5, 'unit': 'кг', 'price_per_unit': 200},
    ]
    pd.DataFrame(ingredients).to_excel(INGREDIENTS_FILE, index=False)
    # Роллы
    rolls = [
        {'id': 1, 'name': 'Филадельфия', 'sale_price': ''},
        {'id': 2, 'name': 'Калифорния', 'sale_price': ''},
        {'id': 3, 'name': 'Каппа маки', 'sale_price': ''},
        {'id': 4, 'name': 'Унаги маки', 'sale_price': ''},
        {'id': 5, 'name': 'Крабовый ролл', 'sale_price': ''},
    ]
    pd.DataFrame(rolls).to_excel(ROLLS_FILE, index=False)
    # Рецепты роллов
    roll_recipes = [
        # Филадельфия
        {'roll_id': 1, 'ingredient_id': 1, 'amount_per_roll': 0.12}, # Рис
        {'roll_id': 1, 'ingredient_id': 2, 'amount_per_roll': 0.06}, # Лосось
        {'roll_id': 1, 'ingredient_id': 3, 'amount_per_roll': 0.03}, # Сыр
        {'roll_id': 1, 'ingredient_id': 5, 'amount_per_roll': 1},    # Нори
        # Калифорния
        {'roll_id': 2, 'ingredient_id': 1, 'amount_per_roll': 0.10}, # Рис
        {'roll_id': 2, 'ingredient_id': 6, 'amount_per_roll': 0.04}, # Крабовые палочки
        {'roll_id': 2, 'ingredient_id': 4, 'amount_per_roll': 0.02}, # Огурец
        {'roll_id': 2, 'ingredient_id': 8, 'amount_per_roll': 0.01}, # Икра масаго
        {'roll_id': 2, 'ingredient_id': 5, 'amount_per_roll': 1},    # Нори
        # Каппа маки
        {'roll_id': 3, 'ingredient_id': 1, 'amount_per_roll': 0.08}, # Рис
        {'roll_id': 3, 'ingredient_id': 4, 'amount_per_roll': 0.03}, # Огурец
        {'roll_id': 3, 'ingredient_id': 5, 'amount_per_roll': 1},    # Нори
        # Унаги маки
        {'roll_id': 4, 'ingredient_id': 1, 'amount_per_roll': 0.09}, # Рис
        {'roll_id': 4, 'ingredient_id': 9, 'amount_per_roll': 0.04}, # Угорь
        {'roll_id': 4, 'ingredient_id': 5, 'amount_per_roll': 1},    # Нори
        {'roll_id': 4, 'ingredient_id': 10, 'amount_per_roll': 0.005}, # Кунжут
        # Крабовый ролл
        {'roll_id': 5, 'ingredient_id': 1, 'amount_per_roll': 0.09}, # Рис
        {'roll_id': 5, 'ingredient_id': 6, 'amount_per_roll': 0.05}, # Крабовые палочки
        {'roll_id': 5, 'ingredient_id': 3, 'amount_per_roll': 0.02}, # Сыр
        {'roll_id': 5, 'ingredient_id': 5, 'amount_per_roll': 1},    # Нори
    ]
    pd.DataFrame(roll_recipes).to_excel(ROLL_RECIPES_FILE, index=False)

def fill_sets_data():
    """Заполнение данных о сетах"""
    sets_data = [
        {
            'id': 1, 'name': 'Классический', 'cost_price': 453.32, 'retail_price': 1685, 
            'set_price': 1360, 'discount_percent': 19, 'gross_profit': 907, 'margin_percent': 200
        },
        {
            'id': 2, 'name': 'Бюджетный', 'cost_price': 203.62, 'retail_price': 960, 
            'set_price': 610, 'discount_percent': 36, 'gross_profit': 406, 'margin_percent': 200
        },
        {
            'id': 3, 'name': 'Темпура', 'cost_price': 384.72, 'retail_price': 1570, 
            'set_price': 1150, 'discount_percent': 27, 'gross_profit': 765, 'margin_percent': 199
        },
        {
            'id': 4, 'name': 'Запечённый', 'cost_price': 386.06, 'retail_price': 1565, 
            'set_price': 1160, 'discount_percent': 26, 'gross_profit': 774, 'margin_percent': 200
        },
        {
            'id': 5, 'name': 'Фила Премиум', 'cost_price': 749.64, 'retail_price': 3020, 
            'set_price': 2250, 'discount_percent': 26, 'gross_profit': 1500, 'margin_percent': 200
        },
        {
            'id': 6, 'name': 'Хит Комбо', 'cost_price': 746.10, 'retail_price': 2880, 
            'set_price': 2240, 'discount_percent': 22, 'gross_profit': 1494, 'margin_percent': 200
        },
        {
            'id': 7, 'name': 'Party Mix', 'cost_price': 1034.68, 'retail_price': 4050, 
            'set_price': 3100, 'discount_percent': 23, 'gross_profit': 2065, 'margin_percent': 252
        },
        {
            'id': 8, 'name': 'Для компании', 'cost_price': 693.46, 'retail_price': 2815, 
            'set_price': 2080, 'discount_percent': 26, 'gross_profit': 1387, 'margin_percent': 200
        },
        {
            'id': 9, 'name': 'Anteyko', 'cost_price': 1087.28, 'retail_price': 4615, 
            'set_price': 3400, 'discount_percent': 26.3, 'gross_profit': 2312, 'margin_percent': 213
        },
        {
            'id': 10, 'name': 'Набор на двоих', 'cost_price': 408.67, 'retail_price': 1645, 
            'set_price': 1250, 'discount_percent': 24, 'gross_profit': 841.33, 'margin_percent': 205
        },
        {
            'id': 11, 'name': 'Набор на троих', 'cost_price': 454.19, 'retail_price': 1940, 
            'set_price': 1450, 'discount_percent': 25.26, 'gross_profit': 995.81, 'margin_percent': 219.3
        },
        {
            'id': 12, 'name': 'Chill на Филармонии', 'cost_price': 595.94, 'retail_price': 2400, 
            'set_price': 1800, 'discount_percent': 25, 'gross_profit': 1204.06, 'margin_percent': 202.1
        }
    ]
    
    # Сохраняем данные о сетах
    pd.DataFrame(sets_data).to_excel(SETS_FILE, index=False)
    
    # Состав сетов (пример для нескольких сетов)
    set_composition = [
        # Классический
        {'set_id': 1, 'roll_id': 1, 'roll_name': 'Калифорния'},
        {'set_id': 1, 'roll_id': 2, 'roll_name': 'Филадельфия'},
        {'set_id': 1, 'roll_id': 3, 'roll_name': 'Темпура Чикен маки'},
        {'set_id': 1, 'roll_id': 4, 'roll_name': 'Саке маки'},
        
        # Бюджетный
        {'set_id': 2, 'roll_id': 5, 'roll_name': 'Овощной ролл'},
        {'set_id': 2, 'roll_id': 6, 'roll_name': 'Мини ролл огурец'},
        {'set_id': 2, 'roll_id': 7, 'roll_name': 'Запеченная Маки курица'},
        {'set_id': 2, 'roll_id': 4, 'roll_name': 'Саке маки'},
        
        # Темпура
        {'set_id': 3, 'roll_id': 8, 'roll_name': 'Лосось темпура'},
        {'set_id': 3, 'roll_id': 9, 'roll_name': 'Курица темпура'},
        {'set_id': 3, 'roll_id': 10, 'roll_name': 'Угорь темпура'},
        
        # Запечённый
        {'set_id': 4, 'roll_id': 11, 'roll_name': 'Запечённый магистр'},
        {'set_id': 4, 'roll_id': 12, 'roll_name': 'Запечённая фила'},
        {'set_id': 4, 'roll_id': 13, 'roll_name': 'Унаги запечённый'},
        
        # Фила Премиум
        {'set_id': 5, 'roll_id': 14, 'roll_name': 'Фила спешл'},
        {'set_id': 5, 'roll_id': 15, 'roll_name': 'Копчёная фила'},
        {'set_id': 5, 'roll_id': 16, 'roll_name': 'Фила с угрём'},
        {'set_id': 5, 'roll_id': 2, 'roll_name': 'Филадельфия'},
        
        # Хит Комбо
        {'set_id': 6, 'roll_id': 2, 'roll_name': 'Филадельфия'},
        {'set_id': 6, 'roll_id': 1, 'roll_name': 'Калифорния'},
        {'set_id': 6, 'roll_id': 11, 'roll_name': 'Запечённый магистр'},
        {'set_id': 6, 'roll_id': 12, 'roll_name': 'Запечённая фила'},
        {'set_id': 6, 'roll_id': 8, 'roll_name': 'Лосось темпура'},
        
        # Party Mix
        {'set_id': 7, 'roll_id': 1, 'roll_name': 'Калифорния'},
        {'set_id': 7, 'roll_id': 2, 'roll_name': 'Филадельфия'},
        {'set_id': 7, 'roll_id': 8, 'roll_name': 'Лосось темпура'},
        {'set_id': 7, 'roll_id': 10, 'roll_name': 'Угорь темпура'},
        {'set_id': 7, 'roll_id': 17, 'roll_name': 'Сладкий ролл'},
        {'set_id': 7, 'roll_id': 5, 'roll_name': 'Овощной ролл'},
        {'set_id': 7, 'roll_id': 18, 'roll_name': 'Чедр ролл'},
        {'set_id': 7, 'roll_id': 19, 'roll_name': 'Острый лосось'},
        
        # Для компании
        {'set_id': 8, 'roll_id': 9, 'roll_name': 'Курица темпура'},
        {'set_id': 8, 'roll_id': 2, 'roll_name': 'Филадельфия'},
        {'set_id': 8, 'roll_id': 1, 'roll_name': 'Калифорния'},
        {'set_id': 8, 'roll_id': 20, 'roll_name': 'Ролл нежный (запеч.)'},
        {'set_id': 8, 'roll_id': 11, 'roll_name': 'Запечённый магистр'},
        {'set_id': 8, 'roll_id': 7, 'roll_name': 'Запеченная Маки курица'},
        {'set_id': 8, 'roll_id': 21, 'roll_name': 'Ролл Чикаго'},
        
        # Anteyko
        {'set_id': 9, 'roll_id': 1, 'roll_name': 'Калифорния'},
        {'set_id': 9, 'roll_id': 22, 'roll_name': 'Запеченная филадельфия'},
        {'set_id': 9, 'roll_id': 21, 'roll_name': 'Чикаго ролл'},
        {'set_id': 9, 'roll_id': 16, 'roll_name': 'Фила с угрем'},
        {'set_id': 9, 'roll_id': 14, 'roll_name': 'Филадельфия спешл'},
        {'set_id': 9, 'roll_id': 17, 'roll_name': 'Сладкий ролл'},
        {'set_id': 9, 'roll_id': 9, 'roll_name': 'Курица темпура'},
        {'set_id': 9, 'roll_id': 20, 'roll_name': 'Ролл нежный'},
        {'set_id': 9, 'roll_id': 5, 'roll_name': 'Овощной ролл'},
        
        # Набор на двоих
        {'set_id': 10, 'roll_id': 23, 'roll_name': 'Ролл томаго'},
        {'set_id': 10, 'roll_id': 14, 'roll_name': 'Фила спешл'},
        {'set_id': 10, 'roll_id': 20, 'roll_name': 'Ролл запеченный нежный'},
        
        # Набор на троих
        {'set_id': 11, 'roll_id': 22, 'roll_name': 'Запеченная Филадельфия'},
        {'set_id': 11, 'roll_id': 11, 'roll_name': 'Запеченный магистр'},
        {'set_id': 11, 'roll_id': 21, 'roll_name': 'Чикаго ролл'},
        {'set_id': 11, 'roll_id': 9, 'roll_name': 'Курица темпура'},
        
        # Chill на Филармонии
        {'set_id': 12, 'roll_id': 2, 'roll_name': 'Филадельфия'},
        {'set_id': 12, 'roll_id': 19, 'roll_name': 'Острый лосось'},
        {'set_id': 12, 'roll_id': 7, 'roll_name': 'Запеченный Маки курица'},
        {'set_id': 12, 'roll_id': 18, 'roll_name': 'Чедр ролл'},
        {'set_id': 12, 'roll_id': 21, 'roll_name': 'Чикаго ролл'}
    ]
    
    # Сохраняем состав сетов
    pd.DataFrame(set_composition).to_excel(SET_COMPOSITION_FILE, index=False)

# Вызов инициализации при импорте
init_db()
# fill_test_data()  # ОТКЛЮЧЕНО: чтобы не затирать актуальные данные
# fill_sets_data()  # ОТКЛЮЧЕНО: чтобы не затирать актуальные данные

def migrate_orders_add_status():
    if os.path.exists(ORDERS_FILE):
        df = pd.read_excel(ORDERS_FILE)
        updated = False
        
        # Добавляем недостающие колонки
        if 'status' not in df.columns:
            df['status'] = 'Готовится'
            updated = True
        
        if 'set_id' not in df.columns:
            df['set_id'] = None
            updated = True
            
        if 'order_type' not in df.columns:
            df['order_type'] = 'roll'
            updated = True
        
        if updated:
            df.to_excel(ORDERS_FILE, index=False)
            print("Миграция заказов завершена")
    
    # Создать файл для расхода по заказам, если нет
    ORDER_INGREDIENTS_FILE = 'order_ingredients.xlsx'
    if not os.path.exists(ORDER_INGREDIENTS_FILE):
        pd.DataFrame(columns=['order_id', 'ingredient_id', 'used_amount']).to_excel(ORDER_INGREDIENTS_FILE, index=False)

migrate_orders_add_status()
ORDER_INGREDIENTS_FILE = 'order_ingredients.xlsx' 