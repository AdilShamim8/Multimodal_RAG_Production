# Example prompts for the Multimodal RAG system

Below are example text queries you can send via the CLI or API. Each is
designed to exercise a different retrieval mode (ingredient, cuisine,
technique, dish name).

## Ingredient-based

- `tomato basil pasta`
- `recipes with garlic and parmesan`
- `coconut milk curry`
- `chicken and rice`
- `dark chocolate dessert`

## Cuisine-based

- `italian pasta dish`
- `thai noodle soup`
- `indian vegetarian curry`
- `japanese fried chicken`
- `mexican tortilla wrap`

## Technique-based

- `slow cooked stew`
- `grilled meat`
- `fried snack`
- `baked dessert`
- `steamed dumpling`

## Dish-name

- `margherita pizza`
- `pad thai`
- `pho bo`
- `tiramisu`
- `butter chicken`
- `banana sour cream bread`
- `moussaka`
- `cup of tea`

## Image-based

Send any food photo via the API:

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d "{\"query_image\": \"$(base64 -w0 my_food_photo.jpg | sed 's/^/data:image\\/jpeg;base64,/')\", \"top_k\": 5}"
```

## Full RAG query

```bash
multimodal-rag query --text "tomato basil pasta" --top-k 5
```

Expected output:

```
Retrieved
  1. Tomato Basil Pasta  (score=0.81)
  2. Margherita Pizza    (score=0.74)
  3. Caprese Salad       (score=0.71)
Reranked
  1. Tomato Basil Pasta  (score=0.92)
  2. Margherita Pizza    (score=0.85)
  3. Caprese Salad       (score=0.79)
Summary
Top pick: Tomato Basil Pasta. A classic Italian pasta combining fresh tomatoes,
basil, and parmesan. Cooks in under 30 minutes and serves 4-6.
```
