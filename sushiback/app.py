import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify, send_file, send_from_directory
from models import init_db
import pandas as pd
from models import INGREDIENTS_FILE
from models import ROLLS_FILE
from models import ORDERS_FILE
from datetime import datetime
from models import ORDER_INGREDIENTS_FILE
import pandas as pd
STOCK_HISTORY_FILE = 'stock_history.xlsx'
from functools import wraps
import zipfile
import io
import glob

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Для flash-сообщений

# Создание папок для шаблонов и статики, если их нет
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Инициализация базы данных
init_db()

AUDIT_LOG_FILE = 'audit_log.xlsx'

def log_audit(action, object_type, object_name, details, comment=None):
    import pandas as pd
    from datetime import datetime
    import os
    role = session.get('role', 'unknown')
    row = {
        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'object_type': object_type,
        'object_name': object_name,
        'details': details,
        'role': role,
        'comment': comment or ''
    }
    if os.path.exists(AUDIT_LOG_FILE):
        df = pd.read_excel(AUDIT_LOG_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_excel(AUDIT_LOG_FILE, index=False)

@app.before_request
def require_login():
    allowed = ['login', 'static']
    if 'role' not in session and request.endpoint not in allowed:
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        role = request.form['role']
        password = request.form['password']
        if (role == 'chef' and password == '123345') or (role == 'staff' and password == '123456') or (role == 'accountant' and password == '123789') or (role == 'owner' and password == 'owner123'):
            session['role'] = role
            return redirect(url_for('index'))
        else:
            error = 'Неверный пароль'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Декоратор для ограничения доступа
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Ограничения на разделы
@app.route('/ingredients', methods=['GET', 'POST'])
@role_required(['chef'])
def ingredients():
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        name = request.form['name']
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
        price_per_unit = float(request.form['price_per_unit'])
        comment = request.form.get('comment', '')
        df = pd.read_excel(INGREDIENTS_FILE)
        new_id = (df['id'].max() + 1) if not df.empty else 1
        new_row = pd.DataFrame([{
            'id': new_id,
            'name': name,
            'quantity': quantity,
            'unit': unit,
            'price_per_unit': price_per_unit
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(INGREDIENTS_FILE, index=False)
        log_audit('Добавление', 'Ингредиент', name, f'Остаток: {quantity} {unit}, Цена: {price_per_unit}', comment)
        return redirect(url_for('ingredients'))
    df = pd.read_excel(INGREDIENTS_FILE)
    # Для отображения использования ингредиента в роллах
    recipes_df = pd.read_excel('roll_recipes.xlsx')
    rolls_df = pd.read_excel(ROLLS_FILE)
    ingredients = df.to_dict(orient='records')
    for ing in ingredients:
        uses = []
        for _, rec in recipes_df[recipes_df['ingredient_id'] == ing['id']].iterrows():
            roll_row = rolls_df[rolls_df['id'] == rec['roll_id']]
            if not roll_row.empty:
                uses.append(f"{roll_row.iloc[0]['name']} ({rec['amount_per_roll']} {ing['unit']})")
        ing['used_in'] = ', '.join(uses) if uses else '—'
    return render_template('ingredients.html', ingredients=ingredients)

@app.route('/ingredients/edit/<int:ing_id>', methods=['GET', 'POST'])
@role_required(['chef'])
def edit_ingredient(ing_id):
    df = pd.read_excel(INGREDIENTS_FILE)
    ing_row = df[df['id'] == ing_id]
    if ing_row.empty:
        flash('Ингредиент не найден', 'danger')
        return redirect(url_for('ingredients'))
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        old = ing_row.iloc[0].to_dict()
        new = {
            'name': request.form['name'],
            'quantity': float(request.form['quantity']),
            'unit': request.form['unit'],
            'price_per_unit': float(request.form['price_per_unit'])
        }
        comment = request.form.get('comment', '')
        df.loc[df['id'] == ing_id, 'name'] = new['name']
        df.loc[df['id'] == ing_id, 'quantity'] = new['quantity']
        df.loc[df['id'] == ing_id, 'unit'] = new['unit']
        df.loc[df['id'] == ing_id, 'price_per_unit'] = new['price_per_unit']
        df.to_excel(INGREDIENTS_FILE, index=False)
        details = f"Было: {old}, Стало: {new}"
        log_audit('Редактирование', 'Ингредиент', new['name'], details, comment)
        flash('Ингредиент обновлён', 'success')
        return redirect(url_for('ingredients'))
    # GET: показать форму редактирования
    # Для шаблона ingredients.html нужно передать edit_ingredient
    recipes_df = pd.read_excel('roll_recipes.xlsx')
    rolls_df = pd.read_excel(ROLLS_FILE)
    ingredients = df.to_dict(orient='records')
    for ing in ingredients:
        uses = []
        for _, rec in recipes_df[recipes_df['ingredient_id'] == ing['id']].iterrows():
            roll_row = rolls_df[rolls_df['id'] == rec['roll_id']]
            if not roll_row.empty:
                uses.append(f"{roll_row.iloc[0]['name']} ({rec['amount_per_roll']} {ing['unit']})")
        ing['used_in'] = ', '.join(uses) if uses else '—'
    return render_template('ingredients.html', ingredients=ingredients, edit_ingredient=ing_row.iloc[0].to_dict())

@app.route('/ingredients/delete/<int:ing_id>')
@role_required(['chef'])
def delete_ingredient(ing_id):
    df = pd.read_excel(INGREDIENTS_FILE)
    ing_row = df[df['id'] == ing_id]
    if ing_row.empty:
        flash('Ингредиент не найден', 'danger')
    else:
        name = ing_row.iloc[0]['name']
        df = df[df['id'] != ing_id]
        df.to_excel(INGREDIENTS_FILE, index=False)
        log_audit('Удаление', 'Ингредиент', name, f'Удалён ингредиент {name}')
        flash('Ингредиент удалён', 'success')
    return redirect(url_for('ingredients'))

@app.route('/rolls', methods=['GET', 'POST'])
@role_required(['chef'])
def rolls():
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        name = request.form['name']
        sale_price = request.form.get('sale_price', '')
        df = pd.read_excel(ROLLS_FILE)
        new_id = (df['id'].max() + 1) if not df.empty else 1
        new_row = pd.DataFrame([{'id': new_id, 'name': name, 'sale_price': sale_price}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(ROLLS_FILE, index=False)
        log_audit('Добавление', 'Ролл', name, f'Добавлен ролл: {name}')
        return redirect(url_for('rolls'))
    df = pd.read_excel(ROLLS_FILE)
    rolls = df.to_dict(orient='records')
    return render_template('rolls.html', rolls=rolls)

@app.route('/sets')
@role_required(['chef', 'staff'])
def sets():
    """Страница с сетов"""
    from models import SETS_FILE, SET_COMPOSITION_FILE
    
    if not os.path.exists(SETS_FILE):
        return render_template('sets.html', sets=[], rolls=[])
    
    sets_df = pd.read_excel(SETS_FILE)
    composition_df = pd.read_excel(SET_COMPOSITION_FILE) if os.path.exists(SET_COMPOSITION_FILE) else pd.DataFrame()
    
    # Загружаем роллы для редактирования состава
    rolls_df = pd.read_excel(ROLLS_FILE)
    rolls = rolls_df.to_dict(orient='records')
    
    sets_data = []
    for _, set_row in sets_df.iterrows():
        set_id = set_row['id']
        composition = composition_df[composition_df['set_id'] == set_id].to_dict(orient='records')
        
        sets_data.append({
            'id': set_row['id'],
            'name': set_row['name'],
            'cost_price': set_row['cost_price'],
            'retail_price': set_row['retail_price'],
            'set_price': set_row['set_price'],
            'discount_percent': set_row['discount_percent'],
            'gross_profit': set_row['gross_profit'],
            'margin_percent': set_row['margin_percent'],
            'composition': composition
        })
    
    return render_template('sets.html', sets=sets_data, rolls=rolls)

@app.route('/sets/edit', methods=['POST'])
@role_required(['chef'])
def edit_set():
    """Редактирование сета"""
    from models import SETS_FILE
    
    set_id = int(request.form['set_id'])
    name = request.form['name']
    cost_price = float(request.form['cost_price'])
    retail_price = float(request.form['retail_price'])
    set_price = float(request.form['set_price'])
    discount_percent = float(request.form['discount_percent'])
    
    # Рассчитываем прибыль и маржу
    gross_profit = set_price - cost_price
    margin_percent = (gross_profit / cost_price * 100) if cost_price > 0 else 0
    
    # Обновляем данные в файле
    sets_df = pd.read_excel(SETS_FILE)
    sets_df.loc[sets_df['id'] == set_id, 'name'] = name
    sets_df.loc[sets_df['id'] == set_id, 'cost_price'] = cost_price
    sets_df.loc[sets_df['id'] == set_id, 'retail_price'] = retail_price
    sets_df.loc[sets_df['id'] == set_id, 'set_price'] = set_price
    sets_df.loc[sets_df['id'] == set_id, 'discount_percent'] = discount_percent
    sets_df.loc[sets_df['id'] == set_id, 'gross_profit'] = gross_profit
    sets_df.loc[sets_df['id'] == set_id, 'margin_percent'] = margin_percent
    
    sets_df.to_excel(SETS_FILE, index=False)
    
    log_audit('Редактирование', 'Сет', name, f'Обновлены параметры: цена сета {set_price}с, себестоимость {cost_price}с', None)
    flash(f'Сет "{name}" успешно обновлен', 'success')
    
    return redirect(url_for('sets'))

@app.route('/sets/edit_composition', methods=['POST'])
@role_required(['chef'])
def edit_set_composition():
    """Редактирование состава сета"""
    from models import SET_COMPOSITION_FILE
    
    set_id = int(request.form['set_id'])
    roll_ids = request.form.getlist('roll_ids[]')
    
    # Удаляем старый состав
    composition_df = pd.read_excel(SET_COMPOSITION_FILE)
    composition_df = composition_df[composition_df['set_id'] != set_id]
    
    # Добавляем новый состав
    new_composition = []
    for roll_id in roll_ids:
        if roll_id:  # Проверяем, что roll_id не пустой
            # Получаем название ролла
            rolls_df = pd.read_excel(ROLLS_FILE)
            roll_name = rolls_df[rolls_df['id'] == int(roll_id)]['name'].iloc[0] if not rolls_df[rolls_df['id'] == int(roll_id)].empty else f'Ролл {roll_id}'
            
            new_composition.append({
                'set_id': set_id,
                'roll_id': int(roll_id),
                'roll_name': roll_name
            })
    
    # Добавляем новый состав в файл
    if new_composition:
        new_df = pd.DataFrame(new_composition)
        composition_df = pd.concat([composition_df, new_df], ignore_index=True)
    
    composition_df.to_excel(SET_COMPOSITION_FILE, index=False)
    
    # Пересчитываем себестоимость сета
    from models import SETS_FILE
    sets_df = pd.read_excel(SETS_FILE)
    set_name = sets_df[sets_df['id'] == set_id]['name'].iloc[0] if not sets_df[sets_df['id'] == set_id].empty else f'Сет {set_id}'
    
    # Рассчитываем новую себестоимость на основе состава
    total_cost = 0
    for composition in new_composition:
        roll_id = composition['roll_id']
        # Получаем рецепт ролла
        recipes_df = pd.read_excel('roll_recipes.xlsx')
        roll_recipe = recipes_df[recipes_df['roll_id'] == roll_id]
        
        for _, recipe_row in roll_recipe.iterrows():
            ingredient_id = recipe_row['ingredient_id']
            amount = recipe_row['amount_per_roll']
            
            # Получаем цену ингредиента
            ingredients_df = pd.read_excel(INGREDIENTS_FILE)
            ingredient = ingredients_df[ingredients_df['id'] == ingredient_id]
            if not ingredient.empty:
                price_per_unit = ingredient.iloc[0]['price_per_unit']
                total_cost += amount * price_per_unit
    
    # Обновляем себестоимость сета
    sets_df.loc[sets_df['id'] == set_id, 'cost_price'] = total_cost
    
    # Пересчитываем прибыль и маржу
    set_price = sets_df.loc[sets_df['id'] == set_id, 'set_price'].iloc[0]
    gross_profit = set_price - total_cost
    margin_percent = (gross_profit / total_cost * 100) if total_cost > 0 else 0
    
    sets_df.loc[sets_df['id'] == set_id, 'gross_profit'] = gross_profit
    sets_df.loc[sets_df['id'] == set_id, 'margin_percent'] = margin_percent
    
    sets_df.to_excel(SETS_FILE, index=False)
    
    log_audit('Редактирование', 'Состав сета', set_name, f'Обновлен состав: {len(new_composition)} роллов, новая себестоимость: {total_cost:.2f}с', None)
    flash(f'Состав сета "{set_name}" успешно обновлен', 'success')
    
    return redirect(url_for('sets'))

@app.route('/sets/<int:set_id>/composition')
@role_required(['chef'])
def get_set_composition(set_id):
    """Получить состав сета для AJAX"""
    from models import SET_COMPOSITION_FILE
    
    if not os.path.exists(SET_COMPOSITION_FILE):
        return jsonify([])
    
    composition_df = pd.read_excel(SET_COMPOSITION_FILE)
    composition = composition_df[composition_df['set_id'] == set_id].to_dict(orient='records')
    
    return jsonify(composition)

@app.route('/rolls/<int:roll_id>', methods=['GET', 'POST'])
@role_required(['chef'])
def roll_detail(roll_id):
    rolls_df = pd.read_excel(ROLLS_FILE)
    roll = rolls_df[rolls_df['id'] == roll_id]
    if roll.empty:
        return 'Ролл не найден', 404
    roll_name = roll.iloc[0]['name']
    recipes_df = pd.read_excel('roll_recipes.xlsx')
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    # Добавление ингредиента в рецепт
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        ing_id = int(request.form['ingredient_id'])
        amount = float(request.form['amount_per_roll'])
        # Проверка на дублирование
        if not recipes_df[(recipes_df['roll_id'] == roll_id) & (recipes_df['ingredient_id'] == ing_id)].empty:
            flash('Этот ингредиент уже есть в рецепте', 'danger')
        else:
            new_row = pd.DataFrame([{'roll_id': roll_id, 'ingredient_id': ing_id, 'amount_per_roll': amount}])
            recipes_df = pd.concat([recipes_df, new_row], ignore_index=True)
            recipes_df.to_excel('roll_recipes.xlsx', index=False)
            ing_name = ingredients_df[ingredients_df['id'] == ing_id].iloc[0]['name'] if not ingredients_df[ingredients_df['id'] == ing_id].empty else str(ing_id)
            log_audit('Добавление', 'Рецепт ролла', roll_name, f'Добавлен ингредиент: {ing_name}, {amount}', None)
            flash('Ингредиент добавлен в рецепт', 'success')
        return redirect(url_for('roll_detail', roll_id=roll_id))
    # Состав ролла
    recipe = recipes_df[recipes_df['roll_id'] == roll_id]
    ingredients = []
    total_cost = 0
    for _, rec in recipe.iterrows():
        ing_row = ingredients_df[ingredients_df['id'] == rec['ingredient_id']]
        if not ing_row.empty:
            ing = ing_row.iloc[0]
            used = rec['amount_per_roll']
            cost = used * ing['price_per_unit']
            total_cost += cost
            ingredients.append({
                'id': rec['ingredient_id'],
                'name': ing['name'],
                'used': used,
                'unit': ing['unit'],
                'on_stock': ing['quantity'],
                'price_per_unit': ing['price_per_unit'],
                'cost': cost
            })
    # Для формы добавления ингредиента
    used_ids = set(recipe['ingredient_id'])
    available_ingredients = [
        {'id': int(ing['id']), 'name': ing['name'], 'unit': ing['unit']} 
        for _, ing in ingredients_df.iterrows() if ing['id'] not in used_ids
    ]
    return render_template('roll_detail.html', roll_name=roll_name, ingredients=ingredients, total_cost=total_cost, roll_id=roll_id, available_ingredients=available_ingredients)

@app.route('/rolls/<int:roll_id>/delete_ingredient/<int:ingredient_id>')
@role_required(['chef'])
def delete_roll_ingredient(roll_id, ingredient_id):
    recipes_df = pd.read_excel('roll_recipes.xlsx')
    rolls_df = pd.read_excel(ROLLS_FILE)
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    roll_name = rolls_df[rolls_df['id'] == roll_id].iloc[0]['name'] if not rolls_df[rolls_df['id'] == roll_id].empty else str(roll_id)
    ing_name = ingredients_df[ingredients_df['id'] == ingredient_id].iloc[0]['name'] if not ingredients_df[ingredients_df['id'] == ingredient_id].empty else str(ingredient_id)
    recipes_df = recipes_df[~((recipes_df['roll_id'] == roll_id) & (recipes_df['ingredient_id'] == ingredient_id))]
    recipes_df.to_excel('roll_recipes.xlsx', index=False)
    log_audit('Удаление', 'Рецепт ролла', roll_name, f'Удалён ингредиент: {ing_name}', None)
    flash('Ингредиент удалён из рецепта', 'success')
    return redirect(url_for('roll_detail', roll_id=roll_id))

@app.route('/rolls/<int:roll_id>/edit_ingredient/<int:ingredient_id>', methods=['GET', 'POST'])
@role_required(['chef'])
def edit_roll_ingredient(roll_id, ingredient_id):
    recipes_df = pd.read_excel('roll_recipes.xlsx')
    rec = recipes_df[(recipes_df['roll_id'] == roll_id) & (recipes_df['ingredient_id'] == ingredient_id)]
    rolls_df = pd.read_excel(ROLLS_FILE)
    roll_name = rolls_df[rolls_df['id'] == roll_id].iloc[0]['name'] if not rolls_df[rolls_df['id'] == roll_id].empty else ''
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    ing_row = ingredients_df[ingredients_df['id'] == ingredient_id]
    ing_name = ing_row.iloc[0]['name'] if not ing_row.empty else ''
    if rec.empty:
        flash('Ингредиент не найден в рецепте', 'danger')
        return redirect(url_for('roll_detail', roll_id=roll_id))
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        old_amount = rec.iloc[0]['amount_per_roll']
        new_amount = float(request.form['amount_per_roll'])
        recipes_df.loc[(recipes_df['roll_id'] == roll_id) & (recipes_df['ingredient_id'] == ingredient_id), 'amount_per_roll'] = new_amount
        recipes_df.to_excel('roll_recipes.xlsx', index=False)
        log_audit('Редактирование', 'Рецепт ролла', roll_name, f'Ингредиент: {ing_name}, Было: {old_amount}, Стало: {new_amount}', None)
        flash('Количество обновлено', 'success')
        return redirect(url_for('roll_detail', roll_id=roll_id))
    amount = rec.iloc[0]['amount_per_roll']
    return render_template('edit_roll_ingredient.html', roll_id=roll_id, ingredient_id=ingredient_id, roll_name=roll_name, ing_name=ing_name, amount=amount)

@app.route('/rolls/edit/<int:roll_id>', methods=['GET', 'POST'])
@role_required(['chef'])
def edit_roll(roll_id):
    df = pd.read_excel(ROLLS_FILE)
    roll_row = df[df['id'] == roll_id]
    if roll_row.empty:
        flash('Ролл не найден', 'danger')
        return redirect(url_for('rolls'))
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        old_name = roll_row.iloc[0]['name']
        new_name = request.form['name']
        new_sale_price = request.form.get('sale_price', roll_row.iloc[0].get('sale_price', ''))
        df.loc[df['id'] == roll_id, 'name'] = new_name
        df.loc[df['id'] == roll_id, 'sale_price'] = new_sale_price
        df.to_excel(ROLLS_FILE, index=False)
        log_audit('Редактирование', 'Ролл', new_name, f'Было: {old_name}, Стало: {new_name}')
        flash('Ролл обновлён', 'success')
        return redirect(url_for('rolls'))
    rolls = df.to_dict(orient='records')
    return render_template('rolls.html', rolls=rolls, edit_roll=roll_row.iloc[0].to_dict())

@app.route('/rolls/delete/<int:roll_id>')
@role_required(['chef'])
def delete_roll(roll_id):
    df = pd.read_excel(ROLLS_FILE)
    roll_row = df[df['id'] == roll_id]
    if roll_row.empty:
        flash('Ролл не найден', 'danger')
    else:
        name = roll_row.iloc[0]['name']
        df = df[df['id'] != roll_id]
        df.to_excel(ROLLS_FILE, index=False)
        log_audit('Удаление', 'Ролл', name, f'Удалён ролл: {name}')
        flash('Ролл удалён', 'success')
    return redirect(url_for('rolls'))

@app.route('/rolls/add', methods=['GET', 'POST'])
@role_required(['chef'])
def add_roll():
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        name = request.form['name']
        sale_price = request.form.get('sale_price', '')
        # Добавляем ролл
        rolls_df = pd.read_excel(ROLLS_FILE)
        new_id = (rolls_df['id'].max() + 1) if not rolls_df.empty else 1
        new_row = pd.DataFrame([{'id': new_id, 'name': name, 'sale_price': sale_price}])
        rolls_df = pd.concat([rolls_df, new_row], ignore_index=True)
        rolls_df.to_excel(ROLLS_FILE, index=False)
        # Добавляем состав
        recipes_df = pd.read_excel('roll_recipes.xlsx')
        for ing in ingredients_df.itertuples():
            amount = request.form.get(f'ingredient_{ing.id}')
            if amount:
                try:
                    amount = float(amount)
                    if amount > 0:
                        new_recipe = pd.DataFrame([{'roll_id': new_id, 'ingredient_id': ing.id, 'amount_per_roll': amount}])
                        recipes_df = pd.concat([recipes_df, new_recipe], ignore_index=True)
                except ValueError:
                    pass
        recipes_df.to_excel('roll_recipes.xlsx', index=False)
        flash('Ролл добавлен', 'success')
        return redirect(url_for('roll_detail', roll_id=new_id))
    return render_template('add_roll.html', ingredients=ingredients_df.to_dict(orient='records'))

@app.route('/orders', methods=['GET', 'POST'])
@role_required(['chef', 'staff'])
def orders():
    error = None
    rolls_df = pd.read_excel(ROLLS_FILE)
    rolls = rolls_df.to_dict(orient='records')
    if request.method == 'POST':
        if session.get('role') == 'owner':
            abort(403)
        roll_id = int(request.form['roll_id'])
        quantity = int(request.form['quantity'])
        comment = request.form.get('comment', '')
        roll = rolls_df[rolls_df['id'] == roll_id]
        if roll.empty:
            error = 'Ролл не найден.'
        else:
            # Проверка остатков ингредиентов
            recipes_df = pd.read_excel('roll_recipes.xlsx')
            ingredients_df = pd.read_excel(INGREDIENTS_FILE)
            not_enough = []
            used_ingredients = []
            total_cost = 0
            cost_per_roll = 0
            for _, rec in recipes_df[recipes_df['roll_id'] == roll_id].iterrows():
                ing_id = rec['ingredient_id']
                need = rec['amount_per_roll'] * quantity
                ing_row = ingredients_df[ingredients_df['id'] == ing_id]
                if ing_row.empty or ing_row.iloc[0]['quantity'] < need:
                    not_enough.append(ing_row.iloc[0]['name'] if not ing_row.empty else f'ID {ing_id}')
                used_ingredients.append((ing_id, need))
                if not ing_row.empty:
                    cost_per_roll += rec['amount_per_roll'] * ing_row.iloc[0]['price_per_unit']
                    total_cost += rec['amount_per_roll'] * ing_row.iloc[0]['price_per_unit'] * quantity
            if not_enough:
                error = 'Не хватает ингредиентов: ' + ', '.join(not_enough)
            else:
                # Вычитаем ингредиенты сразу при добавлении заказа
                for ing_id, need in used_ingredients:
                    idx = ingredients_df[ingredients_df['id'] == ing_id].index[0]
                    ingredients_df.at[idx, 'quantity'] -= need
                ingredients_df.to_excel(INGREDIENTS_FILE, index=False)
                orders_df = pd.read_excel(ORDERS_FILE)
                new_id = (orders_df['id'].max() + 1) if not orders_df.empty else 1
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_row = pd.DataFrame([{
                    'id': new_id,
                    'roll_id': roll_id,
                    'set_id': None,
                    'quantity': quantity,
                    'order_time': now,
                    'total_price': total_cost,
                    'cost_per_roll': cost_per_roll,
                    'status': 'Принят',
                    'comment': comment,
                    'order_type': 'roll'
                }])
                orders_df = pd.concat([orders_df, new_row], ignore_index=True)
                orders_df.to_excel(ORDERS_FILE, index=False)
                return redirect(url_for('orders'))
    # Обработка действия "Сделан"
    if request.args.get('done'):
        order_id = int(request.args.get('done'))
        orders_df = pd.read_excel(ORDERS_FILE)
        order = orders_df[orders_df['id'] == order_id]
        if not order.empty and order.iloc[0]['status'] == 'Готовится':
            roll_id = order.iloc[0]['roll_id']
            quantity = order.iloc[0]['quantity']
            # Получаем рецепт ролла
            recipes_df = pd.read_excel('roll_recipes.xlsx')
            order_ingredients_df = pd.read_excel(ORDER_INGREDIENTS_FILE)
            # Просто фиксируем расход по заказу (ингредиенты уже вычтены)
            for _, rec in recipes_df[recipes_df['roll_id'] == roll_id].iterrows():
                ing_id = rec['ingredient_id']
                need = rec['amount_per_roll'] * quantity
                order_ingredients_df = pd.concat([
                    order_ingredients_df,
                    pd.DataFrame([{'order_id': order_id, 'ingredient_id': ing_id, 'used_amount': need}])
                ], ignore_index=True)
            order_ingredients_df.to_excel(ORDER_INGREDIENTS_FILE, index=False)
            # Меняем статус заказа
            orders_df.loc[orders_df['id'] == order_id, 'status'] = 'Сделан'
            orders_df.to_excel(ORDERS_FILE, index=False)
            return redirect(url_for('orders'))
    # GET: показать список заказов
    orders_df = pd.read_excel(ORDERS_FILE)
    orders = []
    
    # Загружаем данные о сетах для отображения заказов
    from models import SETS_FILE, SET_COMPOSITION_FILE
    sets_df = pd.read_excel(SETS_FILE) if os.path.exists(SETS_FILE) else pd.DataFrame()
    composition_df = pd.read_excel(SET_COMPOSITION_FILE) if os.path.exists(SET_COMPOSITION_FILE) else pd.DataFrame()
    
    # Загружаем данные о сетах для формы заказа
    sets_for_form = sets_df.to_dict(orient='records') if not sets_df.empty else []
    
    for _, row in orders_df.iterrows():
        order_type = row.get('order_type', 'roll')
        
        if order_type == 'set' and 'set_id' in row and row['set_id'] is not None:
            # Заказ сета
            set_data = sets_df[sets_df['id'] == row['set_id']]
            if not set_data.empty:
                set_name = set_data.iloc[0]['name']
                # Получаем состав сета
                set_composition = composition_df[composition_df['set_id'] == row['set_id']]
                composition_text = ', '.join([comp['roll_name'] for _, comp in set_composition.iterrows()])
                item_name = f"Сет: {set_name} ({composition_text})"
            else:
                item_name = f"Сет ID:{row['set_id']}"
        else:
            # Заказ ролла
            roll_name = rolls_df[rolls_df['id'] == row['roll_id']]['name'].values[0] if not rolls_df[rolls_df['id'] == row['roll_id']].empty else '—'
            item_name = roll_name
        
        orders.append({
            'id': row['id'],
            'order_time': row['order_time'],
            'item_name': item_name,
            'order_type': order_type,
            'quantity': row['quantity'],
            'cost_per_roll': row['cost_per_roll'] if 'cost_per_roll' in row else '',
            'total_price': row['total_price'],
            'status': row['status'] if 'status' in row else 'Готовится',
            'comment': row['comment'] if 'comment' in row else ''
        })
    return render_template('orders.html', orders=orders, rolls=rolls, sets=sets_for_form, error=error)

@app.route('/orders/add_set', methods=['POST'])
@role_required(['chef', 'staff'])
def add_set_to_order():
    """Добавление сета в заказ"""
    if session.get('role') == 'owner':
        abort(403)
    
    from models import SETS_FILE, SET_COMPOSITION_FILE, ROLLS_FILE
    
    set_id = int(request.form['set_id'])
    quantity = int(request.form['quantity'])
    comment = request.form.get('comment', '')
    
    # Получаем данные о сете
    sets_df = pd.read_excel(SETS_FILE)
    set_data = sets_df[sets_df['id'] == set_id]
    if set_data.empty:
        flash('Сет не найден', 'danger')
        return redirect(url_for('sets'))
    
    set_info = set_data.iloc[0]
    set_price = set_info['set_price']
    total_cost = set_price * quantity
    
    # Получаем состав сета
    composition_df = pd.read_excel(SET_COMPOSITION_FILE)
    set_composition = composition_df[composition_df['set_id'] == set_id]
    
    # Проверяем остатки ингредиентов для всех роллов в сете
    recipes_df = pd.read_excel('roll_recipes.xlsx')
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    not_enough = []
    used_ingredients = []
    
    for _, comp in set_composition.iterrows():
        roll_id = comp['roll_id']
        roll_recipes = recipes_df[recipes_df['roll_id'] == roll_id]
        
        for _, rec in roll_recipes.iterrows():
            ing_id = rec['ingredient_id']
            need = rec['amount_per_roll'] * quantity
            ing_row = ingredients_df[ingredients_df['id'] == ing_id]
            
            if ing_row.empty or ing_row.iloc[0]['quantity'] < need:
                not_enough.append(f"{comp['roll_name']} - {ing_row.iloc[0]['name'] if not ing_row.empty else f'ID {ing_id}'}")
            else:
                used_ingredients.append((ing_id, need))
    
    if not_enough:
        flash('Не хватает ингредиентов: ' + ', '.join(not_enough), 'danger')
        return redirect(url_for('sets'))
    
    # Вычитаем ингредиенты
    for ing_id, need in used_ingredients:
        idx = ingredients_df[ingredients_df['id'] == ing_id].index[0]
        ingredients_df.at[idx, 'quantity'] -= need
    ingredients_df.to_excel(INGREDIENTS_FILE, index=False)
    
    # Добавляем заказ
    orders_df = pd.read_excel(ORDERS_FILE)
    new_id = (orders_df['id'].max() + 1) if not orders_df.empty else 1
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_row = pd.DataFrame([{
        'id': new_id,
        'roll_id': None,
        'set_id': set_id,
        'quantity': quantity,
        'order_time': now,
        'total_price': total_cost,
        'cost_per_roll': set_info['cost_price'],
        'status': 'Принят',
        'comment': comment,
        'order_type': 'set'
    }])
    
    orders_df = pd.concat([orders_df, new_row], ignore_index=True)
    orders_df.to_excel(ORDERS_FILE, index=False)
    
    flash(f'Сет "{set_info["name"]}" добавлен в заказ', 'success')
    return redirect(url_for('orders'))

@app.route('/orders/change_status/<int:order_id>', methods=['POST'])
@role_required(['chef'])
def change_order_status(order_id):
    """Изменяет статус заказа"""
    new_status = request.form.get('status')
    if new_status in ['Принят', 'Готовится', 'Готов', 'Отправлен', 'Доставлен']:
        orders_df = pd.read_excel(ORDERS_FILE)
        if not orders_df.empty and order_id in orders_df['id'].values:
            order = orders_df[orders_df['id'] == order_id].iloc[0]
            order_type = order.get('order_type', 'roll')
            
            orders_df.loc[orders_df['id'] == order_id, 'status'] = new_status
            orders_df.to_excel(ORDERS_FILE, index=False)
            
            # Логируем изменение статуса
            item_type = 'сет' if order_type == 'set' else 'ролл'
            log_audit('change_status', 'order', f'Order #{order_id} ({item_type})', f'Status changed to {new_status}')
            
            flash(f'Статус заказа #{order_id} ({item_type}) изменен на "{new_status}"', 'success')
        else:
            flash('Заказ не найден', 'error')
    else:
        flash('Неверный статус', 'error')
    
    return redirect(url_for('orders'))

@app.route('/orders/done/<int:order_id>')
@role_required(['chef'])
def order_done(order_id):
    """Отметить заказ как выполненный"""
    orders_df = pd.read_excel(ORDERS_FILE)
    order = orders_df[orders_df['id'] == order_id]
    
    if not order.empty and order.iloc[0]['status'] == 'Готовится':
        order_type = order.iloc[0].get('order_type', 'roll')
        
        if order_type == 'set':
            # Для сета нужно обработать все роллы в составе
            from models import SET_COMPOSITION_FILE
            composition_df = pd.read_excel(SET_COMPOSITION_FILE) if os.path.exists(SET_COMPOSITION_FILE) else pd.DataFrame()
            set_id = order.iloc[0]['set_id']
            set_composition = composition_df[composition_df['set_id'] == set_id]
            
            # Получаем рецепты всех роллов в сете
            recipes_df = pd.read_excel('roll_recipes.xlsx')
            order_ingredients_df = pd.read_excel(ORDER_INGREDIENTS_FILE)
            
            for _, comp in set_composition.iterrows():
                roll_id = comp['roll_id']
                roll_recipes = recipes_df[recipes_df['roll_id'] == roll_id]
                
                for _, rec in roll_recipes.iterrows():
                    ing_id = rec['ingredient_id']
                    need = rec['amount_per_roll'] * order.iloc[0]['quantity']
                    
                    # Фиксируем расход по заказу
                    order_ingredients_df = pd.concat([
                        order_ingredients_df,
                        pd.DataFrame([{'order_id': order_id, 'ingredient_id': ing_id, 'used_amount': need}])
                    ], ignore_index=True)
            
            order_ingredients_df.to_excel(ORDER_INGREDIENTS_FILE, index=False)
        
        # Меняем статус заказа
        orders_df.loc[orders_df['id'] == order_id, 'status'] = 'Сделан'
        orders_df.to_excel(ORDERS_FILE, index=False)
        
        item_type = 'сет' if order_type == 'set' else 'ролл'
        flash(f'Заказ #{order_id} ({item_type}) отмечен как выполненный', 'success')
    
    return redirect(url_for('orders'))

@app.route('/reports')
@role_required(['chef'])
def reports():
    orders_df = pd.read_excel(ORDERS_FILE)
    
    # Подсчитываем доходы по типам заказов
    completed_orders = orders_df[orders_df['status'] == 'Сделан'] if not orders_df.empty else pd.DataFrame()
    
    if not completed_orders.empty:
        roll_orders = completed_orders[completed_orders.get('order_type', 'roll') == 'roll']
        set_orders = completed_orders[completed_orders.get('order_type', 'roll') == 'set']
        
        total_income = completed_orders['total_price'].sum()
        roll_income = roll_orders['total_price'].sum() if not roll_orders.empty else 0
        set_income = set_orders['total_price'].sum() if not set_orders.empty else 0
        
        # Статистика по заказам
        total_orders = len(completed_orders)
        roll_count = len(roll_orders)
        set_count = len(set_orders)
    else:
        total_income = roll_income = set_income = 0
        total_orders = roll_count = set_count = 0
    
    # Расход ингредиентов
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    order_ingredients_df = pd.read_excel(ORDER_INGREDIENTS_FILE)
    
    # Суммируем расход по всем завершённым заказам
    usage = order_ingredients_df.merge(orders_df[['id', 'status']], left_on='order_id', right_on='id')
    usage = usage[usage['status'] == 'Сделан']
    
    ingredients_usage = []
    for _, ing in ingredients_df.iterrows():
        used = usage[usage['ingredient_id'] == ing['id']]['used_amount'].sum() if not usage.empty else 0
        ingredients_usage.append({'name': ing['name'], 'used': used})
    
    return render_template('reports.html', 
                         total_income=total_income,
                         roll_income=roll_income,
                         set_income=set_income,
                         total_orders=total_orders,
                         roll_count=roll_count,
                         set_count=set_count,
                         ingredients_usage=ingredients_usage)

@app.route('/stock', methods=['GET', 'POST'])
@role_required(['chef'])
def stock():
    import pandas as pd
    import os
    from datetime import datetime
    message = None
    ingredients_df = pd.read_excel(INGREDIENTS_FILE)
    if request.method == 'POST':
        ingredient_id = int(request.form['ingredient_id'])
        amount = float(request.form['amount'])
        operation = request.form['operation']
        comment = request.form.get('comment', '')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ing_row = ingredients_df[ingredients_df['id'] == ingredient_id]
        ingredient_name = ing_row.iloc[0]['name'] if not ing_row.empty else str(ingredient_id)
        # Обновление остатков
        if operation == 'add':
            ingredients_df.loc[ingredients_df['id'] == ingredient_id, 'quantity'] += amount
            op_type = 'Поставка'
        else:
            ingredients_df.loc[ingredients_df['id'] == ingredient_id, 'quantity'] -= amount
            op_type = 'Списание'
        ingredients_df.to_excel(INGREDIENTS_FILE, index=False)
        # Лог в историю
        if os.path.exists(STOCK_HISTORY_FILE):
            history_df = pd.read_excel(STOCK_HISTORY_FILE)
        else:
            history_df = pd.DataFrame(columns=['date', 'ingredient_id', 'ingredient_name', 'operation', 'amount', 'comment'])
        new_row = pd.DataFrame([{
            'date': now,
            'ingredient_id': ingredient_id,
            'ingredient_name': ingredient_name,
            'operation': op_type,
            'amount': amount,
            'comment': comment
        }])
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        history_df.to_excel(STOCK_HISTORY_FILE, index=False)
        message = f'{op_type} {ingredient_name} на {amount} успешно проведена.'
    # История операций
    if os.path.exists(STOCK_HISTORY_FILE):
        history_df = pd.read_excel(STOCK_HISTORY_FILE)
    else:
        history_df = pd.DataFrame(columns=['date', 'ingredient_id', 'ingredient_name', 'operation', 'amount', 'comment'])
    history = history_df.to_dict(orient='records')
    return render_template('stock.html', ingredients=ingredients_df.to_dict(orient='records'), history=history, message=message)

@app.route('/audit')
@role_required(['chef'])
def audit():
    import pandas as pd
    if os.path.exists(AUDIT_LOG_FILE):
        df = pd.read_excel(AUDIT_LOG_FILE)
        history = df.sort_values('datetime', ascending=False).to_dict(orient='records')
    else:
        history = []
    return render_template('audit.html', history=history)

@app.route('/history')
@role_required(['owner'])
def history():
    import pandas as pd
    import os
    log_file = 'audit_log.xlsx'
    if os.path.exists(log_file):
        df = pd.read_excel(log_file)
        history = df.to_dict(orient='records')
    else:
        history = []
    return render_template('history.html', history=history)

@app.route('/accounting', methods=['GET', 'POST'])
@role_required(['accountant', 'owner'])
def accounting():
    import pandas as pd
    import os
    from datetime import datetime
    from flask import send_file
    # --- Фильтрация по дате ---
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    export = request.args.get('export')
    today = datetime.today()
    if not date_from:
        date_from = today.replace(day=1).strftime('%Y-%m-%d')
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')
    # --- Загрузка данных ---
    orders_df = pd.read_excel(ORDERS_FILE) if os.path.exists(ORDERS_FILE) else pd.DataFrame()
    stock_df = pd.read_excel(STOCK_HISTORY_FILE) if os.path.exists(STOCK_HISTORY_FILE) else pd.DataFrame()
    rolls_df = pd.read_excel(ROLLS_FILE) if os.path.exists(ROLLS_FILE) else pd.DataFrame()
    recipes_df = pd.read_excel('roll_recipes.xlsx') if os.path.exists('roll_recipes.xlsx') else pd.DataFrame()
    ingredients_df = pd.read_excel(INGREDIENTS_FILE) if os.path.exists(INGREDIENTS_FILE) else pd.DataFrame()
    # --- Загрузка расходов (зп, аренда) ---
    expenses_file = 'accounting_expenses.xlsx'
    if os.path.exists(expenses_file):
        exp_df = pd.read_excel(expenses_file)
        salary = float(exp_df.get('salary', [0])[0])
        rent = float(exp_df.get('rent', [0])[0])
    else:
        salary = 0
        rent = 0
    # --- Сохранение расходов ---
    if request.method == 'POST' and 'set_expenses' in request.form:
        if session.get('role') == 'owner':
            abort(403)
        salary = float(request.form.get('salary', 0))
        rent = float(request.form.get('rent', 0))
        pd.DataFrame({'salary': [salary], 'rent': [rent]}).to_excel(expenses_file, index=False)
    # --- Продажная цена ---
    if request.method == 'POST' and 'set_price' in request.form:
        if session.get('role') == 'owner':
            abort(403)
        roll_id = int(request.form['roll_id'])
        sale_price = float(request.form['sale_price'])
        rolls_df.loc[rolls_df['id'] == roll_id, 'sale_price'] = sale_price
        rolls_df.to_excel(ROLLS_FILE, index=False)
    # --- Себестоимость и продажная цена ---
    roll_costs = {}
    for _, roll in rolls_df.iterrows():
        cost = 0
        for _, rec in recipes_df[recipes_df['roll_id'] == roll['id']].iterrows():
            ing_row = ingredients_df[ingredients_df['id'] == rec['ingredient_id']]
            if not ing_row.empty:
                cost += rec['amount_per_roll'] * ing_row.iloc[0]['price_per_unit']
        sale_price = roll['sale_price'] if 'sale_price' in roll and not pd.isna(roll['sale_price']) else round(cost * 1.2, 2)
        roll_costs[roll['id']] = {'cost': cost, 'sale_price': sale_price, 'name': roll['name']}
        if ('sale_price' not in roll or pd.isna(roll['sale_price'])) and cost > 0:
            rolls_df.loc[rolls_df['id'] == roll['id'], 'sale_price'] = sale_price
    rolls_df.to_excel(ROLLS_FILE, index=False)
    # --- Фильтрация по дате ---
    def in_period(dt):
        try:
            d = pd.to_datetime(dt).date()
            return pd.to_datetime(date_from).date() <= d <= pd.to_datetime(date_to).date()
        except:
            return False
    # --- Фильтрация заказов ---
    filtered_orders = []
    total_income = 0
    total_cost = 0
    roll_id_filter = request.args.get('roll_id')
    order_status_filter = request.args.get('order_status')
    comment_filter = request.args.get('comment', '').strip().lower()
    if not orders_df.empty:
        for _, order in orders_df.iterrows():
            if in_period(order['order_time']):
                if roll_id_filter and str(order['roll_id']) != roll_id_filter:
                    continue
                if order_status_filter and str(order.get('status', '')) != order_status_filter:
                    continue
                if comment_filter and comment_filter not in str(order.get('comment', '')).lower():
                    continue
                roll_id = order['roll_id']
                quantity = order['quantity']
                sale_price = roll_costs[roll_id]['sale_price'] if roll_id in roll_costs else 0
                cost = roll_costs[roll_id]['cost'] if roll_id in roll_costs else 0
                total_income += sale_price * quantity
                total_cost += cost * quantity
                filtered_orders.append(order)
    # --- Фильтрация поставок и списаний ---
    stock_in = []
    stock_out = []
    total_stock_in = 0
    total_stock_out = 0
    ingredient_id_filter = request.args.get('ingredient_id')
    operation_filter = request.args.get('operation')
    comment_filter_stock = comment_filter
    if not stock_df.empty:
        for _, op in stock_df.iterrows():
            if in_period(op['date']):
                if ingredient_id_filter and str(op.get('ingredient_id', '')) != ingredient_id_filter:
                    continue
                if operation_filter and str(op.get('operation', '')) != operation_filter:
                    continue
                if comment_filter_stock and comment_filter_stock not in str(op.get('comment', '')).lower():
                    continue
                if op['operation'] == 'Поставка':
                    stock_in.append(op)
                    total_stock_in += op['amount']
                elif op['operation'] == 'Списание':
                    stock_out.append(op)
                    total_stock_out += op['amount']
    # --- Экспорт в Excel ---
    if export == '1':
        # Для заказов: добавляем roll_name
        orders_export = []
        for order in filtered_orders:
            roll_id = order['roll_id']
            roll_name = roll_costs[roll_id]['name'] if roll_id in roll_costs else str(roll_id)
            row = dict(order)
            row['roll_name'] = roll_name
            orders_export.append(row)
        # Для поставок/списаний: добавляем ingredient_name
        def add_ing_name(op_list):
            res = []
            for op in op_list:
                ing_id = op.get('ingredient_id')
                ing_name = None
                for ing in ingredients_df.to_dict(orient='records'):
                    if str(ing.get('id')) == str(ing_id):
                        ing_name = ing.get('name')
                        break
                row = dict(op)
                row['ingredient_name'] = ing_name if ing_name else op.get('ingredient_name', '')
                res.append(row)
            return res
        stock_in_export = add_ing_name(stock_in)
        stock_out_export = add_ing_name(stock_out)
        with pd.ExcelWriter('accounting_export.xlsx') as writer:
            pd.DataFrame(orders_export).to_excel(writer, sheet_name='Заказы', index=False)
            pd.DataFrame(stock_in_export).to_excel(writer, sheet_name='Поставки', index=False)
            pd.DataFrame(stock_out_export).to_excel(writer, sheet_name='Списания', index=False)
            pd.DataFrame([{
                'Поступления (продажи)': total_income,
                'Себестоимость реализованного': total_cost,
                'Поставки (всего)': total_stock_in,
                'Списания (всего)': total_stock_out,
                'Зарплата': salary,
                'Аренда': rent,
                'Прибыль': total_income - total_cost - salary - rent
            }]).to_excel(writer, sheet_name='Итоги', index=False)
            # Лист "Роллы"
            rolls_export = []
            for rid, roll in roll_costs.items():
                rolls_export.append({
                    'id': rid,
                    'Название': roll['name'],
                    'Себестоимость': roll['cost'],
                    'Цена продажи': roll['sale_price']
                })
            pd.DataFrame(rolls_export).to_excel(writer, sheet_name='Роллы', index=False)
            # Лист "Ингредиенты"
            ingredients_export = []
            for ing in ingredients_df.to_dict(orient='records'):
                stock_value = (ing.get('quantity') or 0) * (ing.get('price_per_unit') or 0)
                ingredients_export.append({
                    'id': ing.get('id'),
                    'Название': ing.get('name'),
                    'Остаток': ing.get('quantity'),
                    'Ед. изм.': ing.get('unit'),
                    'Цена за ед.': ing.get('price_per_unit'),
                    'Сумма на складе': round(stock_value, 2)
                })
            pd.DataFrame(ingredients_export).to_excel(writer, sheet_name='Ингредиенты', index=False)
            # Лист "Рецепты"
            recipes_export = []
            for _, rec in recipes_df.iterrows():
                roll_id = rec['roll_id']
                ingredient_id = rec['ingredient_id']
                roll_name = roll_costs[roll_id]['name'] if roll_id in roll_costs else str(roll_id)
                ing_name = None
                for ing in ingredients_df.to_dict(orient='records'):
                    if str(ing.get('id')) == str(ingredient_id):
                        ing_name = ing.get('name')
                        break
                recipes_export.append({
                    'roll_id': roll_id,
                    'roll_name': roll_name,
                    'ingredient_id': ingredient_id,
                    'ingredient_name': ing_name if ing_name else '',
                    'amount_per_roll': rec['amount_per_roll']
                })
            pd.DataFrame(recipes_export).to_excel(writer, sheet_name='Рецепты', index=False)
            # Лист "Расход по заказам"
            if os.path.exists('order_ingredients.xlsx') and os.path.exists('orders.xlsx'):
                order_ingredients_df = pd.read_excel('order_ingredients.xlsx')
                orders_df_full = pd.read_excel('orders.xlsx')
                recipes_df_full = pd.read_excel('roll_recipes.xlsx') if os.path.exists('roll_recipes.xlsx') else pd.DataFrame()
                order_roll_map = {row['id']: row['roll_id'] for _, row in orders_df_full.iterrows()}
                roll_name_map = {rid: roll['name'] for rid, roll in roll_costs.items()}
                ing_name_map = {ing['id']: ing['name'] for ing in ingredients_df.to_dict(orient='records')}
                oi_export = []
                for _, row in order_ingredients_df.iterrows():
                    order_id = row['order_id']
                    ingredient_id = row['ingredient_id']
                    used_amount = row['used_amount']
                    roll_id = order_roll_map.get(order_id, '')
                    roll_name = roll_name_map.get(roll_id, '')
                    ing_name = ing_name_map.get(ingredient_id, '')
                    oi_export.append({
                        'order_id': order_id,
                        'roll_id': roll_id,
                        'roll_name': roll_name,
                        'ingredient_id': ingredient_id,
                        'ingredient_name': ing_name,
                        'used_amount': used_amount
                    })
                pd.DataFrame(oi_export).to_excel(writer, sheet_name='Расход по заказам', index=False)
            # Лист "Сотрудники"
            if os.path.exists('employees.xlsx'):
                employees_df = pd.read_excel('employees.xlsx')
                pd.DataFrame(employees_df).to_excel(writer, sheet_name='Сотрудники', index=False)
            # Лист "Посещаемость"
            if os.path.exists('attendance.xlsx'):
                attendance_df = pd.read_excel('attendance.xlsx')
                pd.DataFrame(attendance_df).to_excel(writer, sheet_name='Посещаемость', index=False)
        return send_file('accounting_export.xlsx', as_attachment=True)
    # --- Список ингредиентов для фильтра ---
    ingredients = ingredients_df.to_dict(orient='records') if not ingredients_df.empty else []
    return render_template('accounting.html',
        orders=filtered_orders,
        stock_in=stock_in,
        stock_out=stock_out,
        rolls=roll_costs,
        total_income=total_income,
        total_cost=total_cost,
        total_stock_in=total_stock_in,
        total_stock_out=total_stock_out,
        salary=salary,
        rent=rent,
        date_from=date_from,
        date_to=date_to,
        ingredients=ingredients
    )

@app.route('/analytics', methods=['GET'])
@role_required(['accountant', 'owner'])
def analytics():
    import pandas as pd
    import os
    from datetime import datetime
    import plotly.graph_objs as go
    import plotly.io as pio
    # --- Фильтрация по дате ---
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    today = datetime.today()
    if not date_from:
        date_from = today.replace(day=1).strftime('%Y-%m-%d')
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')
    # --- Загрузка данных ---
    orders_df = pd.read_excel(ORDERS_FILE) if os.path.exists(ORDERS_FILE) else pd.DataFrame()
    rolls_df = pd.read_excel(ROLLS_FILE) if os.path.exists(ROLLS_FILE) else pd.DataFrame()
    recipes_df = pd.read_excel('roll_recipes.xlsx') if os.path.exists('roll_recipes.xlsx') else pd.DataFrame()
    ingredients_df = pd.read_excel(INGREDIENTS_FILE) if os.path.exists(INGREDIENTS_FILE) else pd.DataFrame()
    # --- Себестоимость и продажная цена ---
    roll_costs = {}
    for _, roll in rolls_df.iterrows():
        cost = 0
        for _, rec in recipes_df[recipes_df['roll_id'] == roll['id']].iterrows():
            ing_row = ingredients_df[ingredients_df['id'] == rec['ingredient_id']]
            if not ing_row.empty:
                cost += rec['amount_per_roll'] * ing_row.iloc[0]['price_per_unit']
        sale_price = roll['sale_price'] if 'sale_price' in roll and not pd.isna(roll['sale_price']) else round(cost * 1.2, 2)
        roll_costs[roll['id']] = {'cost': cost, 'sale_price': sale_price, 'name': roll['name']}
    # --- Фильтрация по дате ---
    def in_period(dt):
        try:
            d = pd.to_datetime(dt).date()
            return pd.to_datetime(date_from).date() <= d <= pd.to_datetime(date_to).date()
        except:
            return False
    # --- Аналитика по продажам роллов ---
    sales = {}
    profit = {}
    if not orders_df.empty:
        for _, order in orders_df.iterrows():
            if in_period(order['order_time']):
                roll_id = order['roll_id']
                if roll_id not in roll_costs:
                    continue  # пропустить заказы по удалённым роллам
                quantity = order['quantity']
                sale_price = roll_costs[roll_id]['sale_price']
                cost = roll_costs[roll_id]['cost']
                sales[roll_id] = sales.get(roll_id, 0) + quantity
                profit[roll_id] = profit.get(roll_id, 0) + (sale_price - cost) * quantity
    # --- График продаж по роллам ---
    roll_names = [roll_costs[rid]['name'] for rid in sales.keys()]
    sales_values = [sales[rid] for rid in sales.keys()]
    sales_bar = go.Figure([go.Bar(x=roll_names, y=sales_values)])
    sales_bar.update_layout(title='Продажи по роллам', xaxis_title='Ролл', yaxis_title='Кол-во')
    sales_bar_html = pio.to_html(sales_bar, full_html=False)
    # --- График прибыли по роллам ---
    profit_values = [profit[rid] for rid in profit.keys()]
    profit_bar = go.Figure([go.Bar(x=roll_names, y=profit_values)])
    profit_bar.update_layout(title='Прибыль по роллам', xaxis_title='Ролл', yaxis_title='Сом')
    profit_bar_html = pio.to_html(profit_bar, full_html=False)
    return render_template('analytics.html',
        sales_bar_html=sales_bar_html,
        profit_bar_html=profit_bar_html,
        date_from=date_from,
        date_to=date_to
    )

@app.route('/api/menu')
def api_menu():
    import pandas as pd
    import os
    # Пути к файлам
    rolls_file = 'rolls.xlsx'
    roll_recipes_file = 'roll_recipes.xlsx'
    ingredients_file = 'ingredients.xlsx'
    # Проверка наличия файлов
    if not (os.path.exists(rolls_file) and os.path.exists(roll_recipes_file) and os.path.exists(ingredients_file)):
        return jsonify({'error': 'Menu data not found'}), 404
    # Чтение данных
    rolls_df = pd.read_excel(rolls_file)
    recipes_df = pd.read_excel(roll_recipes_file)
    ingredients_df = pd.read_excel(ingredients_file)
    # Категории на основе названий роллов
    def get_category(roll_name):
        name_lower = roll_name.lower()
        if 'темпура' in name_lower or 'запеч' in name_lower:
            return 'baked'
        elif 'маки' in name_lower and 'курица' in name_lower:
            return 'sushi'
        elif 'овощьной' in name_lower or 'вегетарианский' in name_lower:
            return 'vegan'
        elif 'сладкий' in name_lower:
            return 'dessert'
        elif 'соус' in name_lower:
            return 'sauces'
        else:
            return 'classic'
    # Составляем меню
    menu = []
    for _, roll in rolls_df.iterrows():
        roll_id = int(roll['id'])
        name = str(roll['name'])
        price = int(roll['sale_price']) if not pd.isna(roll['sale_price']) and str(roll['sale_price']).isdigit() else 0
        # Состав и вес
        recipe = recipes_df[recipes_df['roll_id'] == roll_id]
        ingredients = []
        weight = 0
        for _, rec in recipe.iterrows():
            ing_row = ingredients_df[ingredients_df['id'] == rec['ingredient_id']]
            if not ing_row.empty:
                ing_name = str(ing_row.iloc[0]['name'])
                amount = rec['amount_per_roll']
                if isinstance(amount, str):
                    try:
                        amount = float(amount.replace(',', '.'))
                    except:
                        amount = 0
                weight += amount if isinstance(amount, (int, float)) else 0
                ingredients.append(ing_name)
        # Категория
        category = get_category(name)
        menu.append({
            'id': roll_id,
            'name': name,
            'category': category,
            'ingredients': ', '.join(ingredients),
            'weight': int(weight),
            'price': price,
            'image': '/client_pwa/image.png'
        })
    # Категории для фронта
    categories = [
        {'id': 'classic', 'name': 'Классические роллы'},
        {'id': 'baked', 'name': 'Тёплые роллы'},
        {'id': 'sushi', 'name': 'Суши'},
        {'id': 'vegan', 'name': 'Вегетарианские'},
        {'id': 'dessert', 'name': 'Десерты'},
        {'id': 'sauces', 'name': 'Соусы'}
    ]
    return jsonify({'categories': categories, 'rolls': menu})

@app.route('/download_backups')
@role_required(['admin', 'accountant', 'owner'])
def download_backups():
    # Собираем все .xlsx-файлы в рабочей папке
    files = glob.glob('*.xlsx')
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            zf.write(file)
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='sushi_backups.zip')

@app.route('/pwa')
def pwa_index():
    return send_from_directory('client_pwa', 'index.html')

@app.route('/client_pwa/<path:filename>')
def pwa_static(filename):
    return send_from_directory('client_pwa', filename)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 