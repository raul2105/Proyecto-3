from recipes import RecipeManager, Recipe
import os

def test_recipe_logic():
    manager = RecipeManager()
    
    # 1. Create and Save
    recipe = Recipe(name="_TEST_RECIPE_", web_width_mm=500.0, lane_count=4)
    manager.save_recipe(recipe)
    print("Save: OK")
    
    # 2. Load
    loaded = manager.load_recipe("_TEST_RECIPE_")
    assert loaded["web_width_mm"] == 500.0
    print("Load: OK")
    
    # 3. Clone
    manager.clone_recipe("_TEST_RECIPE_", "_TEST_CLONE_")
    cloned = manager.load_recipe("_TEST_CLONE_")
    assert cloned["name"] == "_TEST_CLONE_"
    assert cloned["web_width_mm"] == 500.0
    print("Clone: OK")
    
    # Cleanup
    try:
        os.remove("recipes/_TEST_RECIPE_.json")
        os.remove("recipes/_TEST_CLONE_.json")
    except:
        pass
        
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_recipe_logic()
