import pandas as pd
import os

def update_recipe_costs_fixed():
    """
    Обновляет себестоимость рецептов на основе новых цен ингредиентов (исправленная версия)
    """
    try:
        print("Обновляю себестоимость рецептов...")
        
        # Читаем файлы
        ingredients_df = pd.read_csv('ingredients.csv', sep=';')
        recipes_df = pd.read_csv('roll_recipes.csv', sep=';')
        rolls_df = pd.read_csv('rolls.csv', sep=';')
        
        # Создаем словарь цен ингредиентов по ID
        ingredient_prices = {}
        for _, row in ingredients_df.iterrows():
            ingredient_prices[row['id']] = row['price_per_unit']
        
        print(f"Загружено {len(ingredient_prices)} цен ингредиентов")
        
        # Обновляем себестоимость для каждого рецепта
        updated_recipes = []
        
        for _, recipe in recipes_df.iterrows():
            roll_id = recipe['roll_id']
            ingredient_id = recipe['ingredient_id']
            amount = recipe['amount_per_roll']
            
            # Получаем цену ингредиента по ID
            if ingredient_id in ingredient_prices:
                price_per_unit = ingredient_prices[ingredient_id]
                cost = price_per_unit * amount
            else:
                # Если ингредиент не найден, используем базовую цену
                cost = 0.15 * amount
            
            # Создаем обновленную запись
            updated_recipe = {
                'roll_id': roll_id,
                'ingredient_id': ingredient_id,
                'amount_per_roll': amount,
                'cost': round(cost, 2)
            }
            updated_recipes.append(updated_recipe)
        
        # Создаем новый DataFrame
        updated_recipes_df = pd.DataFrame(updated_recipes)
        
        # Сохраняем обновленные рецепты
        updated_recipes_df.to_csv('roll_recipes.csv', sep=';', index=False)
        updated_recipes_df.to_excel('roll_recipes.xlsx', index=False)
        
        print(f"✅ Обновлено {len(updated_recipes)} рецептов")
        
        # Теперь обновляем себестоимость роллов
        print("Обновляю себестоимость роллов...")
        
        # Группируем рецепты по роллам для расчета общей себестоимости
        roll_costs = {}
        for _, recipe in updated_recipes_df.iterrows():
            roll_id = recipe['roll_id']
            cost = recipe['cost']
            
            if roll_id not in roll_costs:
                roll_costs[roll_id] = 0
            roll_costs[roll_id] += cost
        
        # Обновляем роллы
        for idx, roll in rolls_df.iterrows():
            roll_id = roll['id']
            if roll_id in roll_costs:
                rolls_df.at[idx, 'cost'] = round(roll_costs[roll_id], 2)
        
        # Сохраняем обновленные роллы
        rolls_df.to_csv('rolls.csv', sep=';', index=False)
        rolls_df.to_excel('rolls.xlsx', index=False)
        
        print(f"✅ Обновлена себестоимость для {len(roll_costs)} роллов")
        
        # Показываем примеры
        print("\nПримеры обновленных данных:")
        print("\nРецепты (первые 5):")
        sample_recipes = updated_recipes_df.head()
        for _, recipe in sample_recipes.iterrows():
            ingredient_name = ingredients_df[ingredients_df['id'] == recipe['ingredient_id']]['name'].iloc[0] if len(ingredients_df[ingredients_df['id'] == recipe['ingredient_id']]) > 0 else f"ID{recipe['ingredient_id']}"
            print(f"Ролл {recipe['roll_id']}, {ingredient_name}: {recipe['amount_per_roll']}г, стоимость: {recipe['cost']} руб")
        
        print("\nРоллы с себестоимостью (первые 5):")
        sample_rolls = rolls_df.head()
        for _, roll in sample_rolls.iterrows():
            print(f"{roll['name']}: себестоимость {roll['cost']} руб, цена продажи {roll['sale_price']} руб")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    update_recipe_costs_fixed()
