import bpy


class DataUtilities(object):
    """
        Utilities for handling data blocks
        Reference: https://docs.blender.org/manual/en/latest/files/data_blocks.html
    """

    @staticmethod
    def purgeMeshObjectsFromCollection(collection_name, remove_meshes=True, remove_materials=True, remove_images=True):
        """
        Removes no longer needed data from the blender file
        :param collection_name: Name of the collection to purge
        :param remove_meshes: Enable removing Meshes
        :param remove_materials: Enable removing materials
        :param remove_images: Enable removing images
        """

        # Get the collection from its name
        objects = bpy.data.collections[collection_name].objects

        # Will collect meshes from delete objects
        meshes = set()

        # Get objects in the collection if they are meshes store the mesh to delete later and then delete the object
        for obj in objects:
            if obj.type == "MESH":
                meshes.add(obj.data)
            bpy.data.objects.remove(obj)

        if remove_meshes:
            # Look at meshes that are orphan after objects removal
            for mesh in [m for m in meshes if m.users == 0]:
                # Delete the meshes
                bpy.data.meshes.remove(mesh)

        if remove_materials:
            # Look at materials that are orphans since meshes have been deleted
            for material in [mat for mat in bpy.data.materials if mat.users == 0]:
                bpy.data.materials.remove(material)

        if remove_images:
            # Look at materials that are orphans since materials have been deleted
            for image in [i for i in bpy.data.images if i.users == 0]:
                bpy.data.images.remove(image)
