

class EditorCategories:
    Categories = []

    @classmethod
    def register(self, cat):
        self.Categories.append(cat)



# Terrain
class EditorCategoryTerrain:
    name = "Terrain"

EditorCategories.register(EditorCategoryTerrain)

# Vegetation
class EditorCategoryVegetation:
    name = "Vegetation"

EditorCategories.register(EditorCategoryVegetation)

# Objects
class EditorCategoryObjects:
    name = "Objects"

EditorCategories.register(EditorCategoryObjects)
