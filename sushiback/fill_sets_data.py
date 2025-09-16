#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для заполнения данных о сетах
Запускать только один раз для инициализации данных
"""

import pandas as pd
import os
from models import fill_sets_data

if __name__ == "__main__":
    print("Заполнение данных о сетах...")
    
    # Проверяем, существуют ли уже файлы с сетами
    if os.path.exists('sets.xlsx'):
        response = input("Файл sets.xlsx уже существует. Перезаписать? (y/N): ")
        if response.lower() != 'y':
            print("Операция отменена.")
            exit()
    
    try:
        fill_sets_data()
        print("✅ Данные о сетах успешно заполнены!")
        print("📁 Созданы файлы:")
        print("   - sets.xlsx - информация о сетах")
        print("   - set_composition.xlsx - состав сетов")
        print("\nТеперь вы можете:")
        print("1. Открыть приложение и перейти на страницу 'Сеты'")
        print("2. Добавлять сеты в заказы")
        print("3. Просматривать статистику по сете в отчетах")
    except Exception as e:
        print(f"❌ Ошибка при заполнении данных: {e}")
        print("Проверьте, что все необходимые файлы существуют и доступны для записи.")
