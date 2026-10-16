# Tuckshop ERP: Group 22 (The Final Episode)

This is the starting point for our Phase 5 build: a browser-based ERP for a small shop that might have more than one branch. It uses the stack we agreed on in Phase 1: **Django 5.2 (Python)** on the server, **MySQL 8** for the database, and **Bootstrap 5** with **jQuery** in the browser.

The hard groundwork is done. The whole Phase 3 database exists, login and roles work, and there's one working example of each kind of page we'll need. Building your module mostly means copying one of those examples and changing it to fit.

This README takes you from nothing to a running copy, then explains how the pieces fit together so you can start building. If anything in here is wrong or confusing, message on the group, and we'll fix the README rather than everyone working around it.

---

## What's already built

- **The full database from our Phase 3 ERD**: all 10 tables, with the integrity rules (CHECK, UNIQUE and foreign keys) enforced by MySQL itself, so bad data is refused even if our code has a bug
- **Login and logout**, and three roles (Owner, Administrator, Cashier), with a one-line way to protect any page
- **A home page** that lists the stock at your branch and highlights anything below its minimum
- **Add product**: a working example of a form that saves to the database
- **Product search**: a working example of jQuery fetching data without reloading the page
- **Demo data** you can load with one command so youre not working with an empty project
- **Django's admin site** at `/admin/`, for adding test data while you build
---

## Getting it running (first time only)

If MySQL is already installed, this takes about ten minutes.

### What you need installed

- **Python 3.10 or newer** from python.org. On the first screen of the installer, tick **"Add python.exe to PATH"**.
- **Git** and **VS Code**.
- **MySQL Server 8.0.16 or newer**, plus **MySQL Workbench**. You can install both from a terminal:

  ```bash
  winget install --id Oracle.MySQL --exact
  ```
  ```bash
  winget install --id Oracle.MySQLWorkbench --exact
  ```

  Then open **MySQL Configurator** from the Start menu, choose *Development Computer*, keep port 3306, and set a root password you'll remember. You'll need it in step 3.

### Step 1: Get the code


```bash
git clone https://github.com/pelotheheart/tuckshop_erp.git
```

Open the `tuckshop-erp` folder in VS Code, and open a terminal there (Terminal → New Terminal).

### Step 2: Make a virtual environment and install the packages

A virtual environment is this project's own private copy of Python and its packages, kept in a `.venv` folder. 

```bash
python -m venv .venv
```
```bash
.venv\Scripts\activate
```
```bash
pip install -r requirements.txt
```

Once it's activated, your terminal prompt starts with `(.venv)`. You need to activate it again in every new terminal.

If `activate` fails in PowerShell with *"running scripts is disabled on this system"*, either:

- run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once. It changes a Windows security setting for your user only, so it's your call.
- or type `cmd` first, and use Command Prompt instead of PowerShell.

### Step 3: Make your own `.env` file

Passwords don't go in the code. We each keep them in a private `.env` file that git ignores. Make yours from the example:

```bash
copy .env.example .env
```

Then open `.env` and fill in:

