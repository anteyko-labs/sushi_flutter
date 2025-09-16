import pandas as pd
import re

def norm(s):
    return s.strip().lower().replace('ё','е')

# Маппинг для объединения дублей
mapping = {
    'нори': ['нори','нори'],
    'рис': ['рис','рис'],
    'сыр творожный': ['сыр твор','сыр товр','твор сыр','сыр творож'],
    'краб': ['краб'],
    'огурец': ['огурец','огурцы'],
    'майонез': ['майонез'],
    'икра масаго': ['масага кр','икра масага'],
    'васаби': ['васаби'],
    'соевый соус': ['соевый соус'],
    'имбирь': ['имбир','имбирь'],
    'семга': ['семга'],
    'лосось': ['лосось','капч лосось'],
    'яйцо': ['яйцо'],
    'курица': ['курица','капчен кур'],
    'сырный соус': ['сырный соус','сырный соус 350'],
    'перец': ['перец'],
    'сахар': ['сахар'],
    'соль': ['соль'],
    'вода': ['вода'],
    'шоколад': ['шоколад'],
    'банан': ['банан'],
    'клубника': ['клубника'],
    'киви': ['киви'],
    'чипсы': ['чипсы'],
    'сухари': ['сухари'],
    'мука': ['мука'],
    'сыр пармезан': ['сыр пармизан'],
    'сыр чеддер': ['сыр чеддер'],
    'омлет': ['омлет'],
    'ширачи': ['ширачи'],
    'мицукан': ['мицукан'],
    'унаги соус': ['унаги соус'],
    'сприн тесто': ['сприн тесто'],
    'угорь': ['угорь'],
    'кунжут': ['кунжут'],
}

def get_unit(qty):
    qty = str(qty).replace(',', '.').replace('гр', ' г').replace('шт', ' шт').replace(' ', '')
    m = re.match(r'([\d\.]+)(г|шт)', qty)
    return m.group(2) if m else ''

def main():
    df = pd.read_excel('sushi.xlsx')
    ings = {}
    for i, row in df.iterrows():
        ing = str(row.get('Ингредиент', '')).strip()
        qty = str(row.get('нетто', ''))
        unit = get_unit(qty)
        ing_n = norm(ing)
        found = False
        for k, vals in mapping.items():
            if any(norm(v) == ing_n for v in vals):
                ings[k] = unit or ings.get(k, '')
                found = True
                break
        if not found and ing_n:
            ings[ing_n] = unit or ings.get(ing_n, '')
    # Сохраняем ingredients.xlsx
    out = pd.DataFrame([
        {'id': i+1, 'name': k, 'quantity': 0, 'unit': v or '', 'price_per_unit': 0}
        for i, (k, v) in enumerate(sorted(ings.items()))
    ])
    out.to_excel('ingredients.xlsx', index=False)
    print('Ингредиенты успешно нормализованы и сохранены!')

def update_rolls_and_recipes():
    # Загрузка нормализованных ингредиентов
    ingredients_df = pd.read_excel('ingredients.xlsx')
    ing_name_to_id = {str(row['name']).strip().lower(): row['id'] for _, row in ingredients_df.iterrows()}

    # Загрузка sushi.xlsx
    df = pd.read_excel('sushi.xlsx')
    # Список роллов
    rolls = []
    recipes = []
    roll_id = 1
    last_roll_name = None
    roll_name_to_id = {}
    for i, row in df.iterrows():
        name = str(row.get('Название суши', '')).strip()
        ing = str(row.get('Ингредиент', '')).strip()
        qty = str(row.get('нетто', '')).replace(',', '.').replace('гр', '').replace('г', '').replace('шт', '').replace(' ', '')
        unit = 'г' if 'г' in str(row.get('нетто', '')) else ('шт' if 'шт' in str(row.get('нетто', '')) else '')
        if name and name.lower() != 'nan':
            if name not in roll_name_to_id:
                roll_name_to_id[name] = roll_id
                rolls.append({'id': roll_id, 'name': name, 'sale_price': ''})
                last_roll_name = name
                roll_id += 1
        if ing and ing.lower() != 'nan' and last_roll_name:
            ing_norm = ing.strip().lower().replace('ё','е')
            ing_id = ing_name_to_id.get(ing_norm)
            if not ing_id:
                # Попробуем найти по частичному совпадению
                for k in ing_name_to_id:
                    if ing_norm in k or k in ing_norm:
                        ing_id = ing_name_to_id[k]
                        break
            if ing_id:
                try:
                    amount = float(qty)
                except:
                    amount = 0
                recipes.append({'roll_id': roll_name_to_id[last_roll_name], 'ingredient_id': ing_id, 'amount_per_roll': amount})
    # Сохраняем rolls.xlsx
    rolls_df = pd.DataFrame(rolls)
    rolls_df.to_excel('rolls.xlsx', index=False)
    # Сохраняем roll_recipes.xlsx
    recipes_df = pd.DataFrame(recipes)
    recipes_df.to_excel('roll_recipes.xlsx', index=False)
    print('Роллы и рецепты успешно обновлены!')

if __name__ == '__main__':
    main()
    update_rolls_and_recipes() 