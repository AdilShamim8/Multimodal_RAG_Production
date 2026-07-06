"""Generate a 200-recipe sample dataset (deterministic).

The sample dataset is shipped with the project so that `multimodal-rag ingest
--source sample` works offline. Each recipe has: id, title, text (markdown),
image_url (picsum.photos placeholder), and metadata.

The recipes are realistic but synthetic — built from a curated list of dishes,
cooking techniques, and ingredient combos. No external API calls are needed.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "sample_recipes.json"
random.seed(42)

DISHES = [
    ("Tomato Basil Pasta", "italian", "pasta"), ("Chicken Tikka Masala", "indian", "curry"),
    ("Beef Tacos", "mexican", "tex-mex"), ("Caesar Salad", "american", "salad"),
    ("Margherita Pizza", "italian", "pizza"), ("Sushi Roll Combo", "japanese", "sushi"),
    ("Pad Thai", "thai", "noodles"), ("Pho Bo", "vietnamese", "soup"),
    ("Moussaka", "greek", "casserole"), ("Banana Bread", "american", "bread"),
    ("Chocolate Cake", "french", "dessert"), ("Apple Pie", "american", "dessert"),
    ("Greek Salad", "greek", "salad"), ("Beef Wellington", "british", "pastry"),
    ("Sushi Platter", "japanese", "sushi"), ("Laksa", "malaysian", "soup"),
    ("Risotto ai Funghi", "italian", "rice"), ("Paella Valenciana", "spanish", "rice"),
    ("Chicken Katsu", "japanese", "fried"), ("Tiramisu", "italian", "dessert"),
    ("Hummus", "middle-eastern", "dip"), ("Falafel Wrap", "middle-eastern", "wrap"),
    ("Beef Bourguignon", "french", "stew"), ("Croque Monsieur", "french", "sandwich"),
    (" Eggs Benedict", "american", "breakfast"), ("Pancakes", "american", "breakfast"),
    ("Waffles", "belgian", "breakfast"), ("Croissant", "french", "pastry"),
    ("Bagel and Lox", "jewish", "breakfast"), ("Shakshuka", "middle-eastern", "breakfast"),
    ("Ramen Tonkotsu", "japanese", "soup"), ("Udon Stir Fry", "japanese", "noodles"),
    ("Kimchi Jjigae", "korean", "stew"), ("Bibimbap", "korean", "rice"),
    ("Bulgogi", "korean", "beef"), ("Japchae", "korean", "noodles"),
    ("Butter Chicken", "indian", "curry"), ("Biryani", "indian", "rice"),
    ("Dosa", "indian", "crepe"), ("Samosa", "indian", "snack"),
    ("Tandoori Chicken", "indian", "grill"), ("Naan", "indian", "bread"),
    ("Paneer Tikka", "indian", "vegetarian"), ("Aloo Gobi", "indian", "vegetarian"),
    ("Chana Masala", "indian", "vegetarian"), ("Palak Paneer", "indian", "vegetarian"),
    ("Steak Frites", "french", "beef"), ("Coq au Vin", "french", "stew"),
    ("Bouillabaisse", "french", "soup"), ("Quiche Lorraine", "french", "pie"),
    ("French Onion Soup", "french", "soup"), ("Cassoulet", "french", "stew"),
    ("Fish and Chips", "british", "fried"), ("Shepherd's Pie", "british", "pie"),
    ("Bangers and Mash", "british", "sausage"), ("Yorkshire Pudding", "british", "side"),
    ("Full English Breakfast", "british", "breakfast"), ("Scones with Cream", "british", "snack"),
    ("Hamburger", "american", "sandwich"), ("Cheeseburger", "american", "sandwich"),
    ("Hot Dog", "american", "sandwich"), ("BBQ Ribs", "american", "pork"),
    ("Mac and Cheese", "american", "pasta"), ("Clam Chowder", "american", "soup"),
    ("Lobster Roll", "american", "sandwich"), ("Buffalo Wings", "american", "chicken"),
    ("Cobb Salad", "american", "salad"), ("Meatloaf", "american", "beef"),
    ("Chili Con Carne", "tex-mex", "stew"), ("Quesadilla", "mexican", "tex-mex"),
    ("Burrito", "mexican", "wrap"), ("Enchiladas", "mexican", "tex-mex"),
    ("Guacamole", "mexican", "dip"), ("Salsa Verde", "mexican", "sauce"),
    ("Pico de Gallo", "mexican", "salsa"), ("Churros", "mexican", "dessert"),
    ("Tres Leches Cake", "mexican", "dessert"), ("Mole Poblano", "mexican", "sauce"),
    ("Carbonara", "italian", "pasta"), ("Bolognese", "italian", "pasta"),
    ("Pesto Genovese", "italian", "pasta"), ("Lasagna", "italian", "pasta"),
    ("Fettuccine Alfredo", "italian", "pasta"), ("Ravioli", "italian", "pasta"),
    ("Gnocchi", "italian", "pasta"), ("Bruschetta", "italian", "snack"),
    ("Caprese Salad", "italian", "salad"), ("Minestrone", "italian", "soup"),
    ("Osso Buco", "italian", "veal"), ("Cannoli", "italian", "dessert"),
    ("Gelato", "italian", "dessert"), ("Panna Cotta", "italian", "dessert"),
    ("Spaghetti Aglio e Olio", "italian", "pasta"), ("Tagliatelle al Tartufo", "italian", "pasta"),
    ("Vongole", "italian", "pasta"), ("Puttanesca", "italian", "pasta"),
    ("Cacio e Pepe", "italian", "pasta"), ("Arrabbiata", "italian", "pasta"),
    ("Pizza Diavola", "italian", "pizza"), ("Pizza Quattro Formaggi", "italian", "pizza"),
    ("Pizza Capricciosa", "italian", "pizza"), ("Calzone", "italian", "pizza"),
    ("Focaccia", "italian", "bread"), ("Ciabatta", "italian", "bread"),
    ("Beef Noodle Soup", "chinese", "soup"), ("Kung Pao Chicken", "chinese", "stir-fry"),
    ("Mapo Tofu", "chinese", "tofu"), ("Peking Duck", "chinese", "duck"),
    ("Char Siu", "chinese", "pork"), ("Xiao Long Bao", "chinese", "dumpling"),
    ("Dan Dan Noodles", "chinese", "noodles"), ("Chow Mein", "chinese", "noodles"),
    ("Fried Rice", "chinese", "rice"), ("Spring Rolls", "chinese", "snack"),
    ("Hot and Sour Soup", "chinese", "soup"), ("Wonton Soup", "chinese", "soup"),
    ("Salt and Pepper Shrimp", "chinese", "shrimp"), ("General Tso's Chicken", "chinese", "chicken"),
    ("Tom Yum Goong", "thai", "soup"), ("Green Curry", "thai", "curry"),
    ("Red Curry", "thai", "curry"), ("Massaman Curry", "thai", "curry"),
    ("Som Tum", "thai", "salad"), ("Tom Kha Gai", "thai", "soup"),
    ("Mango Sticky Rice", "thai", "dessert"), ("Thai Iced Tea", "thai", "drink"),
    ("Phat Si Ew", "thai", "noodles"), ("Khao Soi", "thai", "noodles"),
    ("Banh Mi", "vietnamese", "sandwich"), ("Goi Cuon", "vietnamese", "spring-roll"),
    ("Bun Cha", "vietnamese", "noodles"), ("Ca Kho To", "vietnamese", "fish"),
    ("Vietnamese Coffee", "vietnamese", "drink"), ("Che Chuoi", "vietnamese", "dessert"),
    ("Beef Pho", "vietnamese", "soup"), ("Chicken Pho", "vietnamese", "soup"),
    ("Vegetable Pho", "vietnamese", "soup"), ("Hu Tieu", "vietnamese", "soup"),
    ("Margherita Flatbread", "italian", "pizza"), ("Capricciosa Pizza", "italian", "pizza"),
    ("Mushroom Risotto", "italian", "rice"), ("Seafood Risotto", "italian", "rice"),
    ("Saffron Risotto", "italian", "rice"), ("Truffle Risotto", "italian", "rice"),
    ("Veal Milanese", "italian", "veal"), ("Chicken Milanese", "italian", "chicken"),
    ("Saltimbocca", "italian", "veal"), ("Piccata", "italian", "chicken"),
    ("Marsala", "italian", "chicken"), ("Scampi", "italian", "shrimp"),
    ("Fra Diavolo", "italian", "seafood"), ("Cioppino", "italian", "stew"),
    ("Bacalhau", "portuguese", "fish"), ("Pastel de Nata", "portuguese", "dessert"),
    ("Francesinha", "portuguese", "sandwich"), ("Caldo Verde", "portuguese", "soup"),
    ("Feijoada", "brazilian", "stew"), ("Pao de Queijo", "brazilian", "bread"),
    ("Brigadeiro", "brazilian", "dessert"), ("Moqueca", "brazilian", "stew"),
    ("Ceviche", "peruvian", "fish"), ("Lomo Saltado", "peruvian", "stir-fry"),
    ("Aji de Gallina", "peruvian", "chicken"), ("Anticuchos", "peruvian", "skewer"),
    ("Empanadas", "argentinian", "pastry"), ("Asado", "argentinian", "grill"),
    ("Chimichurri", "argentinian", "sauce"), ("Alfajores", "argentinian", "dessert"),
    ("Dum Biryani", "indian", "rice"), ("Hyderabadi Biryani", "indian", "rice"),
    ("Lucknowi Biryani", "indian", "rice"), ("Kolkata Biryani", "indian", "rice"),
    ("Mughlai Chicken", "indian", "curry"), ("Rogan Josh", "indian", "curry"),
    ("Dhansak", "indian", "stew"), ("Vindaloo", "indian", "curry"),
    ("Korma", "indian", "curry"), ("Saag", "indian", "vegetarian"),
    ("Matar Paneer", "indian", "vegetarian"), ("Kadai Paneer", "indian", "vegetarian"),
    ("Baingan Bharta", "indian", "vegetarian"), ("Bhindi Masala", "indian", "vegetarian"),
    ("Stuffed Paratha", "indian", "bread"), ("Puri", "indian", "bread"),
    ("Bhatura", "indian", "bread"), ("Roti", "indian", "bread"),
    ("Chapati", "indian", "bread"), ("Pav Bhaji", "indian", "snack"),
    ("Vada Pav", "indian", "snack"), ("Pani Puri", "indian", "snack"),
    ("Dahi Puri", "indian", "snack"), ("Bhel Puri", "indian", "snack"),
    ("Idli", "indian", "breakfast"), ("Vada", "indian", "breakfast"),
    ("Upma", "indian", "breakfast"), ("Pongal", "indian", "breakfast"),
    ("Uttapam", "indian", "breakfast"), ("Lemon Rice", "indian", "rice"),
    ("Curd Rice", "indian", "rice"), ("Tomato Rice", "indian", "rice"),
    ("Coconut Rice", "indian", "rice"), ("Bisi Bele Bath", "indian", "rice"),
    ("Gulab Jamun", "indian", "dessert"), ("Rasgulla", "indian", "dessert"),
    ("Kheer", "indian", "dessert"), ("Payasam", "indian", "dessert"),
    ("Jalebi", "indian", "dessert"), ("Barfi", "indian", "dessert"),
    ("Carrot Halwa", "indian", "dessert"), ("Soan Papdi", "indian", "dessert"),
]


INGREDIENT_POOL = [
    "tomato", "garlic", "onion", "basil", "parmesan", "olive oil", "mozzarella",
    "chicken", "beef", "pork", "lamb", "fish", "shrimp", "egg", "tofu", "paneer",
    "rice", "pasta", "noodles", "bread", "tortilla", "rice noodles", "couscous",
    "chili", "cumin", "turmeric", "coriander", "ginger", "lemon", "lime", "mint",
    "cilantro", "parsley", "thyme", "rosemary", "oregano", "soy sauce", "fish sauce",
    "coconut milk", "yogurt", "cream", "butter", "cheese", "feta", "goat cheese",
    "mushroom", "spinach", "kale", "carrot", "potato", "sweet potato", "eggplant",
    "zucchini", "bell pepper", "broccoli", "cauliflower", "cabbage", "lettuce",
    "avocado", "corn", "peas", "beans", "lentils", "chickpeas", "walnut", "almond",
    "pistachio", "raisin", "cranberry", "apple", "banana", "mango", "pineapple",
    "chocolate", "vanilla", "cinnamon", "nutmeg", "cardamom", "saffron", "paprika",
    "worcestershire sauce", "mustard", "ketchup", "mayonnaise", "vinegar", "honey",
    "sugar", "flour", "butter", "yeast", "baking powder", "baking soda", "salt",
]


def make_recipe(idx: int, dish: tuple[str, str, str]) -> dict:
    name, cuisine, category = dish
    name = name.strip()
    n_ing = random.randint(5, 12)
    ingredients = random.sample(INGREDIENT_POOL, n_ing)
    if name.lower().startswith(("tomato", "banana")) and name.split()[0].lower() not in [i.split()[0] for i in ingredients]:
        # Ensure the title ingredient appears
        ingredients.insert(0, name.split()[0].lower())
    ingredients = list(dict.fromkeys(ingredients))  # dedupe, preserve order

    steps = [
        f"Prepare the {ingredients[0]} by washing and chopping as needed.",
        f"Heat olive oil in a large pan over medium heat.",
        f"Add {ingredients[1] if len(ingredients) > 1 else 'onion'} and sauté until translucent, about 4-5 minutes.",
        f"Stir in {', '.join(ingredients[2:5])} and cook for another 3 minutes.",
        f"Add the remaining ingredients: {', '.join(ingredients[5:])}.",
        f"Season with salt, pepper, and herbs to taste.",
        f"Cook for 15-20 minutes until everything is tender and flavors meld.",
        f"Serve hot, garnished with fresh herbs. Serves 4.",
    ]

    text = (
        f"# {name}\n\n"
        f"**Cuisine:** {cuisine.title()}  \n"
        f"**Category:** {category.title()}  \n"
        f"**Prep time:** {random.randint(10, 30)} min  \n"
        f"**Cook time:** {random.randint(15, 60)} min  \n"
        f"**Servings:** {random.randint(2, 8)}\n\n"
        f"## Ingredients\n\n"
        + "\n".join(f"- {i}" for i in ingredients)
        + "\n\n## Instructions\n\n"
        + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        + f"\n\n## Notes\n\nThis {cuisine} {category} is a great choice for "
        f"{'weeknight dinners' if random.random() > 0.5 else 'special occasions'}. "
        f"Pairs well with a glass of {'red wine' if cuisine in ('italian','french','spanish') else 'sparkling water'}."
    )

    return {
        "id": f"recipe-{idx:04d}",
        "title": name,
        "text": text,
        "image_url": f"https://picsum.photos/seed/{name.lower().replace(' ', '-')}/512/512",
        "metadata": {
            "cuisine": cuisine,
            "category": category,
            "ingredients": ingredients,
            "servings": random.randint(2, 8),
            "difficulty": random.choice(["easy", "medium", "hard"]),
        },
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # We need at least 200 recipes; if the curated list is shorter, cycle.
    recipes = []
    idx = 0
    while len(recipes) < 200:
        for dish in DISHES:
            if len(recipes) >= 200:
                break
            recipes.append(make_recipe(idx, dish))
            idx += 1
    with OUT.open("w") as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(recipes)} recipes to {OUT}")


if __name__ == "__main__":
    main()