- **`DB_PASSWORD`**: your MySQL root password
- **`SEED_PASSWORD`**: any password of 8+ characters. It'll be the password for the demo logins.
- **`SECRET_KEY`**: any long random string. You can generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```

### Step 4: Create the empty database

Django creates the tables, but not the database itself. In MySQL Workbench, connect to your local server and run:

```sql
CREATE DATABASE tuckshop_dev CHARACTER SET utf8mb4;
```

### Step 5: Create the tables and load the demo data

```bash
python manage.py migrate
```
```bash
python manage.py seed
```

`migrate` builds every table from the files in each app's `migrations` folder. It also creates the three roles and a branch called "Main Branch". `seed` then adds demo logins, products, stock and a supplier.

### Step 6: Run it

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** and log in with any of these, using your `SEED_PASSWORD`:

| Username | Role | What you should see |
|---|---|---|
| `owner` | Owner | The stock list and an **Add Product** menu item. This login can also open `/admin/`. |
| `admin` | Administrator | Same as the owner, but no admin site |
| `cashier` | Cashier | The stock list only. If you type `/inventory/products/add/` into the address bar, you get "You don't have access". |

Simba Chips should show in a yellow row with a **Low stock** badge, because it has 5 in stock and a minimum of 12. If you see all of that, you're set up.

---

## Everyday commands

Activate the virtual environment first (`.venv\Scripts\activate`) in every new terminal.

| I want to... | Command |
|---|---|
| Start the site | `python manage.py runserver` (stop it with Ctrl+C) |
| Get everyone else's latest work | `git pull`, then `python manage.py migrate` |
| Save a change I made to a model | `python manage.py makemigrations <app>`, then `python manage.py migrate` |
| See the SQL a migration will run | `python manage.py sqlmigrate <app> <number>`, e.g. `sqlmigrate inventory 0003` |
| Try out database queries | `python manage.py shell` |
| Make a login for myself | `python manage.py createsuperuser` (it asks for a role ID and a branch ID: Owner is 1, Main Branch is 1) |

The server reloads by itself when you save a `.py` file. It **doesn't** reload when you change `.env`, or when you create a new `static` folder. Restart it after either of those.

---

## How it all fits together

The browser never talks to MySQL. It only talks to Django, and Django is the only thing that reads or writes the database. That's also why permission checks have to live in Django: anything in the browser can be changed by the user.

### What happens when you open the home page

1. The browser asks for `/`, sending along the login cookie it got when you logged in.
2. Django uses that cookie to work out who you are, and puts you in `request.user`.
3. Django checks the list of addresses in `config/urls.py`. `""` matches, so it calls the function `home` in `core/views.py`.
4. `@login_required` above `home` checks that you're logged in. If you aren't, it sends you to the login page instead.
5. `home` asks MySQL for the stock at your branch:
   ```python
   stock = (
       Inventory.objects.filter(branch=request.user.branch, product__is_active=True)
       .select_related("product")
       .order_by("product__product_name")
   )
   ```
   You don't write SQL yourself. Django turns that into a `SELECT ... JOIN ...` for you.
6. `render()` fills in the template `core/templates/core/home.html` with that data. `{% for row in stock %}` repeats a table row per item, and `{{ row.quantity }}` prints a value.
7. Django sends back the finished HTML. The browser never sees the template code or the SQL, only plain HTML.

Every page in the system works this way: **an address in `urls.py` -> a function in `views.py` -> (database) -> a template -> HTML.**

### The three kinds of page, and where to copy them from

| What you need | Example to copy | Files |
|---|---|---|
| A page that **shows** data | The home page | `core/views.py` (`home`), `core/templates/core/home.html` |
| A page that **saves** data from a form | Add product | `inventory/forms.py`, `inventory/views.py` (`product_add`), `inventory/templates/inventory/product_form.html` |
| Part of a page that **updates without reloading** | The search bar | `inventory/views.py` (`product_search`), `core/static/core/js/product_search.js` |

The POS system for example is a mix of the last two: search as you type, then send the sale to the server.

---

## Where everything lives

```
tuckshop-erp/
- manage.py - Runs every command: python manage.py <command>
- requirements.txt - The exact package versions we all use
- .env.example - The settings .env needs (copy it to .env)

- config/
  - settings.py - Installed apps, the MySQL connection (read from .env), login settings
  - urls.py - The main address list. Each app adds its own with include().

- core/
  - templates/core/base.html - The layout every page uses: navbar, messages, Bootstrap, jQuery
  - templates/403.html - The "You don't have access" page
  - management/commands/seed.py - python manage.py seed

