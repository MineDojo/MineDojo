import numpy as np

from ...sim.mc_meta import mc as MC


__all__ = ["get_recipes_matrix", "get_inventory_vector"]


def get_recipes_matrix():
    recipes = []
    for item in MC.ALL_CRAFT_SMELT_ITEMS:
        ingredients = (
            MC.CRAFTING_RECIPES_BY_OUTPUT[item]
            if item
            in MC.ALL_HAND_CRAFT_ITEMS_NN_ACTIONS
            + MC.ALL_TABLE_CRAFT_ONLY_ITEMS_NN_ACTIONS
            else MC.SMELTING_RECIPES_BY_OUTPUT[item]
        )
        # take the first recipe if multiple recipes
        ingredients = ingredients[0]["ingredients"]
        recipe_vector = np.zeros(len(MC.ALL_ITEMS))
        for k, v in ingredients.items():
            recipe_vector[MC.ALL_ITEMS.index(k)] += v
        recipes.append(recipe_vector)
    recipes = np.stack(recipes, axis=0)
    assert recipes.shape == (
        len(MC.ALL_CRAFT_SMELT_ITEMS),
        len(MC.ALL_ITEMS),
    ), "Internal"
    return recipes


def get_inventory_vector(inventory):
    vec = np.zeros(len(MC.ALL_ITEMS))
    items, quantities = inventory["name"], inventory["quantity"]
    for item, quantity in zip(items, quantities):
        if " " in item:
            item = item.replace(" ", "_")
        vec[MC.ALL_ITEMS.index(item)] += quantity
    return vec[np.newaxis, ...]
