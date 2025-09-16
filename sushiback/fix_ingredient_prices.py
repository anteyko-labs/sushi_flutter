import pandas as pd
import os

def fix_ingredient_prices():
    """
    Устанавливает правильные цены ингредиентов на основе данных из Excel файла
    """
    try:
        print("Читаю Excel файл для получения цен ингредиентов...")
        
        # Читаем Excel файл
        df = pd.read_excel('calc_for_sushi.xlsx')
        
        # Создаем словарь с ценами ингредиентов за грамм
        ingredient_prices = {}
        
        for _, row in df.iterrows():
            ingredient = row['Ингридиенты']
            price_per_gram = row['Цена/гр']
            
            # Если есть название ингредиента и цена за грамм
            if pd.notna(ingredient) and pd.notna(price_per_gram):
                ingredient = str(ingredient).strip()
                if ingredient and ingredient != 'nan':
                    # Цена за грамм
                    ingredient_prices[ingredient] = float(price_per_gram)
        
        print(f"Найдено {len(ingredient_prices)} ингредиентов с ценами")
        
        # Теперь обновляем файл ingredients.csv
        print("Обновляю цены ингредиентов...")
        
        # Читаем текущий файл ингредиентов
        ingredients_df = pd.read_csv('ingredients.csv', sep=';')
        
        # Обновляем цены
        updated_count = 0
        for idx, row in ingredients_df.iterrows():
            ingredient_name = row['name']
            
            # Ищем соответствующую цену
            if ingredient_name in ingredient_prices:
                old_price = row['price_per_unit']
                new_price = ingredient_prices[ingredient_name]
                ingredients_df.at[idx, 'price_per_unit'] = new_price
                updated_count += 1
                print(f"Обновлена цена для {ingredient_name}: {old_price} → {new_price}")
            else:
                # Если ингредиент не найден в Excel, устанавливаем базовую цену
                if row['price_per_unit'] == 0:
                    # Устанавливаем примерную цену в зависимости от типа ингредиента
                    if 'рис' in ingredient_name.lower():
                        ingredients_df.at[idx, 'price_per_unit'] = 0.05  # 5 копеек за грамм
                    elif 'рыба' in ingredient_name.lower() or 'лосось' in ingredient_name.lower() or 'семга' in ingredient_name.lower():
                        ingredients_df.at[idx, 'price_per_unit'] = 0.8  # 80 копеек за грамм
                    elif 'курица' in ingredient_name.lower():
                        ingredients_df.at[idx, 'price_per_unit'] = 0.3  # 30 копеек за грамм
                    elif 'сыр' in ingredient_name.lower():
                        ingredients_df.at[idx, 'price_per_unit'] = 0.4  # 40 копеек за грамм
                    elif 'овощ' in ingredient_name.lower() or 'огурец' in ingredient_name.lower() or 'помидор' in ingredient_name.lower():
                        ingredients_df.at[idx, 'price_per_unit'] = 0.1  # 10 копеек за грамм
                    elif 'соус' in ingredient_name.lower():
                        ingredients_df.at[idx, 'price_per_unit'] = 0.2  # 20 копеек за грамм
                    else:
                        ingredients_df.at[idx, 'price_per_unit'] = 0.15  # 15 копеек за грамм по умолчанию
        
        # Сохраняем обновленный файл
        ingredients_df.to_csv('ingredients.csv', sep=';', index=False)
        
        # Также обновляем Excel версию
        ingredients_df.to_excel('ingredients.xlsx', index=False)
        
        print(f"\n✅ Обновлено {updated_count} ингредиентов")
        print("Файлы ingredients.csv и ingredients.xlsx обновлены")
        
        # Показываем примеры обновленных цен
        print("\nПримеры обновленных цен:")
        sample_ingredients = ingredients_df.head(10)
        for _, row in sample_ingredients.iterrows():
            print(f"{row['name']}: {row['price_per_unit']} руб/г")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    fix_ingredient_prices()