- accounts/ - Users: Role, Branch, User, login/logout, permissions.py
- inventory/ - Inventory: Product, Inventory (stock per branch), Add product, search
- sales/ - Sales: Sale, SaleItem (tables only so far)
- purchasing/ - Purchasing: Supplier, PurchaseOrder, PurchaseOrderItem (tables only so far)
```

Every module app has the same layout:

| File | What goes in it |
|---|---|
| `models.py` | The tables. One class per table, one attribute per column. |
| `views.py` | One function per page. It takes the request and returns a response. |
| `urls.py` | This app's addresses. `sales` and `purchasing` don't have one yet. See Example 1 below. |
| `forms.py` | Forms that check what the user typed |
| `admin.py` | Which tables show up in the admin site |
| `templates/<app>/` | This app's HTML. The app name is repeated so two apps can both have, say, `list.html` without clashing. |
| `static/<app>/` | This app's JavaScript, CSS and images |
| `migrations/` | Files Django writes when models change. Don't edit them by hand. |

**Stay inside your own module's folder where you can**, so we're not all editing the same files. `core/` and `config/` are shared, so mention it in the group chat before changing them.

---

## Building your module

Every example below uses code that's already in the project, so open the files and follow along. When you build your own page, copy the closest example and swap in your module's names.

### Example 1: a page that shows data (the home page)

A page always has the same four pieces.

**1. An address** in a `urls.py`. The home page's is in `config/urls.py`:

```python
path("", views.home, name="home"),  # http://127.0.0.1:8000/
```

Pages that belong to a module live in that app's own `urls.py`. For example, `inventory/urls.py`:

```python
urlpatterns = [
    path("products/add/", views.product_add, name="product_add"),
    path("products/search/", views.product_search, name="product_search"),
]
```

`config/urls.py` hands every address starting with `inventory/` over to that list:

```python
path("inventory/", include("inventory.urls")),
```

That's why Add product lives at `/inventory/products/add/`. `sales` and `purchasing` don't have a `urls.py` yet. For your first page, create one shaped like `inventory/urls.py`, and add an `include(...)` line like the inventory one to `config/urls.py`.

**2. A view** that gets the data and hands it to a template. Here's `home` in `core/views.py`:

```python
@login_required
def home(request):
    now = datetime.now().strftime("%H:%M:%S")
    stock = (
        Inventory.objects.filter(branch=request.user.branch, product__is_active=True)
        .select_related("product")
        .order_by("product__product_name")
    )
    # render() fills in the template with these values and returns the finished HTML
    return render(request, "core/home.html", {"now": now, "stock": stock})
```

- `@login_required` means you must be logged in to see it. The roles section below explains the other options.
- The `Inventory.objects...` line is the database query. The double underscores follow links between tables: `product__is_active` means "this stock row's product is active".
- The dictionary at the end, `{"now": now, "stock": stock}`, is what the template gets to use.

**3. A template** in `<app>/templates/<app>/`. Here's the important part of `core/templates/core/home.html`:

```django
{% extends "core/base.html" %}

{% block title %}Home | Tuckshop ERP{% endblock %}

{% block content %}
...
  <tbody id="product-rows">
    {% for row in stock %}
    <tr class="{% if row.is_low_stock %}table-warning{% endif %}">
      <td>{{ row.product.product_name }}</td>
      <td>{{ row.product.barcode|default:"-" }}</td>
      <td>R {{ row.product.selling_price }}</td>
      ...
    </tr>
    {% empty %}
    <tr>
      <td colspan="4">No stock at your branch yet.</td>
    </tr>
    {% endfor %}
  </tbody>
