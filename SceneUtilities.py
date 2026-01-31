import bpy
import mathutils
from math import radians

class SceneUtilities(object):
    """
        Utilities for managing scene and objects within the scene
    """

    @staticmethod
    def createCamera(name="Camera", collection=None, location=(0,0,0), rotation=(0,0,0), create_if_camera_exists=False, set_as_active=True):
        """
        Method to create a camera in the provided collection
        :param collection:
        :return:
        """
        # If a specific collection is provided
        if collection:
            camCollection = [x for x in bpy.data.collections if collection == x.name]
            # Create that collection if it does not exist
            if not camCollection:
                # Create collection
                camCollection = bpy.data.collections.new(collection)
                # Link it to the active scene
                bpy.context.scene.collection.children.link(camCollection)
            else:
                camCollection = camCollection[0]
        # Use active collection if none provided
        else:
            camCollection = bpy.context.view_layer.active_layer_collection.collection
            print(f"Use current active collection [{camCollection.name}]")

        # Get existing objects in collection
        objects = camCollection.objects

        # Check for existing cameras
        if not create_if_camera_exists:
            print('check existing')
            for obj in objects:
                print(obj.name)
                print(obj.type)
                if obj.type == "CAMERA":
                    print(f"WARNING:: Camera [{obj.name}] already exists in collection [{camCollection.name}]")
                    return

        # Create Camera
        camera = bpy.data.cameras.new(name)
        # Create Object parent
        camera = bpy.data.objects.new(name, camera)

        # Position camera
        camera.location = location
        camera.rotation_euler = [radians(x) for x in rotation]

        # bpy.context.scene.collection.objects.link(cam) # scene.collection is the ROOT 'Scene Collection' collection

        # Move camera to collection
        if camCollection:
            camCollection.objects.link(camera)

        if set_as_active:
            bpy.context.scene.camera = camera

        return camera

    @staticmethod
    def moveCameraToViewSelected(objects, camera_name, camera_backwards_offset=0):
        """
            Selects all meshes in the Assets collection and moves the camera to fit all objects inside view
            :param objects List of objects to center camera view on
            :param camera_name: Name of the camera to move
            :param camera_backwards_offset: The amount in world units on how far back the camera moves
        """

        for o in objects:
            o.select_set(True)

        bpy.ops.view3d.camera_to_view_selected()

        # move camera in local z axis
        camera = bpy.context.scene.objects[camera_name]
        vec = mathutils.Vector((0.0, 0.0, float(camera_backwards_offset)))
        inv = camera.matrix_world.copy()
        inv.invert()
        camera.location = camera.location + vec @ inv

    @staticmethod
    def selectChildren(parent, recursive=True, select_parent=False):
        """
        Recursively select children
        :param recursive: Enable selecting children recursively to select all children
        :param parent: Parent object whose children are selected
        :param select_parent: bool
        """
        if select_parent:
            parent.select_set(True)

        for child in parent.children:
            child.select_set(True)
            if recursive:
                SceneUtilities.selectChildren(child, True)

    @staticmethod
    def getChildren(parent, include_meshes=True, recursive=True):
        """
        Recursively select children
        :param parent: Parent object whose children are selected
        :param include_meshes:
        :param recursive: Enable selecting children recursively to select all children
        """
        children = []
        for child in parent.children:
            children.append(child)
            if include_meshes and child.data:
                children.append(child.data)
            if recursive:
                children.extend(SceneUtilities.getChildren(child, recursive=True))
        return children

    @staticmethod
    def getChildMeshes(parent, recursive=True, include_root=True):
        """
        Recursively select children
        :param parent: Parent object whose children are selected
        :param recursive: Enable selecting children recursively to select all children
        """
        children = []

        if include_root and parent.data:
            children.append(parent.data)

        for child in parent.children:
            if child.data:
                children.append(child.data)
            if recursive:
                children.extend(SceneUtilities.getChildMeshes(child, recursive=True, include_root=False))

        return children

    @staticmethod
    def duplicateObject(mesh, include_parent=False):
        """
        Select children and join meshes together. Then duplicate the object and returns it
        :param mesh: Mesh to duplicate
        :return:
        """
        if include_parent:
            mesh.select_set(True)

        SceneUtilities.selectChildren(mesh)
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.join()
        bpy.ops.object.duplicate()
        return bpy.context.selected_objects[0]

    @staticmethod
    def joinObjects(active_parent, secondary_parent, cleanup_empties=True):
        """
        Method to join all meshes in the two provided object hierarchies
        :param active_parent:
        :param secondary_parent:
        :return:
        """
        # Clear any existing selection
        bpy.ops.object.select_all(action='DESELECT')

        # Select all objects to merge
        SceneUtilities.selectChildren(active_parent, select_parent=True)
        SceneUtilities.selectChildren(secondary_parent, select_parent=True)

        # Set the merge context
        sceneMeshes = [m for m in bpy.context.scene.objects if m.type == 'MESH']
        print(f'Scene meshes: {[x.name for x in sceneMeshes]}')

        # Find a mesh object child of the active parent object
        for mesh in sceneMeshes:
            # Make the first mesh found under the active parent hierarchy the active object
            if mesh.name == active_parent.name:
                print(f'JOIN from mesh: mesh name - {mesh.name}')
                bpy.context.view_layer.objects.active = mesh
                break
            elif mesh.parent and active_parent.name == mesh.parent.name:
                print(f'JOIN: parent name - {mesh.parent.name} from mesh {mesh.name}')
                bpy.context.view_layer.objects.active = mesh
                break
        # Merge the meshes and clear selection
        bpy.ops.object.join()
        bpy.ops.object.select_all(action='DESELECT')
        
        # Cleanup empties
        if cleanup_empties:
            try:
                bpy.data.objects.remove(secondary_parent)
            except ReferenceError as e:
                # All empties were destroyed during merge, nothing left to cleanup
                pass
