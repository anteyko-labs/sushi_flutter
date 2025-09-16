#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска Flutter приложения после исправлений
"""

import subprocess
import time

def start_flutter_final():
    print("🚀 ЗАПУСК FLUTTER ПРИЛОЖЕНИЯ (ФИНАЛЬНАЯ ВЕРСИЯ)")
    print("=" * 60)
    
    print("📋 ЧТО ИСПРАВЛЕНО:")
    print("✅ База данных полная (25 роллов, 14 сетов, 130 заказов)")
    print("✅ API возвращает правильные цены (поле 'price')")
    print("✅ Шеф-повар видит все заказы")
    print("✅ Корзина работает")
    print("✅ Заказы создаются и попадают к шеф-повару")
    
    print("\n🔑 ЛОГИНЫ:")
    print("👤 Обычный пользователь: oo@gmail.com / 123456")
    print("👨‍🍳 Шеф-повар: chef@sushiroll.com / chef123")
    
    print("\n📱 ЧТО ДОЛЖНО РАБОТАТЬ:")
    print("✅ Роллы и сеты с названиями, фото и ценами")
    print("✅ Добавление товаров в корзину")
    print("✅ Оформление заказов")
    print("✅ Шеф-повар видит все заказы от клиентов")
    print("✅ Шеф-повар может менять статусы заказов")
    
    print("\n🌐 Запуск Flutter приложения...")
    print("   URL: http://localhost:3000")
    
    try:
        # Запускаем Flutter приложение
        process = subprocess.Popen([
            'flutter', 'run', '-d', 'chrome', '--web-port=3000'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        
        print("⏳ Ожидание запуска...")
        
        # Выводим логи
        for line in process.stdout:
            print(line.rstrip())
            
            if 'Flutter run key commands' in line:
                print("\n🎉 FLUTTER ПРИЛОЖЕНИЕ ЗАПУЩЕНО!")
                print("🔗 Откройте: http://localhost:3000")
                print("\n📝 ПРОВЕРЬТЕ:")
                print("1. Роллы и сеты отображаются с ценами")
                print("2. Корзина работает")
                print("3. Заказы создаются")
                print("4. Шеф-повар видит заказы")
                break
        
        process.wait()
        
    except FileNotFoundError:
        print("❌ Flutter не найден. Установите Flutter SDK.")
    except KeyboardInterrupt:
        print("\n⏹️  Запуск прерван")
        if process:
            process.terminate()

if __name__ == "__main__":
    start_flutter_final()