...
{% endblock %}
```

- `{% extends "core/base.html" %}` gives you the navbar, Bootstrap and jQuery automatically. Your page only fills in the `title` and `content` blocks.
- `{% for %}` repeats a row for each item. `{% empty %}` is what shows when there's nothing to list.
- `{{ ... }}` prints a value, and Django escapes it automatically, so text typed by a user can never run as code.
- For styling, use Bootstrap's classes like `table`, `table-warning` and `badge`, instead of writing CSS.

**4. A menu link**, if the page needs one. These go in `core/templates/core/base.html`. Add Product is wrapped so only owners and administrators see it:

```django
{% if user.is_owner or user.is_administrator %}
  <li class="nav-item"><a class="nav-link" href="{% url 'product_add' %}">Add Product</a></li>
{% endif %}
```

Always link with `{% url 'name' %}`, using the `name=` from `urls.py`, rather than typing the address. If an address ever changes, every link keeps working.

### Example 2: a form that saves (Add product)

**The form**, in `inventory/forms.py`:

```python
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["product_name", "barcode", "cost_price", "selling_price", "minimum_stock"]

    def __init__(self, *args, **kwargs):
        # Let Django build the form as normal first
        super().__init__(*args, **kwargs)
        # then give every input Bootstrap's "form-control" class so it gets styled.
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
```

A `ModelForm` builds one input per field from the model. It also checks everything the model already knows: required fields, lengths, number formats, unique barcodes, and the "price must be more than R0.00" rule in `inventory/models.py`. The `__init__` part only adds Bootstrap styling. Copy it as it is.

**The view**, `product_add` in `inventory/views.py`. Every form view has this shape:

```python
@role_required(OWNER, ADMIN)
def product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
                Inventory.objects.create(branch=request.user.branch, product=product, quantity=0)
            messages.success(request, f"{product.product_name} was added.")
            return redirect("home")
    else:
        form = ProductForm()
    return render(request, "inventory/product_form.html", {"form": form})
```

The same address does two jobs:

| What happened | Which path runs | What the user sees |
|---|---|---|
| They opened the page (GET) | `else:` makes an empty form | The blank form |
| They clicked Save, and something's wrong | `is_valid()` is false, so it falls through to the last line | The form again, with what they typed and a red message under each problem |
| They clicked Save, and it's all fine | `form.save()`, then `redirect("home")` | The home page, with a green "Sprite 330ml was added." |

The redirect after saving matters. If we showed a page straight away instead, pressing F5 would send the form again and add the product twice.

**The template**, `inventory/templates/inventory/product_form.html`:

```django
<form method="post">
    {% csrf_token %}
      {% for field in form %}
      <div class="mb-3">
        <label class="form-label" for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {% for error in field.errors %}
        <div class="text-danger small mt-1">{{ error }}</div>
        {% endfor %}
      </div>
      {% endfor %}
    ...
</form>
```

**Every POST form needs `{% csrf_token %}`**, or Django refuses it with a 403. It's a hidden code that proves the form came from our own site. The `{% for field in form %}` loop draws each input with its label and error messages, so you can reuse this template for any form.

**To make your own form:** copy `ProductForm` into your app's `forms.py` with your model and fields, then copy `product_add` and `product_form.html` and change the names. If your form only saves one table, you don't need the `with transaction.atomic():` part. A plain `form.save()` is enough.

**Rules that involve more than one field.** Some tables have a rule about two fields together. For example, the `Supplier` table in `purchasing/models.py` needs a phone number *or* an email. A message like that belongs to the whole form, not one box, so the field loop above won't show it. The form would quietly refuse to save, and the user wouldn't know why. For a model like that, add this just under `{% csrf_token %}`:

```django
{% if form.non_field_errors %}
<div class="alert alert-danger">
  {% for error in form.non_field_errors %}<div>{{ error }}</div>{% endfor %}
</div>
{% endif %}
```

**Editing an existing record** works the same way, except you pass the record in. For example, `ProductForm(request.POST, instance=product)`. Then `save()` updates that row instead of adding a new one.

### Example 3: updating part of a page with jQuery (the search box)

Type in the search box on the home page and the table changes without the page reloading. Three pieces make that work.

**1. A view that returns data instead of a page.** Here's `product_search` in `inventory/views.py`:

```python
@login_required
def product_search(request):
    q = request.GET.get("q", "")
    rows = (
        Inventory.objects.filter(
            branch=request.user.branch,
            product__is_active=True,
            product__product_name__icontains=q,
        )
        .select_related("product")
        .order_by("product__product_name")
    )
    results = []
    for row in rows:
        results.append({
            "name": row.product.product_name,
            "barcode": row.product.barcode,
            # We send the price as text so it stays exactly "18.50".
            "price": str(row.product.selling_price),
            "stock": row.quantity,
            "low_stock": row.is_low_stock,
        })
    return JsonResponse({"results": results})
