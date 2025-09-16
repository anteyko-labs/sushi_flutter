import pandas as pd
import os

def increase_ingredients_quantity():
    """
    Увеличивает количество всех ингредиентов в 10 раз
    """
    try:
        print("Увеличиваю количество всех ингредиентов в 10 раз...")
        
        # Читаем файл ингредиентов
        ingredients_df = pd.read_csv('ingredients.csv', sep=';')
        
        print(f"Найдено {len(ingredients_df)} ингредиентов")
        
        # Увеличиваем количество в 10 раз
        for idx, row in ingredients_df.iterrows():
            old_quantity = row['quantity']
            new_quantity = old_quantity * 10
            ingredients_df.at[idx, 'quantity'] = new_quantity
            print(f"{row['name']}: {old_quantity} → {new_quantity} {row['unit']}")
        
        # Сохраняем обновленный файл
        ingredients_df.to_csv('ingredients.csv', sep=';', index=False)
        
        # Также обновляем Excel версию
        ingredients_df.to_excel('ingredients.xlsx', index=False)
        
        print(f"\n✅ Увеличено количество для {len(ingredients_df)} ингредиентов")
        print("Файлы ingredients.csv и ingredients.xlsx обновлены")
        
        # Показываем примеры обновленных количеств
        print("\nПримеры обновленных количеств:")
        sample_ingredients = ingredients_df.head(10)
        for _, row in sample_ingredients.iterrows():
            print(f"{row['name']}: {row['quantity']} {row['unit']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    increase_ingredients_quantity()