```

`request.GET.get("q", "")` reads the `?q=...` part of the address. `JsonResponse` sends back plain data instead of HTML. Open http://127.0.0.1:8000/inventory/products/search/?q=co while you're logged in to see exactly what it returns.

**2. The template tells the JavaScript where to ask.** From `core/templates/core/home.html`:

```django
<input type="search" id="search" class="form-control mb-3" placeholder="Search products..." data-url="{% url 'product_search' %}">
...
<tbody id="product-rows">
...
{% block scripts %}
<script src="{% static 'core/js/product_search.js' %}"></script>
{% endblock %}
```

Django writes the real address into `data-url`, so it's never typed into the JavaScript file. JavaScript files are sent to the browser as they are, so `{% url %}` wouldn't work inside them. `{% block scripts %}` loads the file after jQuery, and the template needs `{% load static %}` at the top to use `{% static %}`.

**3. The JavaScript**, `core/static/core/js/product_search.js`:

```js
$search.on("input", function () {
    $.getJSON($search.data("url"), { q: $search.val() }, function (data) {
        $rows.empty();
        $.each(data.results, function (index, product) {
            const $tr = $("<tr>");
            $tr.append($("<td>").text(product.name));
            ...
            $rows.append($tr);
        });
    });
});
```

Every time the box changes, `$.getJSON` asks the view for `?q=<what was typed>`. When the answer arrives, jQuery passes it in as `data`, and we redraw the rows. The names line up with the Python: `q` is the same `q` the view reads, and `product.name` is the `"name"` the view put in each result.

Two things to watch when you build your own:

- **Use `.text(...)` for anything that came from the database**, like `.text(product.name)` above, never `.html(...)` or string-building. Otherwise a product called `<script>...</script>` would run on every cashier's screen.
- **Sending data back (an AJAX POST)**, which the POS checkout will need, requires the CSRF token too. Nothing in the project does this yet, so put this in your template's `scripts` block, before your own JS file:
  ```django
  <script>
    // Django refuses POSTs without this token. This sends it with every jQuery request.
    $.ajaxSetup({ headers: { "X-CSRFToken": "{{ csrf_token }}" } });
  </script>
  ```

### Changing the database

Never change tables in Workbench by hand. Change the model, and let Django write the change:

1. Edit the model in your app's `models.py`.
2. Run `python manage.py makemigrations <your app> --name <short description>`. Django writes a new numbered file in `migrations/` describing the change.
3. Optionally, run `python manage.py sqlmigrate <your app> <number>` to see the SQL it'll run.
4. Run `python manage.py migrate` to apply it to your database.
5. **Commit the migration file together with the model change.** When teammates pull and run `migrate`, their tables change to match, and their data is kept.

**What the existing migrations look like.** `inventory/migrations/` shows the history of the inventory tables:

| File | What it did |
|---|---|
| `0001_initial.py` | Created the `product` table |
| `0002_price_rules.py` | Added the "more than R0.00" price checks. These are Python-only rules, so `sqlmigrate inventory 0002` shows `(no-op)`: no SQL at all. |
| `0003_stock.py` | Created the `inventory` table, plus the CHECK and UNIQUE rules MySQL enforces. Run `python manage.py sqlmigrate inventory 0003` to see them. |

`accounts/migrations/0003_add_roles.py` and `0006_add_main_branch.py` are **data migrations**. They don't change tables. They insert the three roles and Main Branch, so every database has them. Copy those if your module ever needs rows that must always exist.

Some things to know:

- **Never edit or delete a migration file that's already been shared.** If you need to change something again, make a new migration.
- If you add a required column to a table that already has rows, `makemigrations` asks what to put in the existing rows. Answer `1`, then give a sensible value. That's how existing users got their role and branch in `accounts/0004_user_role.py` and `0007_user_branch.py`.

### Saving to more than one table at once

If one action writes to several tables, wrap it in a **transaction**. Either everything is saved, or nothing is. `product_add` (Example 2) does this, because a new product also needs a stock row:

```python
with transaction.atomic():
    product = form.save()
    Inventory.objects.create(branch=request.user.branch, product=product, quantity=0)
```

If the second line fails, MySQL undoes the first one too, so we never end up with a product that has no stock row. **The sales checkout and purchase-order fulfilment must work like this.** A sale, its items and the stock reductions are saved together or not at all. When you build checkout, also read the stock rows with `select_for_update()` inside the transaction. That locks them, so two tills can't sell the last bag of chips at the same moment.

---

## Roles: who can do what

Every user has a **role** and a **branch**. In views, use `request.user.role` and `request.user.branch`. In templates, use `user.role` and `user.branch`.

**Protecting a page** is one line above the view:

| Who's allowed | Put this above the view |
|---|---|
| Anyone who's logged in | `@login_required` |
| Only certain roles | `@role_required(OWNER, ADMIN)` |

Anyone else gets the "You don't have access" page. **Every view needs one of these**, because hiding a menu link only stops people *seeing* it. Anyone can still type the address.

**Checking a role in code:** `request.user.has_role(OWNER, ADMIN)`. In templates, use `user.is_owner`, `user.is_administrator` and `user.is_cashier`. Always use the constants `OWNER`, `ADMIN` and `CASHIER` from `accounts.models`, never the words typed out. A typo in a constant fails loudly, but a typo in a word fails silently.

This is the access we agreed on in our Phase 2 SRS:

| | Owner | Administrator | Cashier |
|---|:-:|:-:|:-:|
| Make sales (POS) | yes | yes | yes |
| View or change past sales | yes | yes | no |
| View stock | yes | yes | yes |
| Add, edit and deactivate products | yes | yes | no |
| Suppliers and purchase orders | yes | yes | no |
| Manage users | yes (admins and cashiers) | yes (cashiers only) | no |
| Reports | yes | no (still to confirm) | no |

---

## The database

| Table | App | What it holds |
|---|---|---|
| `role` | accounts | Owner, Administrator, Cashier (created by a migration) |
| `branch` | accounts | The shop's locations ("Main Branch" is created by a migration) |
| `user` | accounts | Everyone who logs in, with their role and branch |
| `product` | inventory | What the shop sells: name, barcode, cost and selling price, minimum stock |
| `inventory` | inventory | How many of each product each branch has (one row per product per branch) |
| `sale` | sales | One completed sale: branch, cashier, date and total |
| `sale_item` | sales | One line of a sale: product, quantity, and the price at the time |
| `supplier` | purchasing | Companies we buy from |
| `purchase_order` | purchasing | An order to a supplier, with a status of Pending, Fulfilled or Cancelled |
| `purchase_order_item` | purchasing | One line of an order: product, quantity, agreed cost |

**Rules MySQL enforces itself:**
- Prices, quantities and costs must be above zero, and stock and minimum stock can't be negative.
- Suppliers need a phone number or an email.
- Order status must be one of the three allowed values.
- Barcodes and usernames are unique, and there's only one stock row per product per branch.
- Every foreign key is `PROTECT`: you can't delete something other records point to, such as a product that's been sold.

That last rule backs up our Phase 3 decision to **deactivate, not delete**.

**Business rules our code still has to follow** (Phase 3, section 3.4.4):

1. Stock can never go negative. If any line of a sale is short, reject the whole sale.
2. The sale total is worked out by the code from its items, never typed in.
3. Each sale line keeps a copy of the selling price at the time of the sale.
4. Stock only goes up when a purchase order changes from Pending to Fulfilled, and only once.
5. Records with history are deactivated, not deleted.
6. Permissions are checked on the server, in the views.

**The admin site** (`/admin/`, log in as `owner`) is handy for adding test data while you build, such as purchase orders before the purchase-order page exists. But it's a developer tool, not part of our system, and **it skips our business rules**. A sale added there doesn't reduce stock.

---

## How we write code

1. **Every view gets `@login_required` or `@role_required(...)`.**
2. **Never type an address by hand.** Use `{% url 'name' %}` in templates and `redirect("name")` in views.
3. **Use the role constants** `OWNER`, `ADMIN` and `CASHIER`.
4. **Deactivate, don't delete.** Set `is_active = False` on anything with history.
5. **Wrap anything that writes to more than one table in `transaction.atomic()`.**
6. **Check input on the server** with Django forms. MySQL's rules are the last line of defence, not the first.
7. **Changed a model? Commit the migration file with it.**
8. **Use `select_related(...)`** when a page shows details from a linked table, like `row.product.product_name`. Otherwise Django sends one extra query per row.
9. **Put a comma after every item in a list**, including the last one. Python quietly joins two strings that have no comma between them, which leads to some very confusing errors.
10. **Comment the way you'd explain it to a teammate**: full, plain sentences about *why*, not just *what*.

---

## Working together with git

A good routine for each session:

```bash
git pull
```
```bash
python manage.py migrate
```

Then do your work, and when it's working:

```bash
git add -A
```
```bash
git commit -m "message about your commit"
```
```bash
git pull
```
```bash
git push
```

Pull before you push, so you pick up everyone else's changes first, and fix any conflicts on your side. Commit small and often, with messages that say what changed. `.env` and `.venv` are already excluded by `.gitignore`, so passwords never end up on GitHub.

---

## What's left to build

| Module | Still to do |
|---|---|
| Users | Add, edit and deactivate users. Owners manage admins and cashiers; admins manage cashiers only. |
| Inventory | Edit and deactivate products, and stock adjustments |
| Sales | The POS cart (jQuery), checkout in one transaction (check stock, save the sale and its items, reduce stock), receipts, sales history |
| Purchasing | Supplier pages, purchase orders with item lines, fulfil (stock goes up, once) and cancel |
| Reports | Sales by period and product, inventory valuation at cost, best and slow sellers, PDF/Excel export |

---

## When something goes wrong

When Python shows an error, **read it from the bottom up**. The last line says what went wrong, and the lines just above it show which of *our* files and line numbers it came from. You can skip the lines from inside `.venv`.

| You see | It usually means |
|---|---|
| `No module named 'django'` | The virtual environment isn't activated. Run `.venv\Scripts\activate`. |
| `Access denied for user 'root'` | Wrong `DB_PASSWORD` in `.env`. Restart the server after fixing it. |
| `Unknown database 'tuckshop_dev'` | Step 4 hasn't been done yet |
| `Table ... doesn't exist`, or *"You have unapplied migrations"* | Run `python manage.py migrate` |
| `No installed app with label ...` | The app isn't listed in `INSTALLED_APPS` in `config/settings.py` |
| `NameError: name '...' is not defined` | You're missing an `import` at the top of that file |
| `NoReverseMatch` | A `{% url %}` or `redirect()` name that doesn't exist. Check the `name=` in `urls.py`. |
| `TemplateDoesNotExist` | The file must be at `<app>/templates/<app>/<name>.html` |
| Template code showing on the page as text | A tag is broken. Check every `{%` has a `%}`, and every `{{` has a `}}`. |
| `didn't return an HttpResponse object` | One path through your view doesn't reach a `return`. Usually it's indentation. |
| `403 CSRF verification failed` | A POST form without `{% csrf_token %}`, or an AJAX POST without the token header |
| Your JS or CSS change doesn't show up | The browser kept an old copy. Press Ctrl+F5, or tick "Disable cache" in DevTools → Network. |
| A 404 for your new `.js` file | You made a new `static` folder while the server was running. Restart it. |
| `That port is already in use` | Another `runserver` is still running in a different terminal |

